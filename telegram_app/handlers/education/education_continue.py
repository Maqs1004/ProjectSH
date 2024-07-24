from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message
from handlers.utils import TranslationKeys, Buttons
from schemas.course_schemas import CurrentStage, UserCoursesSchema


def continue_education(
    user_course: UserCoursesSchema,
    user_telegram: TelegramUser,
    bot: TeleBot,
    storage: StorageAPI,
):
    """
    Продолжает обучение для пользователя на основе текущего этапа курса.

    Отправляет пользователю сообщение с соответствующей кнопкой для продолжения курса.

    Args:
        user_course (UserCoursesSchema): Объект с информацией о курсе пользователя
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    if user_course.current_stage == CurrentStage.not_generated:
        education_btn(
            user_telegram=user_telegram,
            message_key=TranslationKeys.not_generated_course_message,
            button_key=Buttons.prepare_material.text,
            callback_data=f"{Buttons.prepare_material.callback}_{user_course.id}",
            course_title=user_course.title,
            bot=bot,
            storage=storage,
        )
    elif user_course.current_stage == CurrentStage.generated:
        education_btn(
            user_telegram=user_telegram,
            message_key=TranslationKeys.material_prepared_message,
            button_key=Buttons.start_education.text,
            callback_data=f"{Buttons.start_education.callback}_{user_course.id}",
            course_title=user_course.title,
            bot=bot,
            storage=storage,
        )
    elif user_course.current_stage == CurrentStage.education:
        education_btn(
            user_telegram=user_telegram,
            message_key=TranslationKeys.unfinished_course_message,
            button_key=Buttons.continue_button.text,
            callback_data=f"{Buttons.resume_education.callback}_{user_course.id}",
            course_title=user_course.title,
            bot=bot,
            storage=storage,
            start_new_btn=True,
        )

    elif user_course.current_stage == CurrentStage.generating:
        education_btn(
            user_telegram=user_telegram,
            message_key=TranslationKeys.preparing_material_message,
            course_title=user_course.title,
            bot=bot,
            storage=storage,
        )
    elif user_course.current_stage in [
        CurrentStage.ask_question,
        CurrentStage.question,
    ]:
        education_btn(
            user_telegram=user_telegram,
            message_key=TranslationKeys.unfinished_course_message,
            button_key=Buttons.continue_button.text,
            callback_data=f"{Buttons.answer_question.callback}_{user_course.id}",
            course_title=user_course.title,
            bot=bot,
            storage=storage,
            start_new_btn=True,
        )


def education_btn(
    user_telegram: TelegramUser,
    message_key: str,
    course_title,
    bot: TeleBot,
    storage: StorageAPI,
    start_new_btn: bool = False,
    callback_data: str | None = None,
    button_key: str | None = None,
):
    """
    Отправляет сообщение с кнопками для продолжения или начала нового обучения.

    Формирует сообщение и клавиатуру с кнопками на основе текущего этапа курса и отправляет их пользователю.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.
        message_key (str): Ключ сообщения для получения перевода.
        course_title (str): Название курса.
        bot (TeleBot): Экземпляр Telegram бота.
        storage (StorageAPI): Экземпляр для работы с хранилищем данных.
        start_new_btn (bool): Флаг, указывающий, нужно ли добавлять кнопку для начала нового обучения
         (по умолчанию False).
        callback_data (Optional[str]): Данные callback для кнопки (по умолчанию None).
        button_key (Optional[str]): Ключ кнопки для получения перевода (по умолчанию None).
    """
    message_template = storage.get_translation(
        message_key=message_key, language_code=user_telegram.language
    )
    message_text = message_template.message_text.format(course_title=course_title)
    markup = None
    if button_key:
        button_template = storage.get_translation(
            message_key=button_key, language_code=user_telegram.language
        )
        markup = InlineKeyboardMarkup(row_width=1)
        btn_not_started_education = InlineKeyboardButton(
            text=button_template.message_text, callback_data=callback_data
        )
        markup.add(btn_not_started_education)
    if start_new_btn and button_key:
        button_new_education = storage.get_translation(
            message_key=Buttons.start_new_education.text,
            language_code=user_telegram.language,
        )
        btn_new_education = InlineKeyboardButton(
            text=button_new_education.message_text,
            callback_data=Buttons.check_payment.callback,
        )
        markup.add(btn_new_education)
    handler_message(
        bot=bot,
        text=message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
        markup=markup,
    )
