from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

not_subscribed = [
    [InlineKeyboardButton(text="Подписаться", url="https://t.me/bestchangekgz"),
     InlineKeyboardButton(text="Проверить", callback_data="check_subs")]
]
not_subscribed = InlineKeyboardMarkup(inline_keyboard=not_subscribed)

menu = [
    [InlineKeyboardButton(text="🎁 Наличие товаров", callback_data="chapters")],
    [InlineKeyboardButton(text="👤 Профиль", callback_data="cabinet"),
     InlineKeyboardButton(text="Отзывы", callback_data="reviews")],
    [InlineKeyboardButton(text="⚠️ Правила", callback_data="rule"),
     InlineKeyboardButton(text="⚡️Наши ресурсы", callback_data="resources")],
    # [InlineKeyboardButton(text="☎️ Поддержка", url="https://t.me/ololowka_raven")],
]

menu = InlineKeyboardMarkup(inline_keyboard=menu)


cancel = InlineKeyboardButton(text="Назад", callback_data="cancel")
cancel = InlineKeyboardMarkup(inline_keyboard=[[cancel]])

cabinet = [[InlineKeyboardButton(text="💰 Пополнить", callback_data="add_balance"),
            InlineKeyboardButton(text="↔️ Отправить", callback_data="transfer_balance")],
           [InlineKeyboardButton(text="📈 Рефералка", callback_data="referrals"),
            InlineKeyboardButton(text="💟 Промокод", callback_data="promo-code-user")],
           [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]]
cabinet = InlineKeyboardMarkup(inline_keyboard=cabinet)


admin_panel = [[InlineKeyboardButton(text="Промокод", callback_data="promo-code-admin")],
               [InlineKeyboardButton(text="Товары", callback_data="handle_product")],
               [InlineKeyboardButton(text="Товар пополнен", callback_data="product_fulled")],
               [InlineKeyboardButton(text="Добавить/Списать баланс", callback_data="manage_balance")],
               [InlineKeyboardButton(text="Рассылка", callback_data="announce_to_chats")],
               [InlineKeyboardButton(text="Розыгрыш", callback_data="lottery")],
               [InlineKeyboardButton(text="Статистика", callback_data="statistics")]]
admin_panel = InlineKeyboardMarkup(inline_keyboard=admin_panel)

add_product = [[InlineKeyboardButton(text="Добавить раздел", callback_data="add_chapter"),
                InlineKeyboardButton(text="Добавить грам", callback_data="add_gram")],
               [InlineKeyboardButton(text="Добавить продукты", callback_data="add_products")],
               [InlineKeyboardButton(text="Отмена", callback_data="cansel_admin")]]
add_product = InlineKeyboardMarkup(inline_keyboard=add_product)


builder = ReplyKeyboardBuilder()
builder.add(KeyboardButton(text="Октябрьский"))
builder.add(KeyboardButton(text="Ленинский"))
builder.add(KeyboardButton(text="Первомайский"))
builder.add(KeyboardButton(text="Свердловский"))


after_payed = [[InlineKeyboardButton(text="Оставить отзыв", callback_data="add_review")],
               [InlineKeyboardButton(text="Открыть спор", callback_data="cant_find")]]
after_payed = InlineKeyboardMarkup(inline_keyboard=after_payed)