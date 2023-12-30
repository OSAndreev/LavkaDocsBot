from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import imaplib
import email
import base64
from bs4 import BeautifulSoup
from main import bot



scheduler = AsyncIOScheduler()
router = Router()
form = []
# Ссылки на формы по порядку
form_links = ['https://forms.yandex.ru/u/6574ffa090fa7b5ff767f78a/', 'https://forms.yandex.ru/u/6575008d43f74f601e0891dc/', 'https://forms.yandex.ru/u/657500b4eb614663189bd7b2/']
mail = imaplib.IMAP4_SSL('imap.yandex.ru')
mail.login('akelfa@yandex.ru', 'sshjgumsnkahaifk')


@router.message(Command('get_docs'))
async def get_docs_command(message: Message, state):
    # Очищаем информацию по формам на всякий случай
    await state.update_data(forms_info=[])
    chat_id = str(message.chat.id)
    await state.update_data(chat_id=chat_id)
    try:
        # Получаем username из команды
        username = message.text.split(' ')[1]
        await state.update_data(username=username)
        # Отправляем сообщение с приветствием
        await message.answer(f"{username}, заполните, пожалуйста документы. Вот ссылка: https://forms.yandex.ru/u/6574ffa090fa7b5ff767f78a/")
        scheduler.add_job(get_message, "interval", seconds=10, args=(state, ), id='parser' + chat_id)    # Запускаем парсинг ответов с почты
        # Запускаем регулярные напоминания в чат
        scheduler.add_job(remind_form, "interval", minutes=1, args=(f"{username}, заполните, пожалуйста документы. Вот ссылка: https://forms.yandex.ru/u/6574ffa090fa7b5ff767f78a/)", state ),
                          id='form' + '&' + chat_id + '&' + '1')
    except IndexError:
        # Если не указан username, отправляем сообщение об ошибке
        await message.answer("Пожалуйста, укажите username после команды /get_docs")


# Отправка сообщения со ссылкой на следующую форму
async def send_second_form(form_num, state):
    user_data = await state.get_data()
    chat_id = user_data['chat_id']
    username = user_data['username']
    global form_links
    await bot.send_message(chat_id, f"Поздравляем! Вы прошли ещё один этап квеста. {username}, заполните, пожалуйста документы. Вот ссылка: {form_links[form_num]}")
    scheduler.add_job(remind_form, "interval", minutes=1, args=(f"{username}, заполните, пожалуйста документы. Вот ссылка: {form_links[form_num]}", state),
                      id=f'form&{chat_id}&{form_num + 1}')


# Функция, которая парсит новые письма с информацией о заполнении почты
# Если находит новое письмо, кладёт ответы в form_info
async def get_message(state):
    user_data = await state.get_data()
    forms_info = user_data['forms_info']
    mail.list()
    mail.select("inbox")
    result, data = mail.search(None, "ALL")
    ids = data[0]
    id_list = ids.split()
    if len(id_list) > 0:
        latest_email_id = id_list[-1]
        print(latest_email_id)
        result, data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)
        subject = email_message['Subject'].split('?')[3]
        subject = base64.b64decode(subject).decode('utf-8')
        if 'form' in subject:
            # Получение текста письма
            body = None
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_maintype() == 'text':
                        body = BeautifulSoup(base64.b64decode(part.get_payload()).decode(),
                                             'html.parser').body.get_text()

                        body = str(body)
                        break
            else:
                body = email_message.get_payload(decode=True).decode('utf-8')
            answer_id, answers = body.split('answer_id:')[1].split(',answer_data:')
            answer_data = dict()
            for pair in answers.split('\n\n')[:-2]:
                key, value = pair.split(':\n')
                answer_data[key] = value
            if '@' + answer_data['username'] == user_data['username'] and \
                    (not forms_info or forms_info[-1]['id'] != answer_id):
                forms_info.append({'data': answer_data, 'id': answer_id})
                await state.update_data(forms_info=forms_info)
                scheduler.remove_job('form' + '&' + user_data['chat_id'] + '&' + str(len(forms_info)))

                # Если все три формы заполнены, отправляем информацию по ним и выгружаем в чат
                if len(forms_info) == 3:

                    await send_forms_info(state)
                    scheduler.remove_job('parser' + user_data['chat_id'])
                else:
                    await send_second_form(len(forms_info), state)
            mail.store(latest_email_id, '+FLAGS', '\\Deleted')
            mail.expunge()

    print(forms_info)


# Отправляет ответы на формы в чат
async def send_forms_info(state):
    global bot
    user_data = await state.get_data()
    forms_info = user_data['forms_info']
    user_data = await state.get_data()
    chat_id = user_data['chat_id']
    await bot.send_message(chat_id, "Квест пройден! Вот ваши ответы:")
    for form_info in forms_info:
        await bot.send_message(chat_id, '\n'.join([key + ':' + form_info['data'][key]
                                                   for key in form_info['data']]))


# Отправляет сообщение с указанным текстом в чат
async def remind_form(text, state):
    global bot
    user_data = await state.get_data()
    chat_id = user_data['chat_id']
    await bot.send_message(chat_id, text)
