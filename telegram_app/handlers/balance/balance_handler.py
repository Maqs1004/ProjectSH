from telebot import TeleBot
from api.client import StorageAPI
from handlers.balance.balance_command import balance_command_handler
from handlers.utils import Commands
from telebot.types import Message


class BalanceHandler:
    """
    Класс для обработки команды /balance.

    Этот класс регистрирует обработчик команды /balance и связывает его
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
        Регистрирует обработчики событий для команды /balance.

        Метод связывает команду /balance с функцией-обработчиком.
        """

        @self.bot.message_handler(commands=[Commands.balance.value])
        def handle_balance(message: Message):
            balance_command_handler(message=message, bot=self.bot, storage=self.storage)
