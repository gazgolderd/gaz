from aiogram import Router
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from ..models import Review
router = Router()


async def get_reviews(page, msg):
    page_size = 3
    reviews = await sync_to_async(Review.objects.order_by('-id').all)()
    total_pages = (len(reviews) + page_size - 1) // page_size

    if page <= total_pages:
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        reviews = reviews[start_index:end_index]
        builder = InlineKeyboardBuilder()
        response_text = ""
        for i, review in enumerate(reviews, start=start_index + 1):
            response_text += f"Отзыв номер {i}\nОценка: {review.rating}\n{review.text}\n"
        if page > 1:
            builder.add(InlineKeyboardButton(text="Предыдущая", callback_data=f"prev_page_{page}"))
        if page < total_pages:
            builder.add(InlineKeyboardButton(text="Следующая", callback_data=f"next_page_{page}"))
        builder.add(InlineKeyboardButton(text="В меню", callback_data="cancel"))
        await msg.edit_text(text=response_text, reply_markup=builder.as_markup(), parse_mode=None)
