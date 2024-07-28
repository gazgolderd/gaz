import requests
from aiogram import Router, Bot
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from asgiref.sync import sync_to_async
import asyncio

from ..models import Rule, Review, TelegramUser, Product, Chapter, Gram
from .reviews import get_reviews
from .. import kb, text, states
from ..states import ProductState, ChapterState, GramState, TransferBalance, ReviewState, AddToBalance
from ..utils import get_unique_products, create_invoice, check_invoice_paid, find_product_location

router = Router()


@router.callback_query()
async def handle_callback_query(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    if callback_query.data == "check_subs":
        is_subscribed = await bot.get_chat_member(chat_id="@stoner_channel_tests", user_id=callback_query.from_user.id)
        if is_subscribed.status in ['member', 'administrator', 'creator']:
            await callback_query.message.edit_text("Вы подписаны, можете пользоваться", reply_markup=kb.menu)

    if callback_query.data == "cancel":
        await callback_query.message.edit_text("Приветствие ☀️", reply_markup=kb.menu)

    if callback_query.data == "rule":
        rule = await sync_to_async(Rule.objects.first)()
        await callback_query.message.edit_text(str(rule.bot_rule), reply_markup=kb.cancel, parse_mode=None)

    if callback_query.data == "reviews":
        page = 1
        page_size = 3
        reviews = await sync_to_async(Review.objects.order_by('-id').all)()

        total_pages = (len(reviews) + page_size - 1) // page_size

        if page < total_pages:
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            reviews = reviews[start_index:end_index]
            builder = InlineKeyboardBuilder()
            response_text = ""
            for i, review in enumerate(reviews, start=start_index + 1):
                response_text += f"\nОтзыв номер {i}\nОценка: {review.rating}\n{review.text}\n"

            if page > 1:
                builder.add(InlineKeyboardButton(text="Предыдущая", callback_data=f"prev_page_{page}"))
            if page < total_pages:
                builder.add(InlineKeyboardButton(text="Следующая", callback_data=f"next_page_{page}"))
            builder.add(InlineKeyboardButton(text="В меню", callback_data="cancel"))
            await callback_query.message.edit_text(text=response_text, reply_markup=builder.as_markup())

    if callback_query.data.startswith("next_page_"):
        page = int(callback_query.data.split("_")[2])
        await get_reviews(page + 1, callback_query.message)
    if callback_query.data.startswith("prev_page_"):
        page = int(callback_query.data.split("_")[2])
        await get_reviews(page - 1, callback_query.message)

    if callback_query.data == "cabinet":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        bought_products = await sync_to_async(Product.objects.filter)(user=user)
        response_text = "👤 Ваш профиль: \n➖➖➖➖➖➖➖➖➖➖\n"
        response_text += f"💰 Баланс: `{user.balance}`\n🎁 Куплено `{bought_products.count()}`\n\n"
        response_text += f"_Реферальная ссылка:_\n"
        response_text += f"`https://t.me/GazgoIder_bot?start={user.id}`\n"
        response_text += f"_За каждую покупку реферала - 1$_"
        await callback_query.message.edit_text(response_text, reply_markup=kb.cabinet)
    if callback_query.data == "balance":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await callback_query.message.answer(f"Ваш баланс составляет ${user.balance}")
    if callback_query.data == "transfer_balance":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await state.set_state(TransferBalance.awaiting_data)
        await callback_query.message.answer("Пожалуйста введите имя пользователя и сумму, которую хотите отправить")

    if callback_query.data == "referrals":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        await callback_query.message.answer(text.referrals.format(user=user.username, userid=user.id), parse_mode=None)

    if callback_query.data == "promo-code-user":
        await callback_query.message.answer("Введите промокод")
        await state.set_state(states.PromoCodeUser.awaiting_promo)

    if callback_query.data == "promo-code-admin":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            await callback_query.message.answer("Пишите сумму $ для промо кода")
            await state.set_state(states.PromoCodeAdmin.awaiting_sum)

    if callback_query.data == "chapters":
        chapters = await sync_to_async(Chapter.objects.all)()
        if chapters:
            builder = InlineKeyboardBuilder()
            response_text = ""
            for i in chapters:
                if i.oktyabrsky.exists() or i.leninsky.exists() or i.sverdlovsky.exists() or i.pervomaysky.exists():
                    builder.add(InlineKeyboardButton(text=f"{i.title}", callback_data=f"choose_chapter_{i.id}"))
                    response_text += f"════*{i.title}*════\n"

                if i.oktyabrsky.exists():
                    products = i.oktyabrsky.all()
                    unique_grams = products.values('gram__gram').distinct()
                    response_text += "✅ *ОКТЯБРЬСКИЙ*\n"
                    for gram in unique_grams:
                        gram_value = gram['gram__gram']
                        product_object = products.filter(gram__gram=gram_value).first()
                        response_text += f"---Вес {gram_value} *GR* = *${product_object.gram.usd}*\n"
                if i.leninsky.exists():
                    products = i.leninsky.all()
                    unique_grams = products.values('gram__gram').distinct()
                    response_text += "✅ *ЛЕНИНСКИЙ*\n"
                    for gram in unique_grams:
                        gram_value = gram['gram__gram']
                        product_object = products.filter(gram__gram=gram_value).first()
                        response_text += f"---Вес {gram_value} *GR* = *${product_object.gram.usd}*\n"
                if i.sverdlovsky.exists():
                    products = i.sverdlovsky.all()
                    unique_grams = products.values('gram__gram').distinct()
                    response_text += "✅ *СВЕРДЛОВСКИЙ*\n"
                    for gram in unique_grams:
                        gram_value = gram['gram__gram']
                        product_object = products.filter(gram__gram=gram_value).first()
                        response_text += f"---Вес {gram_value} *GR* = *${product_object.gram.usd}*\n"
                if i.pervomaysky.exists():
                    products = i.pervomaysky.all()
                    unique_grams = products.values('gram__gram').distinct()
                    response_text += "✅ *ПЕРВОМАЙСКИЙ*\n"
                    for gram in unique_grams:
                        gram_value = gram['gram__gram']
                        product_object = products.filter(gram__gram=gram_value).first()
                        response_text += f"---Вес {gram_value} *GR* = *${product_object.gram.usd}*\n"

            if not response_text:
                await callback_query.message.answer("Товар закончился, приходите позже")
                return
            response_text += "\n⬇️ Выберите товар ⬇️"
            builder.adjust(1)
            await callback_query.message.answer(text=response_text, reply_markup=builder.as_markup())

    if callback_query.data.startswith("choose_chapter_"):
        chapter_id = callback_query.data[15:]
        chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
        builder = InlineKeyboardBuilder()

        if chapter.oktyabrsky.exists():
            builder.add(InlineKeyboardButton(text="Октябрьский", callback_data=f"pre_confirm_{chapter.id}_okt"))
        if chapter.leninsky.exists():
            builder.add(InlineKeyboardButton(text="Ленинский", callback_data=f"pre_confirm_{chapter.id}_len"))
        if chapter.sverdlovsky.exists():
            builder.add(InlineKeyboardButton(text="Свердловский", callback_data=f"pre_confirm_{chapter.id}_sve"))
        if chapter.pervomaysky.exists():
            builder.add(InlineKeyboardButton(text="Первомайский", callback_data=f"pre_confirm_{chapter.id}_per"))
        builder.adjust(1)
        try:
            await bot.send_photo(chat_id=callback_query.from_user.id, caption=f"Вы выбрали {chapter.title}",
                                 photo=chapter.photo, reply_markup=builder.as_markup())
        except Exception as e:
            await bot.send_message(chat_id=callback_query.from_user.id, text=f"Вы выбрали {chapter.title}", reply_markup=builder.as_markup())

    if callback_query.data.startswith("pre_confirm_"):
        data = callback_query.data.split("_")
        chapter_id = data[2]
        place = data[3]
        chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
        builder = InlineKeyboardBuilder()
        if place == "okt":
            products = chapter.oktyabrsky.all()
            unique_grams = products.values('gram__gram').distinct()
            for gram in unique_grams:
                gram_value = gram['gram__gram']
                product_object = products.filter(gram__gram=gram_value).first()
                builder.add(InlineKeyboardButton(text=f"💵{gram_value} GR = ${product_object.gram.usd}\n",
                                                 callback_data=f"confirm_{product_object.id}"))
        if place == "len":
            products = chapter.leninsky.all()
            unique_grams = products.values('gram__gram').distinct()
            for gram in unique_grams:
                gram_value = gram['gram__gram']
                product_object = products.filter(gram__gram=gram_value).first()
                builder.add(InlineKeyboardButton(text=f"💵{gram_value} GR = ${product_object.gram.usd}\n",
                                                 callback_data=f"confirm_{product_object.id}"))
        if place == "per":
            products = chapter.pervomaysky.all()
            unique_grams = products.values('gram__gram').distinct()
            for gram in unique_grams:
                gram_value = gram['gram__gram']
                product_object = products.filter(gram__gram=gram_value).first()
                builder.add(InlineKeyboardButton(text=f"💵{gram_value} GR = ${product_object.gram.usd}\n",
                                                 callback_data=f"confirm_{product_object.id}"))
        if place == "sve":
            products = chapter.sverdlovsky.all()
            unique_grams = products.values('gram__gram').distinct()
            for gram in unique_grams:
                gram_value = gram['gram__gram']
                product_object = products.filter(gram__gram=gram_value).first()
                builder.add(InlineKeyboardButton(text=f"💵{gram_value} GR = ${product_object.gram.usd}\n",
                                                 callback_data=f"confirm_{product_object.id}"))
        builder.adjust(1)

        await callback_query.message.delete()
        try:
            await bot.send_photo(chat_id=callback_query.from_user.id, caption=f"Выберите грамовку!",
                                 photo=chapter.photo, reply_markup=builder.as_markup())
        except Exception:
            await bot.send_message(chat_id=callback_query.from_user.id, text=f"Выберите грамовку!",
                                   reply_markup=builder.as_markup())

    if callback_query.data.startswith("confirm_"):
        product_id = callback_query.data[8:]
        product = await sync_to_async(Product.objects.get)(id=product_id)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        response_text = (f"☑️ *Подтверждение*:\n ➖➖➖➖➖➖➖➖➖➖\n*📦 Ваш товар*: *{product.gram.chapter.title}*\n"
                         f"⚖️ *Вес*: `{product.gram.gram}`\n💲 *Стоимость*: `{product.gram.usd}`\n\n_Подтвердите покупку или_"
                         f" _используйте баланс для оплаты_\n")
        builder = InlineKeyboardBuilder()
        # if 0 < user.balance < product.gram.usd:
        #     builder.add(InlineKeyboardButton(text="⚡️ Включить баланс для оплаты", callback_data="add_balance_to_pay"))
        if user.balance >= product.gram.usd:
            builder.add(InlineKeyboardButton(text="⚡️ Купить с помощью баланса", callback_data=f"buy_product_with_balance_{product_id}"))
        builder.add(InlineKeyboardButton(text="✅ Подтверждаю", callback_data=f"order_progress_{product.id}"))
        builder.add(InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel"))
        builder.adjust(1)
        await callback_query.message.delete()
        await callback_query.message.answer(response_text, reply_markup=builder.as_markup())

    if callback_query.data.startswith("order_progress_"):
        data = callback_query.data.split("_")
        product_id = data[2]
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        product = await sync_to_async(Product.objects.get)(id=product_id)
        location = find_product_location(product, product.gram.chapter)
        if location is not None:
            if not product.sold:
                a = await create_invoice(product, "ltc")

                invoice = a['invoice']
                amount_in_satoshi = a['amount']
                address = a['address']
                amount_in_ltc = amount_in_satoshi / 10 ** 8
                asyncio.create_task(check_invoice_paid(invoice, callback_query.message, product, product.gram.chapter, user))

                await callback_query.message.edit_text(text.order_data.format(productid=product.id, ves=product.gram.gram,
                                                       price=product.gram.usd, crypto="LTC", cryptosum=amount_in_ltc,
                                                                              cryptoaddress=address))
            else:
                await callback_query.message.answer("Товар уже купили")
        else:
            await callback_query.message.answer("Товар уже купили")

    if callback_query.data == "handle_product":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            await callback_query.message.edit_text("Выберите действие", reply_markup=kb.add_product)

    if callback_query.data == "add_chapter":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            await callback_query.message.answer("Пожалуйста напишите название")
            await state.set_state(ChapterState.awaiting_title)
    if callback_query.data == "add_gram":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            chapters = await sync_to_async(Chapter.objects.all)()
            builder = ReplyKeyboardBuilder()
            for i in chapters:
                builder.add(KeyboardButton(text=i.title))
            if chapters:
                await callback_query.message.answer("Выберите раздел", reply_markup=builder.as_markup(
                    resize_keyboard=True))
                await state.set_state(GramState.awaiting_chapter)
            elif not chapters:
                await callback_query.message.answer("Сначала создайте раздел")
    if callback_query.data == "add_products":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin or user.is_courier:
            builder = ReplyKeyboardBuilder()
            for i in await sync_to_async(Chapter.objects.all)():
                builder.add(KeyboardButton(text=i.title))
            await state.set_state(ProductState.awaiting_chapter)
            await callback_query.message.answer("Выберите раздел", reply_markup=builder.as_markup(resize_keyboard=True))

    if callback_query.data == "manage_balance":
        pass

    if callback_query.data == "product_fulled":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            pass
    if callback_query.data == "statistics":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            await callback_query.message.answer("Для вывода статистики за определенный период\nВведите команду /showstats *кол-во* дней\n\n")
    if callback_query.data == "cansel_admin":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            chapters = await sync_to_async(Chapter.objects.all)()
            response_text = "➖➖➖*КОММАНДЫ АДМИНИСТРАТОРА*➖➖➖\n\n"
            for i in chapters:
                response_text += f"⚫️ *({i.id}) | {i.title}* \n"
                grams = await sync_to_async(Gram.objects.filter)(chapter=i)
                for i in grams:
                    response_text += f"〰️〰️*ID*: ({i.id}) | вес {i.gram} GR = ${i.usd}\n"
            response_text += "\n⚠️ Что бы удалить раздел, введите команду /delchapter *ID* раздела\n"
            response_text += "⚠️ Что бы удалить грам, введите команду /delgram *ID* раздела\n\n"
            response_text += "👁‍🗨 Разослать сообщение всем пользователям бота /send\n"
            response_text += "👁‍🗨 Для просмотра статистика за период /showstats *дней*\n"
            await callback_query.message.edit_text(response_text, reply_markup=kb.admin_panel)
    if callback_query.data.startswith("add_review_"):
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="⭐️⭐️⭐️⭐️⭐️", callback_data="add_rating_5"))
        builder.add(InlineKeyboardButton(text="⭐️⭐️⭐️⭐️️", callback_data="add_rating_4"))
        builder.add(InlineKeyboardButton(text="⭐️⭐️⭐️", callback_data="add_rating_3"))
        builder.add(InlineKeyboardButton(text="⭐️⭐️", callback_data="add_rating_2"))
        builder.add(InlineKeyboardButton(text="⭐️", callback_data="add_rating_1"))
        builder.adjust(1, 1, 3)
        await callback_query.message.delete()
        await callback_query.message.answer("Пожалуйста поставьте оценку", reply_markup=builder.as_markup())
    if callback_query.data.startswith("add_rating_"):
        data = callback_query.data.split("_")
        rate = data[2]
        data = callback_query.data.split("_")
        await state.set_state(ReviewState.awaiting_review)
        await state.update_data(rate=rate)
        await callback_query.message.answer("Пожалуйста введите свой отзыв")
    if callback_query.data.startswith("buy_product_with_balance_"):
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        data = callback_query.data.split("_")
        product_id = data[4]
        product = await sync_to_async(Product.objects.get)(id=product_id)
        location = find_product_location(product, product.gram.chapter)
        if location is not None:
            location.remove(product)
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Оставить отзыв", callback_data=f"add_review_{product.id}"))
            # builder.add(InlineKeyboardButton(text="Открыть спор", callback_data=f"cant_find_{product.id}"))
            builder.adjust(1)
            await callback_query.message.answer(product.text, reply_markup=builder.as_markup(), parse_mode=None)
            product.sold = True
            product.user = user
            product.save()
            user.balance -= product.gram.usd
            user.save()
            if user.referred_by:
                ref_user = user.referred_by
                ref_user.balance += 1
                ref_user.save(update_fields=['balance'])
    if callback_query.data == "money_add_balance":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="Отмена"))
        await callback_query.message.answer("Введите желаемую сумму: ")
        await state.set_state(AddToBalance.awaiting_sum)
    if callback_query.data == "all_products":
        user = await sync_to_async(TelegramUser.objects.get)(user_id=callback_query.from_user.id)
        if user.is_admin:
            chapters = await sync_to_async(Chapter.objects.all)()
            products_text = "➖➖➖*ВИТРИНА*➖➖➖\n"
            for i in chapters:
                products_text += f"➖➖*{i.title}*➖➖\n"
                products_okt = i.oktyabrsky.all()
                if products_okt:
                    products_text += f"➖*ОКТЯБРЬСКИЙ*\n"
                    for i in products_okt:
                        products_text += f"({i.id}) `{i.text}`\n"
                product_len = i.leninsky.all()
                if product_len:
                    products_text += f"➖*ЛЕНИНСКИЙ*\n"
                    for i in product_len:
                        products_text += f"({i.id}) `{i.text}`\n"
                product_sverd = i.sverdlovsky.all()
                if product_sverd:
                    products_text += f"➖*СВЕРДЛОВСКИЙ*\n"
                    for i in product_sverd:
                        products_text += f"({i.id}) `{i.text}`\n"
                product_perv = i.pervomaysky.all()
                if product_perv:
                    products_text += f"➖*ПЕРВОМАЙСКИЙ*\n"
                    for i in product_perv:
                        products_text += f"({i.id}) `{i.text}`\n"
                products_text += "\n\n_Для удаления продукта напишите_ /delproduct ID"
            await callback_query.message.answer(products_text)





