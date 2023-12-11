from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from telethon.sync import TelegramClient
from main import bot



scheduler = AsyncIOScheduler()
router = Router()
form = []
forms_info = []
form_links = ['https://forms.yandex.ru/u/6574ffa090fa7b5ff767f78a/', 'https://forms.yandex.ru/u/6575008d43f74f601e0891dc/', 'https://forms.yandex.ru/u/657500b4eb614663189bd7b2/']

@router.message(Command('get_docs'))
async def get_docs_command(message: Message, state):
    global chat_id
    global username
    chat_id = message.chat.id
    try:
        # Получаем username из команды
        username = message.text.split(' ')[1]

        # Отправляем сообщение с приветствием
        await message.answer(f"{username}, заполните, пожалуйста документы. Вот ссылка: https://forms.yandex.ru/u/6574ffa090fa7b5ff767f78a/")
        scheduler.add_job(get_message, "interval", seconds=10)
        scheduler.add_job(remind_form, "interval", minutes=1, args=(f"{username}, заполните, пожалуйста документы. Вот ссылка: https://forms.yandex.ru/u/6574ffa090fa7b5ff767f78a/)", ), id='form1')
    except IndexError:
        # Если не указан username, отправляем сообщение об ошибке
        await message.answer("Пожалуйста, укажите username после команды /get_docs")

async def send_second_form(form_num):
    global chat_id
    global bot
    global form_links
    await bot.send_message(chat_id, f"Поздравляем! Вы прошли ещё один этап квеста. {username}, заполните, пожалуйста документы. Вот ссылка: {form_links[form_num]}")
    scheduler.add_job(remind_form,"interval", minutes=1, args=(f"{username}, заполните, пожалуйста документы. Вот ссылка: {form_links[form_num]}", ),
                      id=f'form{form_num + 1}')


async def get_message():
    global forms_info
    async with TelegramClient('lavka_bot', '22526632', 'a2adec3a58f237733ab5521b5f75337b') as client:
        await client.start()
        chat = await client.get_entity(-4072882592)
        last_message = await client.get_messages(chat, limit=1)
        last_message = last_message[0]
        if (not forms_info or forms_info[-1].id != last_message.id) and 'форма' in last_message.text.lower():
            forms_info.append(last_message)
            scheduler.remove_job('form' + str(len(forms_info)))
            if len(forms_info) == 3:
                await send_forms_info()
                scheduler.remove_all_jobs()
            else:
                await send_second_form(len(forms_info))

    print(forms_info)


async def send_forms_info():
    global bot
    global forms_info
    await bot.send_message(chat_id, "Квест пройден! Вот ваши ответы:")
    for form_info in forms_info:
        await bot.send_message(chat_id, form_info.text)


async def remind_form(text):
    global bot
    await bot.send_message(chat_id, text)
# @router.message(Command('get_chat_id'))
# async def get_chat_id(message):
#     await message.answer(str(message.chat.id))