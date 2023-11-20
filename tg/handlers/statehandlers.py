from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from ..states import PromoCodeUser, PromoCodeAdmin, TransferBalance
from asgiref.sync import sync_to_async
from ..models import Promo, TelegramUser

router = Router()


@router.message(PromoCodeUser.awaiting_promo)
async def add_promo_to_balance(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        promo_code = msg.text
        promo = await sync_to_async(Promo.objects.get)(promo_text=promo_code)
        if not promo.used:
            user.balance = promo.amount
            user.save()
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
    except Exception as e:
        await msg.answer("Отказано")
        print(e)

