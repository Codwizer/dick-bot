import random
import sqlite3
import asyncio
import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command, ChatTypeFilter
from aiogram.types import InputTextMessageContent


bot = Bot(token="1234", parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS dick_sizes (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    dick_size INTEGER,
    last_time_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    group_id INTEGER DEFAULT 0
)
"""


cursor.execute(create_table_query)
conn.commit()


@dp.message_handler(Command("start"), ChatTypeFilter(types.ChatType.SUPERGROUP))
@dp.message_handler(Command("dick"), ChatTypeFilter(types.ChatType.SUPERGROUP))
async def cmd_dick(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    group_id = message.chat.id

    select_query = f"SELECT username, first_name, last_name, dick_size, last_time_checked FROM dick_sizes WHERE user_id={user_id} AND group_id={group_id}"
    cursor.execute(select_query)
    result = cursor.fetchone()

    if result is None:
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        dick_size = random.randint(1, 20)
        insert_query = f"INSERT INTO dick_sizes(user_id, username, first_name, last_name, dick_size, group_id) VALUES({user_id}, '{username}', '{first_name}', '{last_name}', {dick_size}, {group_id})"
        cursor.execute(insert_query)
        conn.commit()

        await message.reply(
            f"Тебе создали новый хуй, поздравляю. Он равен {dick_size} см"
        )
    else:
        username, first_name, last_name, dick_size, last_time_checked = result
        last_time_checked = datetime.datetime.fromisoformat(last_time_checked)
        current_time = datetime.datetime.now()
        time_since_last_check = (current_time - last_time_checked).total_seconds()

        if time_since_last_check < 24 * 60 * 60:
            remaining_time = int(24 * 60 * 60 - time_since_last_check)
            hours, remaining_time = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remaining_time, 60)
            await message.reply(
                f"Ты идиот. Жди ещё {hours} часов {minutes} минут и {seconds} секунд"
            )
            return

        change = random.randint(1, 20)
        dick_size += change
        update_query = f"UPDATE dick_sizes SET dick_size={dick_size}, last_time_checked=CURRENT_TIMESTAMP WHERE user_id={user_id} AND group_id={group_id}"
        cursor.execute(update_query)
        conn.commit()

        await message.reply(
            f"Твой хер вырос на {change} см, поздравляю. Сейчас он равен {dick_size} см"
        )


@dp.message_handler(
    ChatTypeFilter(types.ChatType.PRIVATE), content_types=types.ContentType.ANY
)
async def bot_msg_handler(message: types.Message):
    me = await bot.get_me()
    print(me)
    await message.reply(
        "Эта команда работает только в групповых чатах. "
        "Добавь меня в группу, чтобы использовать эту функцию.",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Добавить бота",
                        url=f"https://t.me/{me.username}?startgroup=true",
                    )
                ],
            ]
        ),
    )


@dp.message_handler(Command("top"), ChatTypeFilter(types.ChatType.SUPERGROUP))
async def cmd_top(message: types.Message):
    group_id = message.chat.id

    chat = await bot.get_chat(group_id)
    group_name = chat.title

    select_query = f"SELECT username, dick_size FROM dick_sizes WHERE group_id={group_id} ORDER BY dick_size DESC LIMIT 5"
    cursor.execute(select_query)
    top_dick_sizes = cursor.fetchall()

    if not top_dick_sizes:
        await message.reply("В этой группе ещё никто не замерял свою письку")
        return

    top_list = [
        f"{i+1}. @{username}: {size} см"
        for i, (username, size) in enumerate(top_dick_sizes)
    ]
    top_text = (
        f"<b>Топ 5 хуястых</b> данной группы <b><u>{group_name}</u></b>:\n"
        + "\n".join(top_list)
    )

    select_query_all = "SELECT username, dick_size, group_id FROM dick_sizes ORDER BY dick_size DESC LIMIT 3"
    cursor.execute(select_query_all)
    all_dick_sizes = cursor.fetchall()

    group_dict = {}
    for row in all_dick_sizes:
        username, size, group_id = row
        if group_id not in group_dict:
            group_dict[group_id] = []
        group_dict[group_id].append((username, size))

    top_groups = []
    for group_id, dick_sizes in group_dict.items():
        dick_sizes_sorted = sorted(dick_sizes, key=lambda x: x[1], reverse=True)
        top_groups.extend(
            [(group_id, user, size) for user, size in dick_sizes_sorted[:3]]
        )

    if not top_groups:
        return

    top_list_all = [
        f"{i+1}. {group_name} | @{user}: {size} см"
        for i, (group_id, user, size) in enumerate(top_groups)
    ]
    top_text_all = (
        "<b>Топ 3</b> тотальных хуя <b><u>по всему миру</u></b>:\n"
        + "\n".join(top_list_all)
    )

    await message.reply(top_text + "\n\n" + top_text_all)


@dp.inline_handler()
async def inline_handler(query: types.InlineQuery):
    results = []
    text = query.query.strip()

    if not text:
        select_query_all = (
            "SELECT username, dick_size FROM dick_sizes ORDER BY dick_size DESC LIMIT 3"
        )
        cursor.execute(select_query_all)
        dick_sizes = cursor.fetchall()

        message_list = [
            f"{i+1}. @{username}: {size} см"
            for i, (username, size) in enumerate(dick_sizes)
        ]
        message_text = "<b>Топ 3 хуя</b> по всем группам:\n\n" + "\n".join(message_list)

        results.append(
            types.InlineQueryResultArticle(
                id="top_3_dick",
                title="🏆 Топ 3 хуя",
                description="Топ-3 тотальных хуя по всем группам",
                input_message_content=types.InputTextMessageContent(message_text),
            )
        )

    await bot.answer_inline_query(query.id, results)

    if text.startswith(""):
        username = text[1:]
        select_query = f"SELECT username, first_name, last_name, dick_size FROM dick_sizes WHERE username='{username}' ORDER BY last_time_checked DESC LIMIT 5"
        cursor.execute(select_query)
        rows = cursor.fetchall()

        title = "Размер члена"
        for row in rows:
            username, first_name, last_name, dick_size = row
            title_text = f"@{username} ({first_name} {last_name}) - {dick_size} см"
            description = f"@{username} ({first_name} {last_name})"
            message_text = f"Чел {first_name} замерил свой член и кричит, что его размер равен {dick_size}см, а твой?!"
            results.append(
                types.InlineQueryResultArticle(
                    id=username,
                    title=title_text,
                    description=description,
                    input_message_content=types.InputTextMessageContent(message_text),
                )
            )
        await bot.answer_inline_query(query.id, results)


if __name__ == "__main__":
    asyncio.run(dp.start_polling())
