from telebot import TeleBot
from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message, delete_messages
from handlers.education.education_helper import ask_question, sos_answer
from handlers.education.education_process import (
    education_start,
    quiz,
    education,
    next_stage_education,
)
from handlers.education.utils import rating_up, rating_down, check_activity
from handlers.utils import Buttons
from telebot.types import CallbackQuery


class EducationHandler:
    """
    Класс для обработки образовательных взаимодействий в Telegram боте.

    Этот класс регистрирует обработчики для различных этапов образовательного процесса,
    таких как начало обучения, переход на следующий этап, продолжение обучения, ответ на вопрос и оценка.

    Attributes:
        bot (TeleBot): Экземпляр бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """

    def __init__(self, bot: TeleBot, storage: StorageAPI):
        self.bot = bot
        self.storage = storage
        self.register_handlers()

    def register_handlers(self):
        """
        Регистрирует обработчики событий для образовательного процесса.

        Метод связывает этапы образовательного процесса с соответствующими функциями-обработчиками.
        """

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.start_education.callback)
        )
        def start_education_handler(call: CallbackQuery):
            education_start(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.next_stage.callback)
        )
        def next_stage_education_handler(call: CallbackQuery):
            user_telegram = TelegramUser(message=call)
            user_course_id = self.preparing_message(
                call=call,
                call_back=Buttons.next_stage.callback,
                user_telegram=user_telegram,
            )
            next_stage_education(
                user_telegram=user_telegram,
                bot=self.bot,
                storage=self.storage,
                user_course_id=user_course_id,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.resume_education.callback)
        )
        def resume_education_handler(call: CallbackQuery):
            user_telegram = TelegramUser(message=call)
            user_course_id = call.data.split(f"{Buttons.resume_education.callback}_")[1]
            delete_messages(
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
                type_message="system",
            )
            education_course = check_activity(
                storage=self.storage,
                bot=self.bot,
                user_telegram=user_telegram,
                user_course_id=user_course_id,
            )
            if education_course:
                education(
                    education_course=education_course,
                    user_telegram=user_telegram,
                    bot=self.bot,
                    storage=self.storage,
                )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.answer_question.callback)
        )
        def answer_handler(call: CallbackQuery):
            user_telegram = TelegramUser(message=call)
            user_course_id = call.data.split(f"{Buttons.answer_question.callback}_")[1]
            delete_messages(
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
                type_message="system",
            )
            quiz(
                user_course_id=user_course_id,
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.rating_up.callback)
        )
        def rating_up_handler(call: CallbackQuery):
            rating_up(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.sos.callback)
        )
        def sos_handler(call: CallbackQuery):
            user_telegram = TelegramUser(message=call)
            user_course_id = self.preparing_message(
                call=call,
                call_back=Buttons.sos.callback,
                user_telegram=user_telegram,
            )
            sos_answer(
                user_course_id=user_course_id,
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.rating_down.callback)
        )
        def rating_down_handler(call: CallbackQuery):
            rating_down(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.ask_question.callback)
        )
        def ask_question_handler(call: CallbackQuery):
            user_telegram = TelegramUser(message=call)
            user_course_id = self.preparing_message(
                call=call,
                call_back=Buttons.ask_question.callback,
                user_telegram=user_telegram,
            )

            ask_question(
                user_course_id=user_course_id,
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
            )

    def preparing_message(
        self, call: CallbackQuery, call_back: str, user_telegram: TelegramUser
    ):
        user_course_id = call.data.split(f"{call_back}_")[1]
        handler_message(
            bot=self.bot,
            text=call.message.text,
            chat_id=call.message.chat.id,
            user_telegram=user_telegram,
            storage=self.storage,
            type_message="system",
            actin="edit",
            message_id=call.message.message_id,
        )
        return user_course_id
