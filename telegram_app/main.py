import logging
import telebot
from api.client import StorageAPI
from core.config import setting
from handlers.balance.balance_handler import BalanceHandler
from handlers.education.education_handler import EducationHandler
from handlers.help.help_handler import HelpHandler
from handlers.my_courses.my_courses_handler import MyCoursesHandler
from handlers.payment.pyment_handler import PymentHandler
from handlers.prepare.prepare_handler import PrepareHandler
from handlers.start.start_handler import StartHandler
from temporary.add_data import add_locales, add_models, add_instructions


class TelegramBot:
    """
    Класс для работы с Telegram ботом.

    Этот класс обеспечивает инициализацию бота, регистрацию обработчиков
    и запуск бота.

    Атрибуты:
        bot (telebot.TeleBot): Экземпляр бота
        storage (StorageAPI): Экземпляр для работы с API и хранилищем данных
    """

    def __init__(self, token: str):
        """
        Инициализирует бота с заданным токеном и регистрирует все обработчики.

        Args:
            - token (str): Токен Telegram бота.
        """
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.DEBUG,  # Уровень DEBUG включает полное логирование
        )

        telebot.logger.setLevel(logging.INFO)
        self.bot = telebot.TeleBot(token, colorful_logs=True)
        self.storage = StorageAPI()
        self.register_all_handlers()

    def register_all_handlers(self):
        """
        Регистрирует все обработчики событий для бота.

        Метод автоматически вызывается при инициализации и связывает
        бота с функциями обработчиками.
        """

        StartHandler(self.bot, self.storage)
        PrepareHandler(self.bot, self.storage)
        PymentHandler(self.bot, self.storage)
        EducationHandler(self.bot, self.storage)
        HelpHandler(self.bot, self.storage)
        BalanceHandler(self.bot, self.storage)
        MyCoursesHandler(self.bot, self.storage)

    def start(self):
        """
        Запускает бота.

        Метод обеспечивает непрерывную работу бота.
        """

        # add_locales(setting.API_URL)
        # add_models(setting.API_URL)
        # add_instructions(setting.API_URL)
        self.bot.infinity_polling(timeout=10, long_polling_timeout=5)


bot = TelegramBot(setting.TELEGRAM_TOKEN)
bot.start()
