from telebot import TeleBot
from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message
from handlers.utils import Buttons, TranslationKeys
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
)
from schemas.course_schemas import CurrentStage


def preparing_material(
    call: Message | CallbackQuery, bot: TeleBot, storage: StorageAPI
):
    """
    Обрабатывает этап подготовки материалов для курса.

    Проверяет актуальность информации о подготовке, создаёт материалы для курса и отправляет
    пользователю сообщение о готовности материалов или об ошибке.

    Args:
        call (Message | CallbackQuery): Сообщение или запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(call)
    prepare_material = storage.get_translation(
        message_key=TranslationKeys.preparing_material_message,
        language_code=user_telegram.language,
    )
    user_course_id = call.data.split(f"{Buttons.prepare_material.callback}_")[1]
    user_course = storage.get_user_course_info(user_course_id=user_course_id)
    message = handler_message(
        bot=bot,
        text=prepare_material.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=user_telegram.message_id,
    )
    storage.patch_user_course_info(
        user_course_id=user_course_id, current_stage=CurrentStage.generating.value
    )
    user_course = storage.create_material(
        course_id=user_course.course_id, language=user_telegram.language
    )
    if user_course:
        material_ready, markup = get_translations_and_markup(
            storage=storage,
            message_key=TranslationKeys.material_ready_message,
            button_key_text=Buttons.start_education.text,
            callback_prefix=Buttons.start_education.callback,
            language_code=user_telegram.language,
            course_id=user_course.id,
        )

        storage.redis_storage.delete_keys_by_pattern(
            pattern=f"created_course:user_telegram_id:{user_telegram.id}*"
        )
        handler_message(
            bot=bot,
            text=material_ready.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=message.message_id,
            markup=markup,
        )
        return
    material_preparation_error, markup = get_translations_and_markup(
        storage=storage,
        message_key=TranslationKeys.material_preparation_error_message,
        button_key_text=Buttons.repeat_button.text,
        callback_prefix=Buttons.prepare_material.callback,
        language_code=user_telegram.language,
        course_id=user_course.course_id,
    )
    handler_message(
        bot=bot,
        text=material_preparation_error.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=message.message_id,
        markup=markup,
    )


def get_translations_and_markup(
    storage: StorageAPI,
    message_key: str,
    button_key_text: str,
    callback_prefix,
    language_code,
    course_id: str | int,
):
    """
    Получает переводы для сообщения и кнопок, создает разметку клавиатуры.

    Args:
        storage (StorageAPI): Экземпляр для работы с хранилищем данных.
        message_key (str): Ключ для получения перевода сообщения.
        button_key_text (str): Ключ для получения перевода текста кнопки.
        callback_prefix (str): Префикс для callback_data кнопки.
        language_code (str): Код языка.
        course_id (str): Идентификатор курса.

    Returns:
        tuple: Кортеж, содержащий сообщение и разметку клавиатуры.
    """
    message = storage.get_translation(
        message_key=message_key, language_code=language_code
    )

    button_template = storage.get_translation(
        message_key=button_key_text, language_code=language_code
    )
    markup = InlineKeyboardMarkup(row_width=1)
    button = InlineKeyboardButton(
        text=button_template.message_text,
        callback_data=f"{callback_prefix}_{course_id}",
    )
    markup.add(button)

    return message, markup
