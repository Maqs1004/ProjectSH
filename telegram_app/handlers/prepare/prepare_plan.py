from telebot import TeleBot
from api.client import StorageAPI
from handlers.prepare.utils import check_expired_prepare, send_or_edit
from handlers.utils import TranslationKeys, Buttons
from handlers.dependencies import TelegramUser, format_plan_to_markdown, handler_message
from telebot.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def preparing_plan(call: Message | CallbackQuery, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает этап подготовки плана курса.

    Проверяет актуальность информации о подготовке, создаёт курс, добавляет пользователя к курсу
    и отправляет пользователю сообщение с планом курса.

    Args:
        call (Message | CallbackQuery): Сообщение или запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=call)
    created_info = check_expired_prepare(
        user_telegram=user_telegram, bot=bot, storage=storage
    )
    if created_info is None:
        return
    message = send_or_edit(
        storage=storage,
        message_key=TranslationKeys.creating_plan_message,
        user_telegram=user_telegram,
        call=call,
        bot=bot,
    )
    created_course = storage.create_course(extra_info=created_info.extra_info.dict())
    user_course = storage.add_course_user(
        user_telegram_id=user_telegram.id,
        course_id=created_course.course_id,
        current_stage="not_generated",
    )
    your_training_plan = storage.get_translation(
        message_key=TranslationKeys.your_training_plan_message,
        language_code=user_telegram.language,
    )
    plan = format_plan_to_markdown(
        plan=created_course.plan, your_training_plan=your_training_plan.message_text
    )
    prepare_material_button = storage.get_translation(
        message_key=Buttons.prepare_material.text,
        language_code=user_telegram.language,
    )
    markup = InlineKeyboardMarkup(row_width=1)
    btn_prepare_material = InlineKeyboardButton(
        text=prepare_material_button.message_text,
        callback_data=f"{Buttons.prepare_material.callback}_{user_course.id}",
    )
    markup.add(btn_prepare_material)
    process_withdraw(user_telegram=user_telegram, storage=storage)
    handler_message(
        bot=bot,
        text=plan,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=message.message_id,
        parse_mode="HTML",
        markup=markup,
    )


def process_withdraw(
    user_telegram: TelegramUser,
    storage: StorageAPI,
):
    """
    Обрабатывает списание курса.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    storage.change_quantity_user_course(
        telegram_id=user_telegram.id, action="withdraw", count_course=1
    )
