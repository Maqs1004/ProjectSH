import json
import uuid

from telebot import TeleBot
from telebot.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    LabeledPrice,
)

from api.client import StorageAPI
from core.config import setting
from handlers.dependencies import TelegramUser, handler_message
from handlers.start.start_new import start_new_education_btn
from handlers.utils import TranslationKeys, Buttons


def full_pay_process(
    bot: TeleBot,
    storage: StorageAPI,
    amount: int,
    discount: int,
    user_telegram: TelegramUser,
    currency: str,
    callback_data: str,
):
    """
    Обрабатывает процесс полной оплаты для пользователя.

    Создает варианты оплаты с учетом количества курсов и скидки, и отправляет пользователю сообщение с кнопками выбора.

    Args:
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        amount (int): Сумма оплаты за один курс
        discount (int): Скидка на оплату
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        currency (str): Валюта оплаты
        callback_data (str): Данные callback для кнопок оплаты
    """
    payment_options = storage.get_translation(
        message_key=TranslationKeys.payment_options_message,
        language_code=user_telegram.language,
    )
    # TODO: Установить amount и discount в БД
    course_payment_summary_button = storage.get_translation(
        message_key=Buttons.course_payment_summary.text,
        language_code=user_telegram.language,
    )
    markup = InlineKeyboardMarkup(row_width=1)
    for count_courses in range(1, 4, 1):
        full_amount = amount * count_courses - (discount if count_courses > 1 else 0)
        markup.add(
            InlineKeyboardButton(
                text=course_payment_summary_button.message_text.format(
                    count_courses=count_courses, amount=full_amount, currency=currency
                ),
                callback_data=f"{callback_data}_{count_courses}",
            )
        )
    handler_message(
        bot=bot,
        text=payment_options.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=user_telegram.message_id,
        markup=markup,
    )


def get_full_amount(
    call: CallbackQuery,
    bot: TeleBot,
    storage: StorageAPI,
    user_telegram: TelegramUser,
    amount: int,
    discount: int,
):
    """
    Рассчитывает полную сумму оплаты и вызывает функцию подтверждения оплаты.

    В зависимости от количества курсов и скидки рассчитывает итоговую сумму и инициирует процесс подтверждения оплаты.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        amount (int): Сумма оплаты за один курс
        discount (int): Скидка на оплату
    """
    count_courses = int(call.data.split(f"{Buttons.confirm_pay.callback}_")[1])
    full_amount = amount * count_courses - (discount if count_courses > 1 else 0)
    confirm_pay_message(
        user_telegram=user_telegram,
        bot=bot,
        storage=storage,
        full_amount=full_amount,
        count_courses=count_courses,
        edit_message=True,
        currency="RUB",
        provider_token=setting.PROVIDER_TOKEN,
        factor=100,
    )


def discount_pay_process(message: Message, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает процесс оплаты со скидкой для пользователя.

    Рассчитывает сумму со скидкой, отправляет пользователю сообщение с информацией о скидке и
     вызывает функцию подтверждения оплаты.

    Args:
        message (Message): Сообщение от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message)
    prepare_stage = storage.get_prepare_stage(user_telegram_id=user_telegram.id)
    discount_value = prepare_stage.extra_info.promo_info.discount_value
    full_amount = setting.AMOUNT - round(setting.AMOUNT * discount_value / 100, 2)
    if full_amount > 0:
        promo_code_discount = storage.get_translation(
            message_key=TranslationKeys.promo_code_discount_message,
            language_code=user_telegram.language,
        )
        promo_code_discount = promo_code_discount.message_text.format(
            discount_value=discount_value
        )
        handler_message(
            bot=bot,
            text=promo_code_discount,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
        )

        confirm_pay_message(
            user_telegram=user_telegram,
            bot=bot,
            storage=storage,
            full_amount=full_amount,
            count_courses=1,
            edit_message=False,
            currency="RUB",
            provider_token=setting.PROVIDER_TOKEN,
            factor=100,
        )
        return
    storage.change_quantity_user_course(
        telegram_id=user_telegram.id,
        count_course=1,
        action="deposit",
    )
    handle_post_payment(
        user_telegram=user_telegram,
        bot=bot,
        storage=storage,
        message_key=TranslationKeys.promo_code_applied_message,
    )


def confirm_pay_message(
    user_telegram: TelegramUser,
    bot: TeleBot,
    storage: StorageAPI,
    full_amount: float,
    count_courses: int,
    edit_message: bool,
    currency: str,
    provider_token: str,
    factor: int,
):
    """
    Отправляет сообщение с подтверждением оплаты и выставляет счет.

    Формирует сообщение с подтверждением суммы оплаты, отправляет его пользователю,
    а затем выставляет счет с указанной суммой.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        full_amount (float): Итоговая сумма оплаты
        count_courses (int): Количество курсов для оплаты
        edit_message (bool): Флаг, указывающий, нужно ли редактировать сообщение
        currency (str): Валюта оплаты
        provider_token (str): Токен провайдера оплаты
        factor (int): Множитель для расчета суммы в минимальных единицах валюты
    """
    confirm_payment = storage.get_translation(
        message_key=TranslationKeys.confirm_payment_message,
        language_code=user_telegram.language,
    )

    confirm_payment = confirm_payment.message_text.format(
        full_amount=full_amount, currency=currency
    )
    if edit_message:
        handler_message(
            bot=bot,
            text=confirm_payment,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=user_telegram.message_id,
        )
    else:
        handler_message(
            bot=bot,
            text=confirm_payment,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
        )
    course_payment = storage.get_translation(
        message_key=Buttons.course_payment_summary.text,
        language_code=user_telegram.language,
    )
    course_payment = course_payment.message_text.format(
        count_courses=count_courses, amount=full_amount, currency=currency
    )
    prices = [
        LabeledPrice(
            label=course_payment,
            amount=full_amount * factor,
        )
    ]
    bot.send_invoice(
        chat_id=user_telegram.chat_id,
        title=course_payment,
        description=confirm_payment,  # TODO: Добавить полноценное описание
        invoice_payload=json.dumps({"count_courses": count_courses}),
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        start_parameter=str(uuid.uuid4()),
        is_flexible=False,
    )


def handle_post_payment(
    user_telegram: TelegramUser, bot: TeleBot, storage: StorageAPI, message_key: str
):
    """
    Обрабатывает действия после успешной оплаты.

    Добавляет счет, применяет промокод (если есть), отправляет пользователю сообщение
     об успешной оплате и предлагает начать новое обучение.

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        message_key (str): Ключ для текста
    """

    prepare_stage = storage.get_prepare_stage(user_telegram_id=user_telegram.id)
    payment_success = storage.get_translation(
        message_key=message_key,
        language_code=user_telegram.language,
    )
    if prepare_stage and prepare_stage.extra_info.promo_info:
        storage.apply_promo_code(
            telegram_id=user_telegram.id,
            code=prepare_stage.extra_info.promo_info.code,
        )
    markup, btn = start_new_education_btn(user_telegram=user_telegram, storage=storage)
    markup.add(btn)
    handler_message(
        bot=bot,
        text=payment_success.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
        message_id=user_telegram.message_id,
        markup=markup,
    )
