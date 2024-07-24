from telebot import TeleBot
from api.client import StorageAPI
from handlers.dependencies import (
    TelegramUser,
    handler_message,
    append_user_message,
    update_prepare_info,
)
from handlers.prepare.utils import check_expired_prepare, send_or_edit
from handlers.utils import TranslationKeys, Buttons
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from handlers.start.start_command import start_command_handler
from schemas.create_education_schemas import Stages


def preparing_title(call: CallbackQuery | Message, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает подготовку ввода название курса. Задает пользователю вопрос и ждет ответ

    Args:
        call (CallbackQuery | Message): Запрос обратного вызова или сообщение от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(call)
    msg = send_or_edit(
        storage=storage,
        message_key=TranslationKeys.input_title_course_message,
        user_telegram=user_telegram,
        call=call,
        bot=bot,
    )
    bot.register_next_step_handler(
        message=msg, callback=input_title_course, bot=bot, storage=storage
    )


def input_title_course(message: Message, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает ввод название курса пользователем.

    Args:
        message (Message): Сообщение от пользователя.
        bot (TeleBot): Экземпляр Telegram бота.
        storage (StorageAPI): Экземпляр для работы с хранилищем данных.
    """
    user_telegram = TelegramUser(message)
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="system"
    )
    if user_telegram.message_text == "/cancel":
        return
    if user_telegram.message_text == "/start":
        start_command_handler(message=message, bot=bot, storage=storage)
        return
    check_course = storage.get_translation(
        message_key=TranslationKeys.check_course_name_message,
        language_code=user_telegram.language,
    )
    message = handler_message(
        bot=bot,
        text=check_course.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
    )
    check_course_title(
        user_telegram=user_telegram, message=message, bot=bot, storage=storage
    )


def check_course_title(
    user_telegram: TelegramUser, message: Message, bot: TeleBot, storage: StorageAPI
):
    """
    Проверяет название курса на корректность и возможность изучения.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        message (Message): Сообщение от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    checked_title = storage.check_title(
        course_title=user_telegram.message_text, language=user_telegram.language
    )
    created_info = check_expired_prepare(
        user_telegram=user_telegram, bot=bot, storage=storage
    )
    if created_info is None:
        return
    if checked_title.allow:
        topic_eligible = storage.get_translation(
            message_key=TranslationKeys.topic_eligible_message,
            language_code=user_telegram.language,
        )
        answer = storage.get_translation(
            message_key=Buttons.preparing_questions.text,
            language_code=user_telegram.language,
        )
        plan = storage.get_translation(
            message_key=Buttons.create_plan.text,
            language_code=user_telegram.language,
        )
        markup = InlineKeyboardMarkup(row_width=1)
        btn_answer = InlineKeyboardButton(
            text=answer.message_text,
            callback_data=Buttons.preparing_questions.callback,
        )
        btn_plan = InlineKeyboardButton(
            text=plan.message_text, callback_data=Buttons.create_plan.callback
        )
        markup.add(btn_answer, btn_plan)
        handler_message(
            bot=bot,
            text=topic_eligible.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=message.message_id,
            markup=markup,
        )
        created_info.extra_info.title = user_telegram.message_text
        update_prepare_info(
            user_telegram=user_telegram,
            created_info=created_info,
            storage=storage,
            new_stage=Stages.input_title,
        )
    else:
        topic_forbidden = storage.get_translation(
            message_key=TranslationKeys.topic_forbidden_message,
            language_code=user_telegram.language,
        )
        forbidden_description = topic_forbidden.format(
            description=checked_title.description
        )
        repeat = storage.get_translation(
            message_key=Buttons.repeat_button.text,
            language_code=user_telegram.language,
        )
        markup = InlineKeyboardMarkup(row_width=1)
        btn_repeat = InlineKeyboardButton(
            text=repeat.message_text,
            callback_data=Buttons.start_new_education.callback,
        )
        markup.add(btn_repeat)
        handler_message(
            bot=bot,
            text=forbidden_description,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
            markup=markup,
        )
