from typing import Literal

from telebot import TeleBot
from telebot.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from api.client import StorageAPI
from handlers.dependencies import (
    TelegramUser,
    delete_messages,
    append_user_message,
    handler_message,
)
from handlers.start.start_command import add_user
from handlers.utils import (
    TranslationKeys,
    Buttons,
)


def my_courses_command_handler(
    message: Message | CallbackQuery,
    bot: TeleBot,
    storage: StorageAPI,
    actin: Literal["send", "edit"] = "send",
):
    """
    Обработчик команды /my_courses в Telegram боте.

    Эта функция обрабатывает команду /my_courses и показывает, какие у пользователя есть курсы, начатые, законченные,
    приостановленные

    Args:
        message (Message | CallbackQuery): Сообщение от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        actin (str): действие, которое надо выполнить с сообщением, send, если отправить новое или edit,
         если надо изменит старое
    """

    user_telegram = TelegramUser(message=message)
    if actin == "send":
        delete_messages(
            bot=bot, storage=storage, type_message="system", user_telegram=user_telegram
        )
        append_user_message(
            user_telegram=user_telegram, storage=storage, type_message="system"
        )
    try:
        user = storage.get_user(user_telegram=user_telegram)
        if not user:
            add_user(user_telegram=user_telegram, storage=storage, bot=bot)
        else:
            active_course = storage.get_active_user_course(user_telegram=user_telegram)
            unfinished_courses = storage.get_unfinished_user_courses(
                user_telegram=user_telegram
            )
            archived_courses = storage.get_archived_user_courses(
                user_telegram=user_telegram
            )
            buttons = []
            markup = InlineKeyboardMarkup(row_width=1)
            if active_course:
                active_course_button = storage.get_translation(
                    message_key=Buttons.active_course.text,
                    language_code=user_telegram.language,
                )
                active_course_btn = InlineKeyboardButton(
                    text=active_course_button.message_text,
                    callback_data=f"{Buttons.show_user_course_info.callback}_{active_course.id}",
                )
                buttons.append(active_course_btn)
            if unfinished_courses.data:
                unfinished_courses_button = storage.get_translation(
                    message_key=Buttons.unfinished_courses.text,
                    language_code=user_telegram.language,
                )
                unfinished_courses_btn = InlineKeyboardButton(
                    text=unfinished_courses_button.message_text,
                    callback_data=f"{Buttons.unfinished_courses.callback}_1",
                )
                buttons.append(unfinished_courses_btn)
            if archived_courses.data:
                archived_courses_button = storage.get_translation(
                    message_key=Buttons.archived_courses.text,
                    language_code=user_telegram.language,
                )
                archived_courses_btn = InlineKeyboardButton(
                    text=archived_courses_button.message_text,
                    callback_data=f"{Buttons.archived_courses.callback}_1",
                )
                buttons.append(archived_courses_btn)
            manage_courses = storage.get_translation(
                message_key=TranslationKeys.manage_courses_message,
                language_code=user_telegram.language,
            )
            markup.add(*buttons)
            handler_message(
                bot=bot,
                text=manage_courses.message_text,
                chat_id=user_telegram.chat_id,
                user_telegram=user_telegram,
                storage=storage,
                type_message="system",
                actin=actin,
                markup=markup,
                message_id=user_telegram.message_id
            )
    except Exception as e:
        handler_message(
            bot=bot,
            text="Error communicating with the external service., {}".format(e),
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
        )
