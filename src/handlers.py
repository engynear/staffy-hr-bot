from typing import Union
import random

from aiogram import types, F, Router, flags
from aiogram.types import Message
from aiogram.filters import Command, StateFilter, Filter, CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardBuilder, KeyboardButton
from aiogram.fsm.context import FSMContext

import text
from db import get_db
from states import WishFSM, TeamStatus, UserInfo
import utils


router = Router()


async def select_team_member(event: Union[types.Message, types.CallbackQuery], state: FSMContext):
    print('select team member')
    db = await get_db()

    # Определение user_id в зависимости от типа event
    user_id = event.from_user.id if isinstance(event, types.CallbackQuery) else event.from_user.id
    message = event.message if isinstance(event, types.CallbackQuery) else event
    user_team = await db.get_user_team(user_id)
    team_members = await db.get_team_members(user_team['id'])
    builder = InlineKeyboardBuilder()
    for user in team_members:
        if user['id'] == user_id:
            user['name'] = 'Себе'
        builder.add(InlineKeyboardButton(text=f'{user["name"]}', callback_data=str(user['id'])))
        print(f'{user["name"]} {user["id"]}')
    builder.adjust(1)
    await state.set_state(WishFSM.SelectTeamMember)
    await message.answer_sticker(text.question_stick)
    await message.answer(text.choose_team_member, reply_markup=builder.as_markup())


async def add_to_team(args, message: types.Message, db, state: FSMContext):
    if args == 'vovateam':
        await db.add_team_member(1, message.from_user.id)
        await message.answer(text.added_to_team)
        await state.set_state(TeamStatus.InTeam)
        print('added to team')

async def check_if_in_team(message: types.Message, db):
    user_team = await db.get_user_team(message.from_user.id)
    if not user_team:
        return False
    return True

@router.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext, command: CommandObject):
    db = await get_db()
    user = await db.get_user(message.from_user.id)

    args = command.args

    if not user:
        await db.add_user(message.from_user)
        await message.answer_sticker(text.hi_stick)
        await message.answer(text.start_message)
        if args:
            await add_to_team(args, message, db, state)

        # answer text.get_name with button with message.from_user.full_name as default variant. Keyboard not inline
        await message.answer(text.get_name, reply_markup=types.ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text=message.from_user.full_name)]
        ], resize_keyboard=True, one_time_keyboard=True))
        await state.set_state(UserInfo.GetName)
        return

    if args:
        if not await check_if_in_team(message, db):
            await add_to_team(args, message, db, state)
        
    if await check_if_in_team(message, db):
        await select_team_member(message, state)
    

@router.message(StateFilter(UserInfo.GetName))
async def process_get_name(message: types.Message, state: FSMContext):
    db = await get_db()
    await db.update_user(message.from_user.id, message.text)
    await message.answer(text.added_name, reply_markup=InlineKeyboardBuilder().add(
        InlineKeyboardButton(text='Продолжить', callback_data='continue')).as_markup())

    if not await check_if_in_team(message, db):
        await state.set_state(TeamStatus.NotInTeam)
        return

@router.message(StateFilter(TeamStatus.NotInTeam))
async def process_not_in_team(message: types.Message, state: FSMContext):
    await message.answer_sticker(text.not_in_team_stick)
    await message.answer(text.not_in_team)

@router.callback_query(StateFilter(TeamStatus.InTeam), F.data == 'continue')
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer('Переходим к выбору члена команды')
    await select_team_member(callback_query, state)


@router.callback_query(StateFilter(TeamStatus.NotInTeam))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer('Вы не состоите в команде. Зайдите по специальной ссылке, которую отправили вам в чат.')
    await callback_query.message.answer_sticker(text.not_in_team_stick)
    await callback_query.message.answer(text.not_in_team)

@router.callback_query(StateFilter(WishFSM.SelectTeamMember))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer(callback_query.data)

    await state.update_data(team_member_id=callback_query.data)
    await state.set_state(WishFSM.WriteWish)

    await callback_query.message.answer_sticker(text.write_stick)
    await callback_query.message.answer(random.choice(text.write_wish_variants),
                                         reply_markup=InlineKeyboardBuilder().add(
                                             InlineKeyboardButton(text='Отмена', callback_data='cancel')).as_markup())


@router.callback_query(StateFilter(WishFSM.WriteWish), F.data == 'cancel')
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    print('cancel')
    await callback_query.answer('Отменено')
    await select_team_member(callback_query, state)


@router.message(StateFilter(WishFSM.WriteWish))
async def process_write_wish(message: types.Message, state: FSMContext):
    print('write wish')
    db = await get_db()
    data = await state.get_data()
    team_member_id = int(data.get('team_member_id'))
    await db.add_wish(message.from_user.id, team_member_id, message.text)

    await state.set_state(WishFSM.WaitingForContinue)

    await message.answer_sticker(text.love_stick)
    await message.answer(text.sent_wish,
                          reply_markup=InlineKeyboardBuilder().add(
                              InlineKeyboardButton(text='Отправить ещё', callback_data='send_more')).as_markup())


@router.callback_query(F.data == 'send_more')
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer('Переходим к выбору члена команды')
    await select_team_member(callback_query, state)

@router.callback_query(StateFilter("*"))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer('Кажется, состояние устарело. Попробуйте начать сначала.')

# @router.message(F.sticker)
# async def process_sticker(message: types.Message):
#     await message.answer(message.sticker.file_id)