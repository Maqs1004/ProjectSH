from telebot import TeleBot
from telebot.types import Message
from api.client import StorageAPI
from handlers.dependencies import (
    TelegramUser,
    append_user_message,
    delete_messages,
    handler_message,
)
from handlers.utils import (
    TranslationKeys,
)


def help_command_handler(message: Message, bot: TeleBot, storage: StorageAPI):
    """
    Обработчик команды /help в Telegram боте.

    Эта функция обрабатывает команду /help, и выводит сообщение с информацией.

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
    help_message = storage.get_translation(
        message_key=TranslationKeys.help_message,
        language_code=user_telegram.language,
    )
    handler_message(
        bot=bot,
        text=help_message.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
        parse_mode="Markdown",
    )
