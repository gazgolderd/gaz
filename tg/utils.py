from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import ClientConnectorError
from django.db.models import Q

from . import kb
from .models import Product, LostUserProduct
from asgiref.sync import sync_to_async
import aiohttp
import asyncio
from aiogram import exceptions as tg_exceptions


async def get_unique_products():
    all_products = await sync_to_async(Product.objects.filter)(sold=False)
    unique_titles = all_products.values_list('title', flat=True).distinct()
    unique_products = all_products.exclude(Q(title__in=unique_titles) & ~Q(id__in=unique_titles))
    return unique_products


async def create_invoice(product, crypto):
    account = "apr-5bd9fe28b751de5cf6975a08e4fb545c" # СЮДА АПИРОН АЙДИ
    create_invoice_url = f'https://apirone.com/api/v2/accounts/{account}/invoices'
    course = await get_crypto_with_retry(crypto)
    if course is not None:
        ltc_price = product.gram.usd / course

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
            await create_invoice(product, crypto)


# async def get_crypto(crypto):
#     url = f"https://apirone.com/api/v2/ticker?currency={crypto}"
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url) as response:
#                 json_data = await response.json()
#
#         return json_data['usd']
#     except ClientConnectorError as e:
#         await get_crypto(crypto)
#         print("GET CRYPTO ПРОПАДАЕТ")

async def get_crypto_with_retry(crypto, max_retries=10):
    url = f"https://apirone.com/api/v2/ticker?currency={crypto}"

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    json_data = await response.json()

            return json_data.get('usd')
        except aiohttp.ClientConnectorError as e:
            print(f"Ошибка при получении курса криптовалюты. Попытка {attempt + 1}/{max_retries}")
            await asyncio.sleep(1)  # Пауза перед следующей попыткой

    print("Не удалось получить курс криптовалюты после нескольких попыток.")
    return None


async def check_invoice_paid(id: str, message, product, chapter, user):
    while True:
        url = f"https://apirone.com/api/v2/invoices/{id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    invoice_data = await response.json()


            if invoice_data['status'] in ('completed', 'paid', 'overpaid'):
                location = find_product_location(product, chapter)
                if location is not None:
                    location.remove(product)
                    builder = InlineKeyboardBuilder()
                    builder.add(InlineKeyboardButton(text="Оставить отзыв", callback_data=f"add_review_{product.id}"))
                    # builder.add(InlineKeyboardButton(text="Открыть спор", callback_data=f"cant_find_{product.id}"))
                    builder.adjust(1)
                    await message.answer(product.text, reply_markup=builder.as_markup(), parse_mode=None)
                    product.sold = True
                    product.user = user
                    product.save()
                    if user.referred_by:
                        ref_user = user.referred_by
                        ref_user.balance += 1
                        ref_user.save(update_fields=['balance'])
                    return
                else:
                    await message.answer(f"Продукт уже забрали, но вы можете купить другой.\nВаш баланс пополнен на ${product.gram.usd}")
                    user.balance += product.gram.usd
                    user.save()
                    await sync_to_async(LostUserProduct.objects.create)(user=user, lost_product=product,
                                                                       added_to_balance=product.gram.usd)
                    return
            if invoice_data['status'] == 'expired':
                await message.answer("Вы просрочили время")
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


def find_product_location(product, chapter):
    if product in chapter.pervomaysky.all():
        return chapter.pervomaysky
    elif product in chapter.oktyabrsky.all():
        return chapter.oktyabrsky
    elif product in chapter.leninsky.all():
        return chapter.leninsky
    elif product in chapter.sverdlovsky.all():
        return chapter.sverdlovsky
    else:
        return None


