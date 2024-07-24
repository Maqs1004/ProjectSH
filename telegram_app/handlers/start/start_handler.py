from telebot import TeleBot
from api.client import StorageAPI
from handlers.start.start_command import start_command_handler
from handlers.utils import Commands
from telebot.types import Message


class StartHandler:
    """
    Класс для обработки команды /start.

    Этот класс регистрирует обработчик команды /start и связывает его
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
        Регистрирует обработчики событий для команды /start.

        Метод связывает команду /start с функцией-обработчиком.
        """

        @self.bot.message_handler(commands=[Commands.start.value])
        def handle_start(message: Message):
            start_command_handler(message=message, bot=self.bot, storage=self.storage)
