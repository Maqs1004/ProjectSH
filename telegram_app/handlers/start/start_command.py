from telebot import TeleBot
from telebot.types import Message
from api.client import StorageAPI
from handlers.dependencies import (
    TelegramUser,
    delete_messages,
    append_user_message,
    handler_message,
)
from handlers.utils import (
    TranslationKeys,
)
from handlers.start.start_new import start_new_education, start_new_education_btn
from handlers.education.education_continue import continue_education


def start_command_handler(message: Message, bot: TeleBot, storage: StorageAPI):
    """
    Обработчик команды /start в Telegram боте.

    Эта функция обрабатывает команду /start, проверяет наличие пользователя
    в базе данных, запускает или продолжает процесс обучения в зависимости от
    текущего состояния пользователя.

    Args:
        message (Message): Сообщение от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=message)
    delete_messages(
        bot=bot, storage=storage, type_message="system", user_telegram=user_telegram
    )
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="system"
    )
    try:
        user = storage.get_user(user_telegram=user_telegram)
        if user:
            active_user_course = storage.get_active_user_course(
                user_telegram=user_telegram
            )
            if active_user_course:
                continue_education(
                    user_telegram=user_telegram,
                    bot=bot,
                    storage=storage,
                    user_course=active_user_course,
                )
            else:
                start_new_education(
                    user_telegram=user_telegram, bot=bot, storage=storage
                )
                return
        else:
            add_user(user_telegram=user_telegram, storage=storage, bot=bot)
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


def add_user(storage: StorageAPI, user_telegram: TelegramUser, bot: TeleBot) -> None:
    storage.add_user(user_telegram)

    welcome_message = storage.get_translation(
        message_key=TranslationKeys.welcome_message,
        language_code=user_telegram.language,
    )
    markup, btn = start_new_education_btn(user_telegram=user_telegram, storage=storage)
    markup.add(btn)
    handler_message(
        bot=bot,
        text=welcome_message.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
        markup=markup,
        parse_mode="Markdown",
    )
