from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from ..models import TelegramUser, Chapter, Gram
from .. import kb, text
from ..states import SendState

router = Router()


@router.message(Command("start"))
async def start_command(msg: Message, state: FSMContext, bot: Bot, command: CommandObject):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=msg.from_user.id)
    referred_by_id = command.args
    if user.referred_by is None and referred_by_id and created:
        user.referred_by = await sync_to_async(TelegramUser.objects.get)(id=referred_by_id)
        await bot.send_message(user.referred_by.user_id, text=text.referred_announce.format(user=user.username))

    user.first_name = msg.from_user.first_name
    user.last_name = msg.from_user.last_name
    user.username = msg.from_user.username
    user.save()
    print("USER IN START", user.user_id, user.username)
    is_subscribed = await bot.get_chat_member(chat_id="@thischannelfortests", user_id=msg.from_user.id)
    if is_subscribed.status in ['member', 'administrator', 'creator']:
        await msg.answer("Бот готовится, притегните ремни!", reply_markup=kb.menu)
    else:
        await msg.answer("Подпишитесь на канал", reply_markup=kb.not_subscribed)


@router.message(Command("admin007"))
async def admin_panel(msg: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    chapters = await sync_to_async(Chapter.objects.all)()
    response_text = "➖➖➖*КОММАНДЫ АДМИНИСТРАТОРА*➖➖➖\n\n"
    for i in chapters:
        response_text += f"⚫️ *({i.id}) | {i.title}* \n"
        grams = await sync_to_async(Gram.objects.filter)(chapter=i)
        for i in grams:
            response_text += f"〰️〰️*ID*: ({i.id}) | вес {i.gram} GR = ${i.usd}\n"
    response_text += "\n⚠️ Что бы удалить раздел, введите команду /delchapter *ID* раздела\n"
    response_text += "⚠️ Что бы удалить грам, введите команду /delgram *ID* раздела\n"

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
