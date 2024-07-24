import re
import time
from typing import Literal

import telebot
from telebot import TeleBot
from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
)
from api.client import StorageAPI
from core.logging_config import logger
from schemas.create_education_schemas import CreatedEducationStage
from schemas.education_schemas import MessageStorageSchema


def get_message_types(message: Message | CallbackQuery):
    types = []
    if isinstance(message, CallbackQuery):
        message = message.message
    if message.text:
        types.append("text")
    if message.photo:
        types.append("photo")
    if message.video:
        types.append("video")
    if message.document:
        types.append("document")
    if message.audio:
        types.append("audio")
    if message.voice:
        types.append("voice")
    if message.sticker:
        types.append("sticker")
    if message.location:
        types.append("location")
    if message.contact:
        types.append("contact")
    if message.animation:
        types.append("animation")
    if message.video_note:
        types.append("video_note")
    return types


class TelegramUser:
    """
    Класс, представляющий пользователя Telegram.

    Этот класс используется для извлечения и хранения информации о пользователе
    из сообщения или запроса обратного вызова Telegram.

    Attributes:
        id (int): Идентификатор пользователя.
        language (str): Код языка пользователя.
        user_name (str): Имя пользователя (username) в Telegram.
        message_text (str): Текст сообщения.
        message_id (int): Идентификатор сообщения.
        message_typs (str): Тип сообщения.
        chat_id (int): Идентификатор чата.
        payment_info (dict): Словарь объекта SuccessfulPayment при выполнении оплаты
    """

    def __init__(self, message: Message | CallbackQuery):
        self.id = message.from_user.id
        self.language = message.from_user.language_code
        self.user_name = message.from_user.username
        if isinstance(message, Message):
            self.message_text = message.text
            self.payment_info = (
                message.successful_payment.__dict__
                if message.successful_payment
                else None
            )
        elif isinstance(message, CallbackQuery):
            self.message_text = message.message.text
        if isinstance(message, Message):
            self.message_id = message.message_id
        elif isinstance(message, CallbackQuery):
            self.message_id = message.message.message_id
        self.message_typs = get_message_types(message)
        if isinstance(message, Message):
            self.chat_id = message.chat.id
        elif isinstance(message, CallbackQuery):
            self.chat_id = message.message.chat.id


def format_plan_to_markdown(
    plan: dict[str, list[dict[str, list[str]]]], your_training_plan: str
):
    """
    Форматирует учебный план в Markdown формат для удобного представления.

    Args:
        plan (dict): Учебный план для форматирования.
        your_training_plan (str): Подготовительная фраза

    Returns:
        str: Учебный план, оформленный в виде Markdown строки.
    """
    formatted_text = f"{your_training_plan}\n\n"
    main_topic_number = 1
    for module_title, sub_modules in plan.items():
        formatted_text += f"<strong>{main_topic_number}) {module_title}</strong>\n\n"
        main_topic_number += 1
        for sub_module in sub_modules:
            for sub_module_title, contents in sub_module.items():
                formatted_text += f"<i>{sub_module_title}</i>\n"
                for content in contents:
                    formatted_text += f"-{content}\n"
                formatted_text += "\n"
    return formatted_text


def update_prepare_info(
    user_telegram: TelegramUser,
    created_info: CreatedEducationStage,
    storage: StorageAPI,
    new_stage: str,
):
    """
    Обновляет информацию о стадии подготовки курса и сохраняет её в кэш.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        created_info (CreatedEducationStage): Объект с информацией о стадии подготовки
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        new_stage (str): Новая стадия подготовки
    """
    cache_key = f"created_course:user_telegram_id:{user_telegram.id}"
    created_info.stage = new_stage
    created_info_dict = created_info.dict()
    storage.redis_storage.delete_keys_by_pattern(pattern=f"{cache_key}*")
    storage.redis_storage.set(cache_key=cache_key, cached=created_info_dict, ex=86400)


def handler_message(
    bot: TeleBot,
    text: str,
    chat_id: int,
    user_telegram: TelegramUser,
    storage: StorageAPI,
    type_message: Literal["system", "education", "quiz"],
    actin: Literal["send", "edit"],
    message_id: int | None = None,
    parse_mode: str | None = None,
    markup: (
        InlineKeyboardMarkup
        | ReplyKeyboardMarkup
        | ReplyKeyboardRemove
        | ForceReply
        | None
    ) = None,
) -> Message:
    """
    Обрабатывает отправку и редактирование сообщений в Telegram и записывает ID сообщений в историю, для дальнейшего
    редактирования либо удаления.

    Args:
        bot (TeleBot): Экземпляр Telegram бота.
        text (str): Текст сообщения.
        chat_id (int): Идентификатор чата.
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.
        storage (StorageAPI): Экземпляр для работы с хранилищем данных.
        type_message (Literal["system", "education", "quiz"]): Тип сообщения.
        actin (Literal["send", "edit"]): Действие с сообщением (отправка или редактирование).
        message_id (int | None): Идентификатор сообщения (для редактирования).
        parse_mode (str | None): Режим форматирования текста.
        markup (InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | ForceReply | None):
         Разметка клавиатуры.

    Returns:
        Message: Объект отправленного или отредактированного сообщения.
    """
    for try_count in range(3):
        try:
            if actin == "send":
                cache_key = (
                    f"user_telegram_id:{user_telegram.id}:type_message:{type_message}"
                )
                storage_message = storage.redis_storage.get(
                    base_model=MessageStorageSchema, cache_key=cache_key
                )
                if storage_message is None:
                    storage_message = MessageStorageSchema.model_validate(
                        {"messages": []}
                    )
                sent_message = bot.send_message(
                    text=text,
                    chat_id=chat_id,
                    reply_markup=markup,
                    parse_mode=parse_mode,
                )
                if type_message == "education":
                    storage_message.messages.append(
                        {
                            "message_id": sent_message.message_id,
                            "text": sent_message.text,
                        }
                    )
                else:
                    storage_message.messages.append(
                        {"message_id": sent_message.message_id}
                    )
                storage.redis_storage.delete_keys_by_pattern(pattern=f"{cache_key}*")
                storage.redis_storage.set(
                    cache_key=cache_key, cached=storage_message.dict()
                )

                return sent_message
            elif actin == "edit":
                edited_message = bot.edit_message_text(
                    text=text,
                    chat_id=chat_id,
                    reply_markup=markup,
                    message_id=message_id,
                    parse_mode=parse_mode,
                )
                return edited_message
        except telebot.apihelper.ApiTelegramException as exception:
            if exception.error_code == 429:
                logger.warning(exception.description)
                time.sleep(2)


def append_user_message(
    user_telegram: TelegramUser,
    storage: StorageAPI,
    type_message: Literal["system", "education", "quiz"],
):
    """
    Добавляет сообщение пользователя в историю сообщений.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.
        storage (StorageAPI): Экземпляр для работы с хранилищем данных.
        type_message (Literal["system", "education", "quiz"]): Тип сообщения.
    """
    cache_key = f"user_telegram_id:{user_telegram.id}:type_message:{type_message}"
    storage_message = storage.redis_storage.get(
        base_model=MessageStorageSchema, cache_key=cache_key
    )
    if storage_message is None:
        storage_message = MessageStorageSchema.model_validate({"messages": []})
    storage_message.messages.append({"message_id": user_telegram.message_id})
    storage.redis_storage.delete_keys_by_pattern(pattern=f"{cache_key}*")
    storage.redis_storage.set(cache_key=cache_key, cached=storage_message.dict())


def delete_messages(
    bot: TeleBot,
    user_telegram: TelegramUser,
    storage: StorageAPI,
    type_message: Literal["system", "education", "quiz"],
):
    cache_key = f"user_telegram_id:{user_telegram.id}:type_message:{type_message}"
    storage_message = storage.redis_storage.get(
        base_model=MessageStorageSchema, cache_key=cache_key
    )
    if storage_message is None:
        return

    for message in storage_message.messages:
        try:
            bot.delete_message(
                chat_id=user_telegram.chat_id, message_id=message["message_id"]
            )
        except Exception as e:
            print(e)
    storage.redis_storage.delete_keys_by_pattern(pattern=f"{cache_key}*")


def spoiler_message(
    bot: TeleBot,
    user_telegram: TelegramUser,
    storage: StorageAPI,
    action: str = Literal["set", "pull off"],
    type_message: str = "education",
):
    cache_key = f"user_telegram_id:{user_telegram.id}:type_message:{type_message}"
    storage_message = storage.redis_storage.get(
        base_model=MessageStorageSchema, cache_key=cache_key
    )
    if storage_message is None:
        return
    for message in storage_message.messages:
        try:
            if action == "set":
                text = f'<span class="tg-spoiler">{message["text"]}</span>'
            elif action == "pull off":
                text = re.sub(r'<span class="tg-spoiler">', "", message["text"], 1)
                text = re.sub(r"</span>(?!.*</span>)", "", text)

            bot.edit_message_text(
                message_id=message["message_id"],
                text=text,
                parse_mode="HTML",
                chat_id=user_telegram.chat_id,
            )
        except Exception as e:
            print(e)
    if action == "pull off":
        storage.redis_storage.delete_keys_by_pattern(pattern=f"{cache_key}*")
