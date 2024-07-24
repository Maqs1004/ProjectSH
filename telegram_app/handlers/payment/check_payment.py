from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message
from handlers.prepare.prepare_title import preparing_title
from handlers.prepare.utils import check_expired_prepare
from handlers.utils import TranslationKeys, Buttons
from schemas.create_education_schemas import Stages


def payment_check(call: CallbackQuery, bot: TeleBot, storage: StorageAPI):
    """
    Проверяет баланс пользователя и обрабатывает этап оплаты.

    Если баланс пользователя недостаточен, вызывается функция обработки недостатка средств.
    В противном случае устанавливается стадия "оплата подтверждена" и начинается подготовка к созданию курса.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=call)
    user_balance = storage.get_user_balance(telegram_id=user_telegram.id)

    if user_balance.count_course == 0:
        insufficient_funds(user_telegram=user_telegram, storage=storage, bot=bot)
    else:
        created_info = check_expired_prepare(
            user_telegram=user_telegram, bot=bot, storage=storage, only_check=True
        )
        if created_info is None:
            extra_info = {
                "language": user_telegram.language,
            }
            storage.set_prepare_stage(
                user_telegram_id=user_telegram.id,
                stage=Stages.payment_verified,
                extra_info=extra_info,
            )
        preparing_title(call=call, bot=bot, storage=storage)
    return


def insufficient_funds(user_telegram: TelegramUser, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает ситуацию недостатка средств у пользователя.

    Отправляет пользователю сообщение о недостатке средств и предлагает варианты оплаты
    или ввода промокода.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    insufficient_fund = storage.get_translation(
        message_key=TranslationKeys.insufficient_funds_message,
        language_code=user_telegram.language,
    )
    markup = show_promo_pay_button(storage=storage, user_telegram=user_telegram)
    handler_message(
        bot=bot,
        text=insufficient_fund.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=user_telegram.message_id,
        markup=markup,
    )


def show_promo_pay_button(storage: StorageAPI, user_telegram: TelegramUser):
    markup = InlineKeyboardMarkup(row_width=1)
    pay_button = storage.get_translation(
        message_key=Buttons.full_pay.text, language_code=user_telegram.language
    )
    payment_btn = InlineKeyboardButton(
        text=pay_button.message_text, callback_data=Buttons.full_pay.callback
    )
    promo_code_button = storage.get_translation(
        message_key=Buttons.promo_code.text, language_code=user_telegram.language
    )
    promo_code_btn = InlineKeyboardButton(
        text=promo_code_button.message_text,
        callback_data=Buttons.promo_code.callback,
    )
    telegram_stars_btn = InlineKeyboardButton(
        text="Telegram Stars⭐",
        callback_data=Buttons.telegram_stars.callback,
    )
    markup.add(payment_btn, promo_code_btn, telegram_stars_btn)
    return markup
