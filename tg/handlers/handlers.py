from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from ..models import TelegramUser, Chapter, Gram, Product
from .. import kb, text
from ..states import SendState
from django.utils import timezone
from datetime import datetime, timedelta
router = Router()


@router.message(Command("start"))
async def start_command(msg: Message, state: FSMContext, bot: Bot, command: CommandObject):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=msg.from_user.id)
    referred_by_id = command.args
    if user.referred_by is None and referred_by_id:
        user.referred_by = await sync_to_async(TelegramUser.objects.get)(id=referred_by_id)
        await bot.send_message(user.referred_by.user_id, text=text.referred_announce.format(user=user.username))

    user.first_name = msg.from_user.first_name
    user.last_name = msg.from_user.last_name
    user.username = msg.from_user.username
    user.save()
    print("USER IN START", user.user_id, user.username)
    await msg.answer("Приветствие ☀️", reply_markup=kb.menu)
    # is_subscribed = await bot.get_chat_member(chat_id="@GAZGOLDER_TEST", user_id=msg.from_user.id)
    # if is_subscribed.status in ['member', 'administrator', 'creator']:
    #     await msg.answer("Приветствие", reply_markup=kb.menu)
    # else:
    #     await msg.answer("Подпишитесь на канал", reply_markup=kb.not_subscribed)


@router.message(Command("admin007"))
async def admin_panel(msg: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    chapters = await sync_to_async(Chapter.objects.all)()
    response_text = "➖➖*ПАНЕЛЬ АДМИНИСТРАТОРА*➖➖\n\n"
    for i in chapters:
        perv = i.pervomaysky.count()
        okt = i.oktyabrsky.count()
        leni = i.leninsky.count()
        sverd = i.sverdlovsky.count()
        total = perv + okt + leni + sverd
        response_text += f"⚫️ *({i.id}) | {i.title}*\n({total} в продаже)\n"
        grams = await sync_to_async(Gram.objects.filter)(chapter=i)
        for i in grams:
            response_text += f"〰️〰️*ID*: ({i.id}) | вес {i.gram} GR = ${i.usd}\n"
    response_text += "\n⚠️ Что бы удалить раздел, введите команду /delchapter *ID* раздела\n"
    response_text += "⚠️ Что бы удалить грам, введите команду /delgram *ID* раздела\n\n"
    response_text += "👁‍🗨 Разослать сообщение всем пользователям бота /send\n"
    response_text += "👁‍🗨 Для просмотра статистика за период /showstats *дней*\n"
    response_text += "👁‍🗨 Для добавления курьера /cour *юзернейм курьера без @*\n"

    print("USER IN ADMIN007", user.user_id, user.username)
    if user.is_admin:
        await msg.answer(response_text, reply_markup=kb.admin_panel)
    else:
        print(f"Пользователь {user.username} попытался войти в админ панель")


@router.message(Command("send"))
async def send_command(msg: Message, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if user.is_admin:
        await msg.answer("Введите текст, который вы хотите отправить всем пользователям.")
        await state.set_state(SendState.awaiting_text)
    else:
        await msg.answer("У вас нет прав для этой команды")


@router.message(Command("delchapter"))
async def delete_chapter(msg: Message, command: CommandObject):
    args = command.args
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if args and user.is_admin or args and user.is_super_admin:
        chapter = await sync_to_async(Chapter.objects.get)(id=args)
        chapter.delete()
        await msg.answer(f"Раздел {chapter.title} удалён")
    if not args and user.is_admin or not args and user.is_super_admin:
        await msg.answer("Введите ID раздела!\nНапример: /delchapter 5")


@router.message(Command("delgram"))
async def delete_gram(msg: Message, command: CommandObject):
    args = command.args
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if args and user.is_admin or args and user.is_super_admin:
        gram = await sync_to_async(Gram.objects.get)(id=args)
        gram.delete()
        await msg.answer(f"Грам {gram.gram}, относящий к {gram.chapter.title} удалён")
    if not args and user.is_admin or not args and user.is_super_admin:
        await msg.answer("Введите ID грама!\nНапример: /delgram 5")


@router.message(Command("showstats"))
async  def show_statistic(msg: Message, command: CommandObject):
    args = command.args
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if args and user.is_admin or args and user.is_super_admin:
        try:
            days_ago = int(args)
        except ValueError:
            await msg.answer("Введите кол-во дней (период)\nНапример /showstats 4")
            return
        three_days_ago = datetime.now() - timedelta(days=int(args))
        sold_products = await sync_to_async(Product.objects.filter)(
            sold=True,
            created_at__gte=three_days_ago
        )
        all_sum = 0
        text = "Статистика проданных продуктов за последние {} дней:\n\n".format(days_ago)
        for stats in sold_products:
            text += f"ID продукта: {stats.id}\n"
            text += f"Продан пользователю: {stats.user.username if stats.user.username else stats.user.user_id}\n"
            text += f"Раздел: {stats.gram.chapter.title}\n"
            text += f"Грамм: {stats.gram.gram}\n"
            text += f"Стоимость: {stats.gram.usd}\n"
            text += "-" * 20 + "\n"
            all_sum += stats.gram.usd
        text += f"\n\nОбщая сумма проданных продуктов {all_sum} за {days_ago} дней"
        await msg.answer(text)


@router.message(Command("c"))
async def courier(msg: Message):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if user.is_courier:
        await msg.answer("*Добавление продуктов:*\n➖➖➖➖➖➖➖➖➖➖➖➖\n",
                         reply_markup=kb.add_product_cour)


@router.message(Command("cour"))
async def add_courier(msg: Message, command: CommandObject):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if user.is_admin:
        args = command.args
        cour = await sync_to_async(TelegramUser.objects.get)(username=args)
        if cour.is_courier:
            cour.is_courier = False
            cour.save()
            await msg.answer(f"Пользователь @{user.username} удален из курьеров")
        elif not cour.is_courier:
            cour.is_courier = True
            cour.save()
            await msg.answer(f"Пользователь @{user.username} успешно добавлен в курьеры")


@router.message(Command("delproduct"))
async def del_product_admin(msg: Message, command: CommandObject):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if user.is_admin:
        args = command.args
        product = await sync_to_async(Product.objects.get)(id=args)
        product.delete()
        await msg.answer(f"({product.id}) `{product.text}`\nУдален")


@router.message(Command("showproduct"))
async def del_product_admin(msg: Message, command: CommandObject):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    if user.is_admin:
        args = command.args
        product = await sync_to_async(Product.objects.get)(id=args)
        await msg.answer(f"({product.id}) {product.text}\n"
                         f"{product.gram.chapter.title} {product.gram.gram}гр ${product.gram.usd}\n"
                         f"{'Куплен@'+product.user.username + '' if product.user else 'Не куплен'}\n"
                         f"Выложил курьер: {product.courier.username if product.courier.username else product.courier.user_id}", parse_mode=None)
