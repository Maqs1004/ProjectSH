from telebot import TeleBot
from telebot.types import CallbackQuery, Message

from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message, append_user_message
from handlers.payment.pay_process import discount_pay_process
from handlers.prepare.utils import try_again
from handlers.utils import TranslationKeys, Buttons
from schemas.create_education_schemas import Stages
from schemas.user_schemas import PromoCode


def promo_code_check(call: CallbackQuery, bot: TeleBot, storage: StorageAPI):
    """
    Запрашивает у пользователя ввод промокода.

    Отправляет пользователю сообщение с запросом на ввод промокода и регистрирует обработчик ввода.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=call)
    enter_promo_code = storage.get_translation(
        message_key=TranslationKeys.enter_promo_code_message,
        language_code=user_telegram.language,
    )
    msg = handler_message(
        bot=bot,
        text=enter_promo_code.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=user_telegram.message_id,
    )
    bot.register_next_step_handler(
        message=msg, callback=check_code, storage=storage, bot=bot
    )


def check_code(message: Message, bot: TeleBot, storage: StorageAPI):
    """
    Проверяет введенный пользователем промокод.

    Отправляет запрос на проверку промокода и обрабатывает ответ сервера. В случае успешной проверки,
    устанавливает стадию "промокод применен". В случае неуспешной проверки, отправляет сообщение о причине ошибки.

    Args:
        message (Message): Сообщение от пользователя с введенным промокодом
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=message)
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="system"
    )
    response = storage.check_promo_code(
        telegram_id=user_telegram.id, promo_code=message.text
    )
    if response.status_code == 200:
        code = PromoCode.model_validate(response.json())
        extra_info = {
            "promo_info": {
                "code": message.text,
                "discount_type": code.discount_type,
                "discount_value": code.discount_value,
                "course_content_volume": code.course_content_volume,
            },
            "language": user_telegram.language,
        }
        storage.redis_storage.delete_keys_by_pattern(
            pattern=f"created_course:user_telegram_id:{user_telegram.id}*"
        )
        storage.set_prepare_stage(
            user_telegram_id=user_telegram.id,
            stage=Stages.apply_promo_code,
            extra_info=extra_info,
        )
        discount_pay_process(message=message, bot=bot, storage=storage)
    elif response.status_code == 409:
        reason, markup, btn = try_again(
            user_telegram=user_telegram,
            message_key=TranslationKeys.promo_code_reuse_message,
            storage=storage,
            callback_data=Buttons.promo_code.callback,
        )
        handler_message(
            bot=bot,
            text=reason.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
            markup=markup,
        )
    elif response.status_code == 404:
        reason, markup, btn = try_again(
            user_telegram=user_telegram,
            message_key=TranslationKeys.promo_code_not_found_message,
            storage=storage,
            callback_data=Buttons.promo_code.callback,
        )
        handler_message(
            bot=bot,
            text=reason.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
            markup=markup,
        )
