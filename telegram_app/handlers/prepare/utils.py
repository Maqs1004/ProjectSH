from telebot import TeleBot
from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message
from handlers.utils import TranslationKeys, Buttons
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


def check_expired_prepare(
    user_telegram: TelegramUser,
    bot: TeleBot,
    storage: StorageAPI,
    only_check: bool = False,
):
    """
    Проверяет на доступность подготовительной информации и возвращает ее.

    Если информация о подготовке истекла, отправляет сообщение пользователю с предложением начать заново.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        only_check (bool): Флаг указывающий, что нужно только проверить наличие, не выводя ошибки

    Returns:
        info: Информация о текущей стадии подготовки или None, если информация истекла.
    """
    info = storage.get_prepare_stage(
        user_telegram_id=user_telegram.id,
    )

    if info is None:
        if only_check:
            return
        # TODO где то тут ошибка
        reason, markup, btn = try_again(
            user_telegram=user_telegram,
            message_key=TranslationKeys.time_expired_message,
            storage=storage,
            callback_data=Buttons.start_new_education.callback,
        )
        handler_message(
            bot=bot,
            text=reason.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=user_telegram.message_id,
            markup=markup,
        )
    return info


def try_again(
    user_telegram: TelegramUser,
    message_key: str,
    storage: StorageAPI,
    callback_data: str,
):
    """
    Формирует сообщение и кнопку для повторной попытки.

    Создает сообщение и разметку клавиатуры с кнопкой для повторной попытки.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        message_key (str): Ключ для получения перевода сообщения
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        callback_data (str): Данные callback для кнопки

    Returns:
        tuple: Сообщение о причине, разметка клавиатуры и кнопка.
    """
    reason = storage.get_translation(
        message_key=message_key, language_code=user_telegram.language
    )
    repeat = storage.get_translation(
        message_key=Buttons.repeat_button.text,
        language_code=user_telegram.language,
    )
    markup = InlineKeyboardMarkup(row_width=1)
    btn = InlineKeyboardButton(text=repeat.message_text, callback_data=callback_data)
    markup.add(btn)
    return reason, markup, btn


def send_or_edit(storage, message_key, user_telegram, call, bot):
    text = storage.get_translation(
        message_key=message_key,
        language_code=user_telegram.language,
    )
    if isinstance(call, CallbackQuery):
        msg = handler_message(
            bot=bot,
            text=text.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=user_telegram.message_id,
        )
    else:
        msg = handler_message(
            bot=bot,
            text=text.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
        )
    return msg

