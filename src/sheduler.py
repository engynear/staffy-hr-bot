from db import get_db
from aiogram import Bot

import text
import random
from utils import wish_to_image

from aiogram.types import InputMediaPhoto, InputFile, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton


async def friday_thank_you(bot: Bot):
    db = await get_db()
    users = await db.get_users()
    print(users)
    for user in users:
        wishes = await db.get_last_week_wishes(user['id'])

        media_group = []
        for wish in wishes:
            from_user = await db.get_user(wish['from_user_id'])
            to_user = await db.get_user(wish['to_user_id'])
            image_bytes = await wish_to_image(from_user, to_user, wish['wish_text'])

            input_file = BufferedInputFile(file=image_bytes.read(), filename='wish.png')
            media = InputMediaPhoto(media=input_file)
            media_group.append(media)  # добавляем media в media group

        if media_group:  # проверяем, не пуста ли media group
            await bot.send_message(user['id'], random.choice(text.friday_thank_you))
            await bot.send_media_group(user['id'], media=media_group) 

async def friday_thank_you_prepare(bot: Bot):
    db = await get_db()
    users = await db.get_users()
    for user in users:
        await bot.send_sticker(user['id'], text.love_stick)
        await bot.send_message(user['id'], random.choice(text.friday_thank_you_prepare), reply_markup=InlineKeyboardBuilder().add(
                              InlineKeyboardButton(text='Написать спасибо', callback_data='send_more')).as_markup())

async def monday_thank_you_prepare(bot: Bot):
    db = await get_db()
    users = await db.get_users()
    for user in users:
        await bot.send_sticker(user['id'], text.work_stick)
        await bot.send_message(user['id'], random.choice(text.monday_thank_you_prepare), reply_markup=InlineKeyboardBuilder().add(
                              InlineKeyboardButton(text='Написать спасибо', callback_data='send_more')).as_markup())