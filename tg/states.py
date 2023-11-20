from aiogram.fsm.state import StatesGroup, State


class PromoCodeUser(StatesGroup):
    awaiting_promo = State()


class PromoCodeAdmin(StatesGroup):
    awaiting_sum = State()


class ChapterState(StatesGroup):
    awaiting_title = State()
    awaiting_photo = State()
    awaiting_description = State()


class ProductState(StatesGroup):
    awaiting_chapter = State()
    awaiting_gram = State()
    awaiting_place = State()
    awaiting_products = State()


class GramState(StatesGroup):
    awaiting_chapter = State()
    awaiting_gram = State()
    awaiting_usd = State()


class SendState(StatesGroup):
    awaiting_text = State()


class TransferBalance(StatesGroup):
    awaiting_data = State()