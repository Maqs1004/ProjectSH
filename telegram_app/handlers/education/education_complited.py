from telebot import TeleBot
from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message
from handlers.start.start_new import start_new_education_btn
from handlers.utils import TranslationKeys


def completion_course(
    user_course_id: str, storage: StorageAPI, bot: TeleBot, user_telegram: TelegramUser
):
    """
    Обрабатывает завершение курса для пользователя.

    Архивирует курс, отправляет пользователю сообщение о завершении курса и предлагает начать новый курс.

    Args:
        user_course_id (str): Идентификатор курса пользователя
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        bot (TeleBot): Экземпляр Telegram бота
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
    """
    # TODO: Не убирается спойлер, после пройденных тестов
    user_course = storage.get_user_course_info(user_course_id=user_course_id)
    storage.set_course_status(user_course_id=user_course_id, status="archive")
    course_completion = storage.get_translation(
        message_key=TranslationKeys.course_completion_message,
        language_code=user_telegram.language,
    )

    markup, btn = start_new_education_btn(
        user_telegram=user_telegram,
        storage=storage,
    )
    markup.add(btn)
    handler_message(
        bot=bot,
        text=course_completion.message_text.format(course=user_course.title),
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
        markup=markup,
    )
