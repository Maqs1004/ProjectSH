from telebot import TeleBot
from api.client import StorageAPI
from handlers.utils import Buttons
from handlers.dependencies import (
    TelegramUser,
    handler_message,
    update_prepare_info,
    append_user_message,
)
from handlers.utils import TranslationKeys
from handlers.prepare.utils import check_expired_prepare, try_again
from handlers.prepare.prepare_plan import preparing_plan
from telebot.types import CallbackQuery, Message

from schemas.create_education_schemas import Stages


def preparing_questions(call: CallbackQuery, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает этап подготовки вопросов для курса.

    Проверяет актуальность информации о подготовке, запрашивает вопросы для уточнения курса,
    обновляет информацию о подготовке и отправляет пользователю сообщение о готовности вопросов.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=call)
    created_info = check_expired_prepare(
        user_telegram=user_telegram, bot=bot, storage=storage
    )
    if created_info is None:
        return
    message = None
    if not created_info.extra_info.questions:
        preparing_question = storage.get_translation(
            message_key=TranslationKeys.preparing_questions_message,
            language_code=user_telegram.language,
        )
        message = handler_message(
            bot=bot,
            text=preparing_question.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=user_telegram.message_id,
        )
        question = storage.get_preparing_questions(
            course_title=created_info.extra_info.title, language=user_telegram.language
        )
        questions = dict.fromkeys(question.questions)
        created_info.extra_info.questions = questions
        update_prepare_info(
            user_telegram=user_telegram,
            created_info=created_info,
            storage=storage,
            new_stage=Stages.clarifying_questions,
        )
    message_id = message.message_id if message is not None else user_telegram.message_id
    questions_ready = storage.get_translation(
        message_key=TranslationKeys.questions_ready_message,
        language_code=user_telegram.language,
    )
    handler_message(
        bot=bot,
        text=questions_ready.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=message_id,
    )
    ask_next_question(user_message=call, bot=bot, storage=storage)
    return


def ask_next_question(
    user_message: Message | CallbackQuery, bot: TeleBot, storage: StorageAPI
):
    """
    Запрашивает у пользователя следующий вопрос для курса.

    Проверяет актуальность информации о подготовке, отправляет пользователю следующий вопрос
    и регистрирует обработчик ответа. Если все вопросы заданы, проверяет ответы и формирует краткий пересказ.

    Args:
        user_message (Message | CallbackQuery): Сообщение или запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=user_message)
    created_info = check_expired_prepare(
        user_telegram=user_telegram, bot=bot, storage=storage
    )
    if created_info is None:
        return
    for question, answer in created_info.extra_info.questions.items():
        if answer is None:
            message = handler_message(
                bot=bot,
                text=question,
                chat_id=user_telegram.chat_id,
                user_telegram=user_telegram,
                storage=storage,
                type_message="system",
                actin="send",
            )
            bot.register_next_step_handler(
                message=message,
                callback=process_response,
                question=question,
                bot=bot,
                storage=storage,
            )
            return

    checking_prepare_answers = storage.get_translation(
        message_key=TranslationKeys.checking_prepare_answers_message,
        language_code=user_telegram.language,
    )
    message = handler_message(
        bot=bot,
        text=checking_prepare_answers.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
    )
    summarize = storage.summarize(questions_answer=created_info.extra_info.questions)
    created_info = check_expired_prepare(
        user_telegram=user_telegram, bot=bot, storage=storage
    )
    if created_info is None:
        return
    # TODO: Подумать над валидацией, чет много отбраковывает
    if summarize and summarize.is_validate:
        created_info.extra_info.summary = summarize.summary
        update_prepare_info(
            user_telegram=user_telegram,
            created_info=created_info,
            storage=storage,
            new_stage=Stages.preparing_plan,
        )
        preparing_plan(call=user_message, bot=bot, storage=storage)
    else:
        # TODO: Проверить, как тут отрабатывает, что то с ошибкой есть
        reason, markup, btn = try_again(
            user_telegram=user_telegram,
            message_key=TranslationKeys.validation_failure_message,
            storage=storage,
            callback_data=Buttons.start_new_education.callback,
        )
        created_info.extra_info.questions = dict.fromkeys(
            created_info.extra_info.questions
        )
        update_prepare_info(
            user_telegram=user_telegram,
            created_info=created_info,
            storage=storage,
            new_stage=Stages.clarifying_questions,
        )
        handler_message(
            bot=bot,
            text=reason.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=message.message_id,
            markup=markup,
        )


def process_response(
    message: Message, question: str, bot: TeleBot, storage: StorageAPI
):
    """
    Обрабатывает ответ пользователя на заданный вопрос.

    Сохраняет ответ пользователя в информацию о подготовке, обновляет стадию подготовки и запрашивает следующий вопрос.

    Args:
        message (Message): Сообщение от пользователя с ответом на вопрос
        question (str): Текст вопроса, на который отвечает пользователь
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=message)
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="system"
    )
    created_info = check_expired_prepare(
        user_telegram=user_telegram, bot=bot, storage=storage
    )
    if created_info is None:
        return
    created_info.extra_info.questions[question] = user_telegram.message_text
    update_prepare_info(
        user_telegram=user_telegram,
        created_info=created_info,
        storage=storage,
        new_stage=Stages.clarifying_questions,
    )
    ask_next_question(user_message=message, bot=bot, storage=storage)
    return
