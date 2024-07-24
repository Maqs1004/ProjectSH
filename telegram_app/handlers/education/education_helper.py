from telebot import TeleBot
from telebot.types import (
    Message,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from api.client import StorageAPI
from handlers.balance.balance_command import balance_command_handler
from handlers.dependencies import TelegramUser, handler_message, append_user_message
from handlers.education.education_process import next_stage_education
from handlers.education.utils import clean_and_escape_html
from handlers.help.help_command import help_command_handler
from handlers.my_courses.my_courses_command import my_courses_command_handler
from handlers.start.start_command import start_command_handler
from handlers.utils import (
    TranslationKeys,
    Buttons,
    Commands,
)
from schemas.course_schemas import ContentType, ModuleContentsSchema
from schemas.education_schemas import QuestionType


def ask_question(
    user_course_id: str, bot: TeleBot, storage: StorageAPI, user_telegram: TelegramUser
):
    """
    Позволяет задать вопрос пользователю по пройденному курсу материалу.

    Отправляет пользователю инструкцию и регистрирует обработчик для обработки вопроса от пользователя.

    Args:
        user_course_id (str): Идентификатор курса пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
    """
    ask_questions = storage.get_translation(
        message_key=TranslationKeys.ask_questions_message,
        language_code=user_telegram.language,
    )
    markup = ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True, row_width=2
    )

    markup.add(Buttons.skip_button.text)
    msg = handler_message(
        bot=bot,
        text=ask_questions.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="education",
        actin="send",
        markup=markup,
    )
    user_course = storage.get_user_course_info(user_course_id=user_course_id)
    content = storage.get_modul_content(
        sub_module_id=user_course.current_sub_module_id,
        order_number=user_course.current_order_number,
        content_type=ContentType.text.value,
    )
    bot.register_next_step_handler(
        message=msg,
        callback=waiting_question,
        user_course_id=user_course_id,
        bot=bot,
        storage=storage,
        content=content,
        dialog=[],
    )


def waiting_question(
    message: Message,
    user_course_id: str,
    bot: TeleBot,
    storage: StorageAPI,
    content: ModuleContentsSchema,
    dialog: list,
    count: int = 0,
):
    """
    Обрабатывает вопросы пользователя по материалу в рамках курса.

    Проверяет вопрос пользователя, получает на него ответ от LLM и регистрирует следующий шаг. Если достигнут
    предел вопросов, переходит к следующему этапу.

    Args:
        message (Message): Сообщение от пользователя с ответом на вопрос
        user_course_id (str): Идентификатор курса пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        content (ModuleContentsSchema): Содержимое модуля курса
        dialog (list): История диалога пользователя с системой
        count (int): Количество вопросов, заданных пользователю
    """
    user_telegram = TelegramUser(message=message)
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="education"
    )
    if message.text == Buttons.skip_button.text:
        next_stage_education(
            user_telegram=user_telegram,
            bot=bot,
            storage=storage,
            user_course_id=user_course_id,
        )
        return
    if message.text in [f"/{command.value}" for command in Commands]:
        handlers = {
            f"/{Commands.start.value}": start_command_handler,
            f"/{Commands.help.value}": help_command_handler,
            f"/{Commands.balance.value}": balance_command_handler,
            f"/{Commands.my_courses.value}": my_courses_command_handler,
        }
        handlers[message.text](message=message, bot=bot, storage=storage)
        return
    dialog.append(
        {
            "role": "user",
            "content": f"{message.text}. Верни ответ на языке {user_telegram.language}",
        }
    )
    handler_message(
        bot=bot,
        text="🤔",
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
    )
    answer = storage.get_answer(
        content=content.content_data,
        history=dialog,
        language=user_telegram.language,
        user_course_id=user_course_id,
    )
    if answer.is_validate:
        count += 1
        reply_markup = ReplyKeyboardRemove() if count == 3 else None
        msg = handler_message(
            bot=bot,
            text=answer.response,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="education",
            actin="send",
            markup=reply_markup,
        )
        dialog.append({"role": "assistant", "content": answer.response})
        if count == 3:
            limit_reached = storage.get_translation(
                message_key=TranslationKeys.limit_reached_message,
                language_code=user_telegram.language,
            )
            markup = InlineKeyboardMarkup(row_width=5)
            next_stage_btn = InlineKeyboardButton(
                text=Buttons.next_stage.text,
                callback_data=f"{Buttons.next_stage.callback}_{user_course_id}",
            )
            markup.add(next_stage_btn)
            handler_message(
                bot=bot,
                text=limit_reached.message_text,
                chat_id=user_telegram.chat_id,
                user_telegram=user_telegram,
                storage=storage,
                type_message="system",
                actin="send",
                markup=markup,
            )
            return
        bot.register_next_step_handler(
            message=msg,
            callback=waiting_question,
            user_course_id=user_course_id,
            bot=bot,
            storage=storage,
            content=content,
            dialog=dialog,
            count=count,
        )
        return
    dialog.append(
        {"role": "assistant", "content": '{"response": null, "is_validate": false}'}
    )
    count += 1
    if count == 3:
        limit_reached = storage.get_translation(
            message_key=TranslationKeys.limit_reached_message,
            language_code=user_telegram.language,
        )
        handler_message(
            bot=bot,
            text=limit_reached.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="send",
        )
        return
    toxic_warning = storage.get_translation(
        message_key=TranslationKeys.toxic_warning_message,
        language_code=user_telegram.language,
    )
    msg = handler_message(
        bot=bot,
        text=toxic_warning.message_text,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
    )
    bot.register_next_step_handler(
        message=msg,
        callback=waiting_question,
        user_course_id=user_course_id,
        bot=bot,
        storage=storage,
        content=content,
        dialog=dialog,
        count=count,
    )


def sos_answer(
    user_course_id: str, bot: TeleBot, storage: StorageAPI, user_telegram: TelegramUser
):
    handler_message(
        bot=bot,
        text="🤔",
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
    )
    current_education_stage = storage.get_user_course_info(
        user_course_id=user_course_id
    )
    question = storage.get_question_content(
        sub_module_id=current_education_stage.current_sub_module_id,
        order_number=current_education_stage.current_order_number,
    )
    answer = storage.get_user_answer(
        telegram_id=user_telegram.id, question_id=question.id
    )
    if question.question_type == QuestionType.multiple_choice:
        question.content += f"{question.content}\n" + "\n".join(
            f"{index}. {text['option']}"
            for index, text in enumerate(question.options, start=1)
        )
    correct_feedback = storage.get_correct_feedback(
        user_course_id=user_course_id,
        question=question.content,
        answer=answer.answer,
        feedback=answer.feedback,
        language=user_telegram.language,
    )
    next_stage_btn = InlineKeyboardButton(
        text=Buttons.next_stage.text,
        callback_data=f"{Buttons.next_stage.callback}_{user_course_id}",
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(next_stage_btn)
    correct_feedback_html = clean_and_escape_html(correct_feedback.response)
    handler_message(
        bot=bot,
        text=correct_feedback_html,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="send",
        markup=markup,
        parse_mode="HTML",
    )
