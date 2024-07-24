from telebot import TeleBot
from api.client import StorageAPI
from handlers.utils import Buttons
from telebot.types import CallbackQuery, Message
from handlers.prepare.prepare_plan import preparing_plan
from handlers.prepare.prepare_title import preparing_title
from handlers.prepare.prepare_material import preparing_material
from handlers.prepare.prepare_questions import preparing_questions


class PrepareHandler:
    """
    Класс для обработки этапов подготовки курса в Telegram боте.

    Этот класс регистрирует обработчики для различных этапов подготовки курса,
    таких как ввода темы обучения, создание плана, создание вопросов и материалов.

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
        Регистрирует обработчики событий для этапов подготовки курса.

        Метод связывает этапы подготовки курса с соответствующими функциями-обработчиками.
        """

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Buttons.start_new_education.callback
        )
        def handle_prepare(call: CallbackQuery):
            preparing_title(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Buttons.create_plan.callback
        )
        def handle_plan(call: CallbackQuery | Message):
            preparing_plan(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Buttons.preparing_questions.callback
        )
        def handle_preparing_questions(call: CallbackQuery):
            preparing_questions(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.prepare_material.callback)
        )
        def handle_prepare_material(call: CallbackQuery):
            preparing_material(call=call, bot=self.bot, storage=self.storage)
