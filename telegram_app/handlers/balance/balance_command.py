from telebot import TeleBot
from telebot.types import Message
from api.client import StorageAPI
from handlers.dependencies import (
    TelegramUser,
    delete_messages,
    append_user_message,
    handler_message,
)
from handlers.payment.check_payment import show_promo_pay_button
from handlers.start.start_command import add_user
from handlers.utils import (
    TranslationKeys,
)


def balance_command_handler(message: Message, bot: TeleBot, storage: StorageAPI):
    """
    Обработчик команды /balance в Telegram боте.

    Эта функция обрабатывает команду /balance, и отображает пользователю количество доступных курсов

    Args:
        message (Message): Сообщение от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=message)
    delete_messages(
        bot=bot, storage=storage, type_message="system", user_telegram=user_telegram
    )
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="system"
    )
    try:
        user = storage.get_user(user_telegram=user_telegram)
        if user:
            balance = storage.get_user_balance(telegram_id=user_telegram.id)
            available_courses = storage.get_translation(
                message_key=TranslationKeys.available_courses_message,
                language_code=user_telegram.language,
            )
            markup = None
            if balance.count_course == 0:
                markup = show_promo_pay_button(
                    storage=storage, user_telegram=user_telegram
                )
            handler_message(
                bot=bot,
                text=available_courses.message_text.format(
                    count_course=balance.count_course
                ),
                chat_id=user_telegram.chat_id,
                user_telegram=user_telegram,
                storage=storage,
                type_message="system",
                actin="send",
                markup=markup,
            )
        else:
            add_user(user_telegram=user_telegram, storage=storage, bot=bot)
    except Exception as e:
        handler_message(
            bot=bot,
            text="Error communicating with the external service., {}".format(e),
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
        )
