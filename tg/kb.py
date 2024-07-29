from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

not_subscribed = [
    [InlineKeyboardButton(text="Подписаться", url="https://t.me/GAZGOLDER_TEST"),
     InlineKeyboardButton(text="Проверить", callback_data="check_subs")]
]
not_subscribed = InlineKeyboardMarkup(inline_keyboard=not_subscribed)

menu = [
    [InlineKeyboardButton(text="🎁 Наличие товаров", callback_data="chapters")],
    [InlineKeyboardButton(text="👤 Профиль", callback_data="cabinet"),
     InlineKeyboardButton(text="Отзывы", url="https://t.me/+p0Bhm_J3JgtmZjli")],
     # InlineKeyboardButton(text="Отзывы", url="https://t.me/+R7OAXJEGr1hjYzgy")],
    [InlineKeyboardButton(text="⚠️ Правила", callback_data="rule")],
    # [InlineKeyboardButton(text="⚠️ Правила", callback_data="rule"),
    # [InlineKeyboardButton(text="⚡️Наши ресурсы", callback_data="resources")],
    [InlineKeyboardButton(text="☎️ Поддержка", url="https://t.me/Gazgolder_support1")],
]

menu = InlineKeyboardMarkup(inline_keyboard=menu)


cancel = InlineKeyboardButton(text="Назад", callback_data="cancel")
cancel = InlineKeyboardMarkup(inline_keyboard=[[cancel]])

# cabinet = [[InlineKeyboardButton(text="💰 Пополнить", callback_data="add_balance"),
# cabinet = [[InlineKeyboardButton(text="↔️ Отправить", callback_data="transfer_balance")],
#            # [InlineKeyboardButton(text="📈 Рефералка", callback_data="referrals")],
#             [InlineKeyboardButton(text="💟 Промокод", callback_data="promo-code-user")],
#            [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]]
cabinet = [[InlineKeyboardButton(text="💟 Промокод", callback_data="promo-code-user")],
           [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="money_add_balance")],
           [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]]
cabinet = InlineKeyboardMarkup(inline_keyboard=cabinet)

tovars = [InlineKeyboardButton(text="Товары", callback_data="handle_product")]
tovars = InlineKeyboardMarkup(inline_keyboard=[tovars])
admin_panel = [[InlineKeyboardButton(text="Промокод", callback_data="promo-code-admin")],
               [InlineKeyboardButton(text="Товары", callback_data="handle_product")],
               [InlineKeyboardButton(text="Витрина", callback_data="all_products")],
               # [InlineKeyboardButton(text="Добавить/Списать баланс", callback_data="manage_balance")],
               # [InlineKeyboardButton(text="Рассылка", callback_data="announce_to_chats")],
               # [InlineKeyboardButton(text="Розыгрыш", callback_data="lottery")],
               [InlineKeyboardButton(text="Статистика", callback_data="statistics")]]
admin_panel = InlineKeyboardMarkup(inline_keyboard=admin_panel)

add_product = [[InlineKeyboardButton(text="Добавить раздел", callback_data="add_chapter"),
                InlineKeyboardButton(text="Добавить грам", callback_data="add_gram")],
               [InlineKeyboardButton(text="Добавить продукты", callback_data="add_products")],
               [InlineKeyboardButton(text="Отмена", callback_data="cansel_admin")]]
add_product = InlineKeyboardMarkup(inline_keyboard=add_product)

add_product_cour = [[InlineKeyboardButton(text="Добавить продукты", callback_data="add_products")]]
add_product_cour = InlineKeyboardMarkup(inline_keyboard=add_product_cour)


builder = ReplyKeyboardBuilder()
builder.add(KeyboardButton(text="Октябрьский"))
builder.add(KeyboardButton(text="Ленинский"))
builder.add(KeyboardButton(text="Первомайский"))
builder.add(KeyboardButton(text="Свердловский"))


after_payed = [[InlineKeyboardButton(text="Оставить отзыв", callback_data="add_review")],
               [InlineKeyboardButton(text="Открыть спор", callback_data="cant_find")]]
after_payed = InlineKeyboardMarkup(inline_keyboard=after_payed)
