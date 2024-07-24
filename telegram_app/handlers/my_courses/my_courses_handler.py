from telebot import TeleBot
from api.client import StorageAPI
from handlers.my_courses.my_courses_command import my_courses_command_handler
from handlers.my_courses.courses import archived_handler, unfinished_handler
from handlers.my_courses.utils import show_user_course, change_status_handler
from handlers.utils import Commands, Buttons
from telebot.types import Message, CallbackQuery


class MyCoursesHandler:
    """
    Класс для обработки команды /my_courses.

    Этот класс регистрирует обработчик команды /my_courses и связывает его
    с функцией-обработчиком.

    Attributes:
        bot (TeleBot): Экземпляр бота
        storage (StorageAPI): Экземпляр для работы с API и хранилищем данных
    """

    def __init__(self, bot: TeleBot, storage: StorageAPI):
        self.bot = bot
        self.storage = storage
        self.register_handlers()

    def register_handlers(self):
        """
        Регистрирует обработчики событий для команды /my_courses.

        Метод связывает команду /my_courses с функцией-обработчиком.
        """

        @self.bot.message_handler(commands=[Commands.my_courses.value])
        def handle_my_courses(message: Message):
            my_courses_command_handler(
                message=message, bot=self.bot, storage=self.storage
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.archived_courses.callback)
        )
        def handle_archived_courses(call: CallbackQuery):
            page = call.data.split(f"{Buttons.archived_courses.callback}_")[1]
            archived_handler(call=call, bot=self.bot, storage=self.storage, page=page)

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.unfinished_courses.callback)
        )
        def handle_unfinished_courses(call: CallbackQuery):
            page = call.data.split(f"{Buttons.unfinished_courses.callback}_")[1]
            unfinished_handler(call=call, bot=self.bot, storage=self.storage, page=page)

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(
                Buttons.show_user_course_info.callback
            )
        )
        def handle_show_user_course_info(call: CallbackQuery):
            user_course_id = call.data.split(
                f"{Buttons.show_user_course_info.callback}_"
            )[1]
            show_user_course(
                call=call,
                bot=self.bot,
                storage=self.storage,
                user_course_id=user_course_id,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Commands.my_courses.value
        )
        def handle_my_courses_call(call: CallbackQuery):
            my_courses_command_handler(
                message=call, bot=self.bot, storage=self.storage, actin="edit"
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.pause_course.callback)
        )
        def handle_pause_course(call: CallbackQuery):
            user_course_id = call.data.split(f"{Buttons.pause_course.callback}_")[1]
            change_status_handler(
                call=call,
                bot=self.bot,
                storage=self.storage,
                status="pause",
                user_course_id=user_course_id,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.restart_course.callback)
        )
        def handle_restart_course(call: CallbackQuery):
            user_course_id = call.data.split(f"{Buttons.restart_course.callback}_")[1]
            change_status_handler(
                call=call,
                bot=self.bot,
                storage=self.storage,
                status="restart",
                user_course_id=user_course_id,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.resume_course.callback)
        )
        def handle_resume_course(call: CallbackQuery):
            user_course_id = call.data.split(f"{Buttons.resume_course.callback}_")[1]
            change_status_handler(
                call=call,
                bot=self.bot,
                storage=self.storage,
                status="resume",
                user_course_id=user_course_id,
            )
