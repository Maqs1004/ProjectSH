from telebot import TeleBot
from api.client import StorageAPI
from handlers.help.help_command import help_command_handler
from handlers.utils import Commands
from telebot.types import Message


class HelpHandler:
    """
    Класс для обработки команды /help.

    Этот класс регистрирует обработчик команды /help.

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
        Регистрирует обработчики событий для команды /help.

        Метод связывает команду /help с функцией-обработчиком.
        """

        @self.bot.message_handler(commands=[Commands.help.value])
        def handle_help(message: Message):
            help_command_handler(message=message, bot=self.bot, storage=self.storage)
