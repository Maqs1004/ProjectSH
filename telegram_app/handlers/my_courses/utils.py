from typing import Literal

from telebot import TeleBot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from api.client import StorageAPI
from handlers.dependencies import handler_message, TelegramUser
from handlers.utils import Buttons, TranslationKeys, Commands
from schemas.course_schemas import PaginatedUserCoursesSchema, CurrentStage


def show_list_courses(
    courses: PaginatedUserCoursesSchema,
    bot: TeleBot,
    storage: StorageAPI,
    user_telegram: TelegramUser,
    callback_data: str,
):
    """
    Отображает список курсов пользователю.

    Создает кнопки для каждого курса и навигационные кнопки для перехода между страницами списка курсов.

    Args:
        courses (PaginatedUserCoursesSchema): Объект с информацией о курсах и пагинации
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        callback_data (str): Данные callback для навигационных кнопок
    """
    buttons = []
    for user_course in courses.data:
        buttons.append(
            InlineKeyboardButton(
                text=user_course.title,
                callback_data=f"{Buttons.show_user_course_info.callback}_{user_course.id}",
            )
        )

    markup = InlineKeyboardMarkup()
    markup.add(*buttons, row_width=1)
    navigation_menu = []
    if courses.total_records > (courses.page * courses.page_size):
        navigation_menu.append(
            InlineKeyboardButton(
                text=">>",
                callback_data=f"{callback_data}_{courses.page + 1}",
            )
        )
    if courses.page > 1:
        navigation_menu.append(
            InlineKeyboardButton(
                text="<<",
                callback_data=f"{callback_data}_{courses.page - 1}",
            )
        )
    back = storage.get_translation(
        message_key=Buttons.back_button.text,
        language_code=user_telegram.language,
    )
    navigation_menu.append(
        InlineKeyboardButton(
            text=back.message_text,
            callback_data=f"{Commands.my_courses.value}",
        )
    )
    markup.add(*navigation_menu, row_width=2)
    select_course = storage.get_translation(
        message_key=TranslationKeys.select_course_message,
        language_code=user_telegram.language,
    )
    handler_message(
        bot=bot,
        text=select_course.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=user_telegram.message_id,
        markup=markup,
    )


def show_user_course(
    bot: TeleBot,
    storage: StorageAPI,
    call: CallbackQuery,
    user_course_id: str,
    updated_text: str | None = None,
    status: Literal["resume", "restart", "pause"] | None = None,
):
    """
    Отображает информацию о курсе пользователя.

    В зависимости от статуса курса формирует соответствующее сообщение и кнопки для действий с курсом.

    Args:
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        call (CallbackQuery): Запрос обратного вызова от пользователя
        user_course_id (str): Идентификатор курса пользователя
        updated_text (str | None): Текст с обновлением курса
        status (Literal["resume", "restart", "pause"] | None): Статус курса.
    """
    user_telegram = TelegramUser(message=call)
    user_course = storage.get_user_course_info(user_course_id=user_course_id)
    buttons = []
    if user_course.active:
        if user_course.current_stage == CurrentStage.not_generated:
            text = user_course.title
            prepare_material = storage.get_translation(
                message_key=Buttons.prepare_material.text,
                language_code=user_telegram.language,
            )
            buttons.append(
                InlineKeyboardButton(
                    text=prepare_material.message_text,
                    callback_data=f"{Buttons.prepare_material.callback}_{user_course.id}",
                )
            )
        elif user_course.current_stage == CurrentStage.generating:
            preparing_material = storage.get_translation(
                message_key=TranslationKeys.preparing_material_message,
                language_code=user_telegram.language,
            )
            text = preparing_material.message_text
        else:
            text = user_course.title
            pause_course = storage.get_translation(
                message_key=Buttons.pause_course.text,
                language_code=user_telegram.language,
            )
            if status == "resume":
                continue_button = storage.get_translation(
                    message_key=Buttons.continue_button.text,
                    language_code=user_telegram.language,
                )
                buttons.append(
                    InlineKeyboardButton(
                        text=continue_button.message_text,
                        callback_data=f"{Buttons.resume_education.callback}_{user_course_id}",
                    )
                )
            elif status == "restart":
                start_education_button = storage.get_translation(
                    message_key=Buttons.start_education.text,
                    language_code=user_telegram.language,
                )
                buttons.append(
                    InlineKeyboardButton(
                        text=start_education_button.message_text,
                        callback_data=f"{Buttons.start_education.callback}_{user_course_id}",
                    )
                )
            buttons.append(
                InlineKeyboardButton(
                    text=pause_course.message_text,
                    callback_data=f"{Buttons.pause_course.callback}_{user_course.id}",
                )
            )
    if user_course.finished and user_course.archived:
        text = user_course.title
        restart_course = storage.get_translation(
            message_key=Buttons.restart_course.text,
            language_code=user_telegram.language,
        )
        buttons.append(
            InlineKeyboardButton(
                text=restart_course.message_text,
                callback_data=f"{Buttons.restart_course.callback}_{user_course.id}",
            )
        )
    if not any([user_course.active, user_course.archived, user_course.finished]):
        text = user_course.title
        resume_course = storage.get_translation(
            message_key=Buttons.resume_course.text,
            language_code=user_telegram.language,
        )
        buttons.append(
            InlineKeyboardButton(
                text=resume_course.message_text,
                callback_data=f"{Buttons.resume_course.callback}_{user_course.id}",
            )
        )
    back = storage.get_translation(
        message_key=Buttons.back_button.text,
        language_code=user_telegram.language,
    )
    buttons.append(
        InlineKeyboardButton(
            text=back.message_text,
            callback_data=f"{Commands.my_courses.value}",
        )
    )
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(*buttons)
    text = updated_text if updated_text else text
    handler_message(
        bot=bot,
        text=text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=user_telegram.message_id,
        markup=markup,
    )


def change_status_handler(
    call: Message | CallbackQuery,
    bot: TeleBot,
    storage: StorageAPI,
    user_course_id: str,
    status: Literal["resume", "restart", "pause"],
):
    """
    Обрабатывает изменение статуса курса пользователя.

    В зависимости от нового статуса курса обновляет статус и формирует соответствующее
    сообщение и кнопки для действий с курсом.

    Args:
        call (Message | CallbackQuery): Сообщение или запрос обратного вызова от пользователя.
        bot (TeleBot): Экземпляр Telegram бота.
        storage (StorageAPI): Экземпляр для работы с хранилищем данных.
        user_course_id (str): Идентификатор курса пользователя.
        status (Literal["resume", "restart", "pause"]): Новый статус курса.
    """
    user_telegram = TelegramUser(message=call)
    active_user_course = storage.get_active_user_course(user_telegram=user_telegram)
    if active_user_course:
        storage.set_course_status(user_course_id=active_user_course.id, status="pause")
    user_course = storage.set_course_status(
        user_course_id=user_course_id, status=status
    )

    change_status = storage.get_translation(
        message_key=getattr(TranslationKeys, f"course_{status}_message"),
        language_code=user_telegram.language,
    )

    show_user_course(
        bot=bot,
        storage=storage,
        call=call,
        user_course_id=user_course.id,
        updated_text=change_status.message_text.format(title=user_course.title),
        status=status,
    )
