import asyncio

from aiogram import Router, Bot
from aiogram.client.session import aiohttp
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiohttp import ClientConnectorError

from ..states import PromoCodeUser, PromoCodeAdmin, TransferBalance, ReviewState, AddToBalance
from asgiref.sync import sync_to_async
from ..models import Promo, TelegramUser, Review
from ..utils import create_invoice, get_crypto_with_retry
from aiogram import exceptions as tg_exceptions
router = Router()


@router.message(PromoCodeUser.awaiting_promo)
async def add_promo_to_balance(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        promo_code = msg.text
        promo = await sync_to_async(Promo.objects.get)(promo_text=promo_code)
        if not promo.used:
            user.balance += promo.amount
            user.save()
            promo.used = True
            promo.save()
            await msg.answer(f"${promo.amount} добавлен в ваш баланс")
            await state.clear()
    except Exception as e:
        await msg.answer("Неверный промокод")


@router.message(TransferBalance.awaiting_data)
async def transfer_balance(msg: Message, state: FSMContext, bot: Bot):
    try:
        current_user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        data = msg.text.split()
        username = data[0]
        if data[0].startswith("@"):
            username = data[0][1:]
        target_user = await sync_to_async(TelegramUser.objects.get)(username=username)
        transfer_amount = int(data[1])
        if current_user.balance >= transfer_amount and target_user:
            target_user.balance += transfer_amount
            await bot.send_message(target_user.user_id, f"Вам начислено ${transfer_amount}")
            current_user.balance -= transfer_amount
            target_user.save()
            current_user.save()
            await msg.answer(f"Вы успешно перевели {transfer_amount} пользователю @{target_user.username}",
                             parse_mode=None)
            await state.clear()
        else:
            await msg.answer(f"Отказано")
    except Exception as e:
        await msg.answer("Отказано")
        print(e)


@router.message(ReviewState.awaiting_review)
async def add_review(msg: Message, state: FSMContext, bot: Bot):
    await msg.delete()
    data = await state.get_data()
    rate = data.get("rate")
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    await sync_to_async(Review.objects.create)(user=user, rating=rate, text=msg.text)
    await msg.answer("Спасибо за ваш отзыв")


@router.message(AddToBalance.awaiting_sum)
async def awaiting_sum(msg: Message, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if msg.text.isdigit():
        a = await create_balance_invoice(float(msg.text), "ltc")
        invoice = a['invoice']
        amount_in_satoshi = a['amount']
        address = a['address']
        amount_in_ltc = amount_in_satoshi / 10 ** 8
        asyncio.create_task(check_invoice_balance_paid(invoice, Message, user, msg.text, state))
        await state.set_state(AddToBalance.awaiting_pay)
        text = "*Пополнение баланса:*\n"
        text += "➖➖➖➖➖➖➖➖➖➖➖➖\n"
        text += f"_Способ оплаты_ *LTC*\n\n"
        text += f"*Сумма к оплате:* `{amount_in_ltc}`  \n"
        text += f"`{address}`\n\n"
        text += "✅_Нажми на адрес или сумму, чтобы скопировать!_\n"
        text += "⏰ _Время на оплату:_ *30 минут*"
        await msg.answer(text)
    elif msg.text == "Отмена":
        await msg.answer("Оплата отменена!", reply_markup=ReplyKeyboardRemove())
    else:
        await msg.answer("Введите число: ")


@router.message(AddToBalance.awaiting_pay)
async def awaiting_pay_balance(msg: Message, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if msg.text == "Отмена":
        await msg.answer("Оплата отменена", reply_markup=ReplyKeyboardRemove())
    else:
        await msg.answer("Пожалуйста отправьте указанную сумму!")


async def create_balance_invoice(amount, crypto):
    account = "apr-5bd9fe28b751de5cf6975a08e4fb545c" # СЮДА АПИРОН АЙДИ
    create_invoice_url = f'https://apirone.com/api/v2/accounts/{account}/invoices'
    course = await get_crypto_with_retry(crypto)
    try:
        amount = float(amount)
    except ValueError:
        # Обработка ошибки, если amount_str не является допустимым числом
        raise ValueError("Введено некорректное значение для суммы.")
    if course is not None:
        ltc_price = amount / course

        decimal_places = 8

        amount_in_satoshi = int(ltc_price * 10 ** decimal_places)
        invoice_data = {
            "amount": amount_in_satoshi,
            "currency": "ltc",
            "lifetime": 2000,
            "callback_url": "http://example.com",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(create_invoice_url, json=invoice_data, headers={'Content-Type': 'application/json'}
                                        ) as response:
                    invoice_info = await response.json()

            return invoice_info
        except ClientConnectorError as e:
            await create_balance_invoice(amount, crypto)


async def check_invoice_balance_paid(id: str, message, user, amount, state):
    while True:
        url = f"https://apirone.com/api/v2/invoices/{id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    invoice_data = await response.json()

            if invoice_data['status'] in ('completed', 'paid', 'overpaid'):
                new_user = await sync_to_async(TelegramUser.objects.get)(user_id=user.user_id)
                new_user.balance += amount
                new_user.save()
                await state.clear()
                await message.answer(f"Ваш баланс пополнен на {amount}$", reply_markup=ReplyKeyboardRemove())
                return
            if invoice_data['status'] == 'expired':
                await message.answer("Вы просрочили время", reply_markup=ReplyKeyboardRemove())
                await state.clear()
                return

            await asyncio.sleep(10)
        except ClientConnectorError as e:
            print(f"Connection error: {e}")
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except tg_exceptions.TelegramNetworkError as e:
            print(f"Telegram Network error: {e}")
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)