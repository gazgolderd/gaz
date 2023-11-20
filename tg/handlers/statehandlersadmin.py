from aiogram import Router, Bot
from aiogram.types import Message, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from ..states import PromoCodeUser, PromoCodeAdmin, ChapterState, GramState, ProductState, SendState
from asgiref.sync import sync_to_async
from ..models import Promo, TelegramUser, Product, Chapter, Gram
from .. import text, kb

router = Router()


@router.message(PromoCodeAdmin.awaiting_sum)
async def create_promo(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            sum_of_promo = msg.text
            promo = await sync_to_async(Promo.objects.create)(amount=sum_of_promo)
            await msg.answer(f"Вы создали промокод: `{promo.promo_text}`\nСумма ${sum_of_promo}")
            await state.clear()
    except Exception as e:
        await msg.answer("Введите вверный формат, например число")


@router.message(ChapterState.awaiting_title)
async def add_title(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            title = str(msg.text)
            chapter = await sync_to_async(Chapter.objects.create)(title=title)
            await state.update_data(chapter_id=chapter.id)
            await msg.answer("Отправьте фото", parse_mode=None)
            await state.set_state(ChapterState.awaiting_photo)
    except Exception as e:
        await msg.answer(f"Ошибка {e}")


@router.message(ChapterState.awaiting_photo)
async def add_price(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            data = await state.get_data()
            chapter_id = data.get("chapter_id")
            if chapter_id:
                photo = msg.photo
                if photo:
                    photo = photo[0].file_id
                    await state.update_data(photo_id=photo)
                    await msg.answer("Напишите описание")
                    await state.set_state(ChapterState.awaiting_description)
    except Exception as e:
        await msg.answer(f"Ошибка {e}")


@router.message(ChapterState.awaiting_description)
async def add_description(msg: Message, state: FSMContext, bot: Bot):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            data = await state.get_data()
            chapter_id = data.get("chapter_id")
            photo_id = data.get("photo_id")
            if chapter_id and photo_id:
                chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
                description = msg.text
                chapter.description = description
                chapter.photo = photo_id
                chapter.save()
                await bot.send_photo(chat_id=user.user_id, photo=chapter.photo, caption=text.chapter.format(
                    title=chapter.title, description=chapter.description))
                await state.clear()
    except Exception as e:
        await msg.answer(f"Ошибка {e}")


@router.message(GramState.awaiting_chapter)
async def choose_chapter_for_gram(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            chapters = await sync_to_async(Chapter.objects.all)()
            chapter_title = msg.text
            for i in chapters:
                if i.title == chapter_title:
                    await state.update_data(chapter_id=i.id)
                    await state.set_state(GramState.awaiting_gram)
                    await msg.answer("Введите грамовку, например:\n\n `1` , `1.5`")
                    return
            await msg.answer("Не удается найти раздел")
    except Exception as e:
        print(e)


@router.message(GramState.awaiting_gram)
async def add_gram(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            g = msg.text
            await state.update_data(gram_amount=g)
            await msg.answer("Введите стоимость $")
            await state.set_state(GramState.awaiting_usd)
    except Exception as e:
        await msg.answer(f"Некорректное число, введите 1 или 1.5 \n{e}")


@router.message(GramState.awaiting_usd)
async def add_usd(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin:
            data = await state.get_data()
            chapter_id = data.get("chapter_id")
            gram_amount = data.get("gram_amount")
            chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
            if chapter:
                gram = await sync_to_async(Gram.objects.create)(gram=gram_amount, chapter=chapter, usd=msg.text)
                await msg.answer(f"{gram.id}. {gram.chapter.title} {gram.gram} GR ${gram.usd}\n\nСоздано")
                await state.clear()
    except Exception as e:
        print(e)


@router.message(ProductState.awaiting_chapter)
async def choose_chapter(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin or user.is_courier:
            chapter = await sync_to_async(Chapter.objects.get)(title=msg.text)
            if chapter:
                await state.update_data(chapter_id=chapter.id)
                builder = ReplyKeyboardBuilder()
                for i in await sync_to_async(Gram.objects.filter)(chapter=chapter):
                    builder.add(KeyboardButton(text=f"{i.gram} GR ${i.usd}"))
                builder.adjust(4)
                await msg.answer("Выберите грамовку", reply_markup=builder.as_markup(resize_keyboard=True))
                await state.set_state(ProductState.awaiting_gram)
    except Exception as e:
        print(e)


@router.message(ProductState.awaiting_gram)
async def choose_gram(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin or user.is_courier:
            g = msg.text.split()
            g = g[0]
            data = await state.get_data()
            chapter_id = data.get("chapter_id")
            chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
            grams = await sync_to_async(Gram.objects.filter)(gram=g, chapter=chapter)
            gram = grams.first()
            if gram:
                await state.update_data(gram_id=gram.id)
                await msg.answer("Пожалуйста выберите район", reply_markup=kb.builder.as_markup(
                    resize_keyboard=True, one_time_keyboard=True))
                await state.set_state(ProductState.awaiting_place)
    except Exception as e:
        print(e)


@router.message(ProductState.awaiting_place)
async def choose_place(msg: Message, state: FSMContext):
    try:
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin or user.is_courier:
            await state.update_data(place=msg.text)
            await msg.answer("Пожалуйста отправьте продукты!\n\nКаждая строка - это новый продукт")
            await state.set_state(ProductState.awaiting_products)
    except Exception as e:
        print(e)


@router.message(ProductState.awaiting_products)
async def add_products(msg: Message, state: FSMContext):
    try:
        product_texts = msg.text.split("\n")
        user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
        if user.is_admin or user.is_courier:
            data = await state.get_data()
            print(data)
            gram_id = data.get("gram_id")
            chapter_id = data.get("chapter_id")
            place = data.get("place")
            gram = await sync_to_async(Gram.objects.get)(id=gram_id)
            chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
            for i in product_texts:
                product = await sync_to_async(Product.objects.create)(courier=user, gram=gram, text=i)
                if place == "Октябрьский":
                    chapter.oktyabrsky.add(product)
                elif place == "Ленинский":
                    chapter.leninsky.add(product)
                elif place == "Первомайский":
                    chapter.pervomaysky.add(product)
                elif place == "Свердловский":
                    chapter.sverdlovsky.add(product)
            chapter.save()
            await state.clear()
            await msg.answer("Успешно")
    except Exception as e:
        print(e)


@router.message(SendState.awaiting_text)
async def handle_send_all(message: Message, state: FSMContext, bot: Bot):
    text_to_send = message.text
    users = await sync_to_async(TelegramUser.objects.all)()

    for user in users:
        try:
            chat_member = await bot.get_chat_member(user.user_id, user.user_id)
            if chat_member.status != "left" and chat_member.status != "kicked":
                # Пользователь не заблокировал бота, отправляем сообщение
                await bot.send_message(user.user_id, text_to_send)
                await message.answer(f"Сообщение отправлено пользователю: {user.username}")
            else:
                await message.answer(f"Сообщение НЕ отправлено: {user.username}")
                print(f"Пользователь {user.username} заблокировал бота")
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user.username}: {str(e)}")

    await message.answer(f"Вы отправили сообщение:\n\n{text_to_send}\n\nвсем пользователям в боте.")
    await state.clear()