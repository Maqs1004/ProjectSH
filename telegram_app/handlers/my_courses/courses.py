from telebot import TeleBot
from telebot.types import CallbackQuery
from api.client import StorageAPI
from handlers.dependencies import TelegramUser
from handlers.my_courses.utils import show_list_courses
from handlers.utils import Buttons


def archived_handler(call: CallbackQuery, bot: TeleBot, storage: StorageAPI, page: str):
    """
    Обрабатывает запрос на получение списка архивных курсов пользователя.

    Получает архивные курсы и отображает их пользователю.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        page (str): Номер страницы для пагинации
    """
    user_telegram = TelegramUser(message=call)
    archived_courses = storage.get_archived_user_courses(
        user_telegram=user_telegram, page=page
    )
    show_list_courses(
        courses=archived_courses,
        bot=bot,
        storage=storage,
        user_telegram=user_telegram,
        callback_data=Buttons.archived_courses.callback,
    )


def unfinished_handler(
    call: CallbackQuery, bot: TeleBot, storage: StorageAPI, page: str
):
    """
    Обрабатывает запрос на получение списка незавершенных курсов пользователя.

    Получает незавершенные курсы и отображает их пользователю.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        page (str): Номер страницы для пагинации
    """
    user_telegram = TelegramUser(message=call)
    unfinished_courses = storage.get_unfinished_user_courses(
        user_telegram=user_telegram, page=page
    )
    show_list_courses(
        courses=unfinished_courses,
        bot=bot,
        storage=storage,
        user_telegram=user_telegram,
        callback_data=Buttons.unfinished_courses.callback,
    )
