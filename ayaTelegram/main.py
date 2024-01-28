from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
import asyncio

from aiogram import executor

from openai import OpenAI
import json
import time

from config import api_key, assistant_id, bot_token

openai_api_key = api_key
openai_assistant_id = assistant_id

openai_client = OpenAI(api_key=openai_api_key)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)

user_sessions = {}

@dp.message_handler(commands=['start'])
async def start_session(message: types.Message):
    thread = openai_client.beta.threads.create()
    user_sessions[message.chat.id] = thread.id
    await message.reply("Привет! Для начала общения введите ваш запрос.")

# Clear current thread 
@dp.message_handler(commands=['newtopic'])
async def clear_session(message: types.Message):
    if message.chat.id in user_sessions:
        del user_sessions[message.chat.id]
        await message.reply("Ваша сессия очищена. Теперь вы можете начать заново.")
    else:
        await message.reply("У вас нет активной сессии.")




@dp.message_handler()
async def handle_message(message: types.Message):
    if message.chat.id not in user_sessions:
        thread = openai_client.beta.threads.create()
        user_sessions[message.chat.id] = thread.id
    else:
        thread_id = user_sessions[message.chat.id]


    msg = await message.reply("Я размышляю над вашим вопросом...")

    openai_client.beta.threads.messages.create(
        thread_id=user_sessions[message.chat.id],
        role="user",
        content=message.text,
    )

    run = openai_client.beta.threads.runs.create(
        thread_id=user_sessions[message.chat.id],
        assistant_id=openai_assistant_id,
    )

    while run.status == "queued" or run.status == "in_progress":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=user_sessions[message.chat.id],
            run_id=run.id,
        )
        time.sleep(0.5)


    messages = openai_client.beta.threads.messages.list(thread_id=user_sessions[message.chat.id])

    item = json.loads(messages.model_dump_json())['data'][0]['content'][0]['text']['value']
    
 
    await msg.edit_text(item, parse_mode=ParseMode.MARKDOWN)

if __name__ == '__main__':
    executor.start_polling(dp)

