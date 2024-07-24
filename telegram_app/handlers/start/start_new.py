from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message
from handlers.utils import TranslationKeys, Buttons


def start_new_education(user_telegram: TelegramUser, bot: TeleBot, storage: StorageAPI):
    """
    Запускает процесс нового обучения для пользователя.

    Эта функция отправляет сообщение пользователю с предложением начать новое
    обучение, если активных курсов не найдено.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    no_courses = storage.get_translation(
        message_key=TranslationKeys.no_courses_start_message,
        language_code=user_telegram.language,
    )
    markup, btn = start_new_education_btn(user_telegram=user_telegram, storage=storage)
    markup.add(btn)
    handler_message(
        bot=bot,
        text=no_courses.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
        markup=markup,
    )


def start_new_education_btn(user_telegram: TelegramUser, storage: StorageAPI):
    """
    Создает кнопку для начала нового обучения.

    Эта функция создает кнопку и разметку для отправки пользователю.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        storage (StorageAPI): Экземпляр для работы с хранилищем данных

    Returns:
        tuple: Кортеж, содержащий разметку клавиатуры и кнопку.
    """
    btn_start = storage.get_translation(
        message_key=Buttons.start_new_education.text,
        language_code=user_telegram.language,
    )
    markup = InlineKeyboardMarkup(row_width=2)
    btn = InlineKeyboardButton(
        text=btn_start.message_text, callback_data=Buttons.check_payment.callback
    )

    return markup, btn
