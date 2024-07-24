import json

from telebot import TeleBot
from api.client import StorageAPI
from core.config import setting
from handlers.dependencies import TelegramUser
from handlers.payment.pay_process import (
    full_pay_process,
    handle_post_payment,
    get_full_amount,
    confirm_pay_message,
)
from handlers.utils import Buttons, TranslationKeys
from telebot.types import Message, CallbackQuery, PreCheckoutQuery
from handlers.payment.check_payment import payment_check
from handlers.payment.check_promo_code import promo_code_check


class PymentHandler:
    """
    Класс для обработки платежных операций и ввода промокодов в Telegram боте.

    Этот класс регистрирует обработчики для различных платежных операций,
    таких как проверка платежа и ввод промокода.

    Атрибуты:
        bot (TeleBot): Экземпляр бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """

    def __init__(self, bot: TeleBot, storage: StorageAPI):
        self.bot = bot
        self.storage = storage
        self.register_handlers()

    def register_handlers(self):
        """
        Регистрирует обработчики событий для платежных операций.

        Метод связывает платежные операции с соответствующими функциями-обработчиками.
        """

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Buttons.check_payment.callback
        )
        def handle_payment(call: CallbackQuery | Message):
            payment_check(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Buttons.promo_code.callback
        )
        def handle_promo_code(call: CallbackQuery | Message):
            promo_code_check(call=call, bot=self.bot, storage=self.storage)

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Buttons.full_pay.callback
        )
        def handle_pay(call: CallbackQuery | Message):
            user_telegram = TelegramUser(call)
            full_pay_process(
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
                amount=setting.AMOUNT,
                discount=setting.DISCOUNT,
                currency=setting.CURRENCY,
                callback_data=Buttons.confirm_pay.callback,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(Buttons.confirm_pay.callback)
        )
        def handle_confirm_pay(call: CallbackQuery | Message):
            user_telegram = TelegramUser(call)
            get_full_amount(
                call=call,
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
                amount=setting.AMOUNT,
                discount=setting.DISCOUNT,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data == Buttons.telegram_stars.callback
        )
        def handle_make_payment_star(call: CallbackQuery | Message):
            user_telegram = TelegramUser(call)
            full_pay_process(
                bot=self.bot,
                storage=self.storage,
                user_telegram=user_telegram,
                amount=setting.AMOUNT_STARS,
                discount=setting.DISCOUNT_STARS,
                currency="⭐",
                callback_data=Buttons.pay_by_telegram_stars.callback,
            )

        @self.bot.callback_query_handler(
            func=lambda call: call.data.startswith(
                Buttons.pay_by_telegram_stars.callback
            )
        )
        def handle_pay_by_telegram_stars(call: CallbackQuery | Message):
            user_telegram = TelegramUser(message=call)
            count_courses = int(
                call.data.split(f"{Buttons.pay_by_telegram_stars.callback}_")[1]
            )
            full_amount = setting.AMOUNT_STARS * count_courses - (
                setting.DISCOUNT_STARS if count_courses > 1 else 0
            )
            confirm_pay_message(
                user_telegram=user_telegram,
                bot=self.bot,
                storage=self.storage,
                full_amount=full_amount,
                count_courses=count_courses,
                edit_message=True,
                currency="XTR",
                provider_token="",
                factor=1,
            )

        @self.bot.pre_checkout_query_handler(func=lambda query: True)
        def pre_checkout_query(checkout_query: PreCheckoutQuery):
            count_courses = json.loads(checkout_query.invoice_payload)["count_courses"]
            ok = self.storage.change_quantity_user_course(
                telegram_id=checkout_query.from_user.id,
                count_course=count_courses,
                action="deposit",
            )
            if ok:
                self.bot.answer_pre_checkout_query(checkout_query.id, ok=ok)
                return

            # TODO: Добавить сообщение об ошибке
            self.bot.answer_pre_checkout_query(
                checkout_query.id, ok=ok, error_message="error_message"
            )

        @self.bot.message_handler(content_types=["successful_payment"])
        def successful_payment(message):
            user_telegram = TelegramUser(message=message)
            self.storage.add_invoices(user_telegram=user_telegram)
            handle_post_payment(
                storage=self.storage,
                bot=self.bot,
                user_telegram=user_telegram,
                message_key=TranslationKeys.payment_success_message
            )
