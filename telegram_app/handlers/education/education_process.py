from telebot import TeleBot
from telebot.types import (
    CallbackQuery,
    ReplyKeyboardMarkup,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from api.client import StorageAPI
from handlers.balance.balance_command import balance_command_handler
from handlers.dependencies import (
    TelegramUser,
    spoiler_message,
    delete_messages,
    handler_message,
    append_user_message,
)
from handlers.education.education_complited import completion_course
from handlers.education.utils import show_content, check_activity
from handlers.help.help_command import help_command_handler
from handlers.my_courses.my_courses_command import my_courses_command_handler
from handlers.start.start_command import start_command_handler
from handlers.utils import (
    Buttons,
    TranslationKeys,
    Commands,
)
from schemas.course_schemas import ContentType, CurrentStage, UserCoursesSchema
from schemas.education_schemas import QuestionType, QuestionsSchema


def education_start(call: CallbackQuery, bot: TeleBot, storage: StorageAPI):
    """
    Начинает процесс обучения для пользователя.

    Проверяет активность курса, обновляет стадию курса и запускает процесс обучения.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_telegram = TelegramUser(message=call)
    user_course_id = call.data.split(f"{Buttons.start_education.callback}_")[1]
    education_course = check_activity(
        storage=storage,
        bot=bot,
        user_telegram=user_telegram,
        user_course_id=user_course_id,
    )
    if education_course:
        storage.patch_user_course_info(
            user_course_id=user_course_id, current_stage=CurrentStage.education.value
        )
        bot.delete_message(
            chat_id=user_telegram.chat_id, message_id=user_telegram.message_id
        )
        education(
            education_course=education_course,
            storage=storage,
            bot=bot,
            user_telegram=user_telegram,
        )


def next_stage_education(
    user_telegram: TelegramUser, bot: TeleBot, storage: StorageAPI, user_course_id: str
):
    """
    Переходит к следующему этапу обучения.

    Проверяет активность курса, получает следующую стадию обучения и обновляет информацию о курсе.
    В зависимости от текущей стадии запускает соответствующий процесс (обучение, вопросы или завершение курса).

    Args:
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        user_course_id (str): Идентификатор курса пользователя
    """
    education_course = check_activity(
        storage=storage,
        bot=bot,
        user_telegram=user_telegram,
        user_course_id=user_course_id,
    )
    if not education_course:
        return
    next_stage = storage.get_next_stage_education(user_course_id=user_course_id)
    if (
        next_stage.data.current_order_number == 1
        and next_stage.stage.value == CurrentStage.education.value
    ):
        delete_messages(
            bot=bot, storage=storage, user_telegram=user_telegram, type_message="quiz"
        )
        spoiler_message(
            bot=bot, storage=storage, user_telegram=user_telegram, action="pull off"
        )
    elif (
        next_stage.data.current_order_number == 1
        and next_stage.stage.value == CurrentStage.question.value
    ):
        spoiler_message(
            bot=bot, storage=storage, user_telegram=user_telegram, action="set"
        )
    education_course = storage.patch_user_course_info(
        user_course_id=user_course_id,
        current_stage=next_stage.stage.value,
        current_module_id=next_stage.data.current_module_id,
        current_order_number=next_stage.data.current_order_number,
        current_sub_module_id=next_stage.data.current_sub_module_id,
    )

    if education_course.current_stage == CurrentStage.education:
        education(
            education_course=education_course,
            storage=storage,
            bot=bot,
            user_telegram=user_telegram,
        )
    elif education_course.current_stage in [
        CurrentStage.question,
        CurrentStage.ask_question,
    ]:
        quiz(
            user_course_id=user_course_id,
            storage=storage,
            bot=bot,
            user_telegram=user_telegram,
        )
    elif education_course.current_stage == CurrentStage.completed:
        completion_course(
            user_course_id=user_course_id,
            storage=storage,
            bot=bot,
            user_telegram=user_telegram,
        )


def education(
    education_course: UserCoursesSchema,
    bot: TeleBot,
    storage: StorageAPI,
    user_telegram: TelegramUser,
):
    """
    Проводит процесс обучения для пользователя.

    Загружает текстовый и визуальный контент текущего модуля и отображает его пользователю.

    Args:
        education_course (UserCoursesSchema): Информация о текущем курсе пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
    """
    text_content = storage.get_modul_content(
        sub_module_id=education_course.current_sub_module_id,
        order_number=education_course.current_order_number,
        content_type=ContentType.text.value,
    )
    image_content = storage.get_modul_content(
        sub_module_id=education_course.current_sub_module_id,
        order_number=education_course.current_order_number,
        content_type=ContentType.image.value,
    )
    show_content(
        text_content=text_content,
        image_content=image_content,
        bot=bot,
        storage=storage,
        user_telegram=user_telegram,
        education_course=education_course,
    )


def quiz(
    user_course_id: str, storage: StorageAPI, bot: TeleBot, user_telegram: TelegramUser
):
    """
    Проводит викторину для пользователя.

    Загружает вопрос текущего модуля и отображает его пользователю в зависимости от типа вопроса.

    Args:
        user_course_id (str): Идентификатор курса пользователя
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        bot (TeleBot): Экземпляр Telegram бота
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
    """
    current_education_stage = storage.get_user_course_info(
        user_course_id=user_course_id
    )
    question = storage.get_question_content(
        sub_module_id=current_education_stage.current_sub_module_id,
        order_number=current_education_stage.current_order_number,
    )
    if question.question_type == QuestionType.multiple_choice:
        ask_multiple_choice_question(
            question=question,
            bot=bot,
            storage=storage,
            user_telegram=user_telegram,
            user_course_id=user_course_id,
        )
    elif question.question_type == QuestionType.open:
        ask_open_question(
            question=question,
            bot=bot,
            storage=storage,
            user_telegram=user_telegram,
            user_course_id=user_course_id,
        )


def ask_multiple_choice_question(
    question: QuestionsSchema,
    bot: TeleBot,
    storage: StorageAPI,
    user_telegram: TelegramUser,
    user_course_id: str,
):
    """
    Задает пользователю вопрос с несколькими вариантами ответа.

    Отправляет пользователю вопрос с вариантами ответа и регистрирует обработчик для обработки ответа пользователя.

    Args:
        question (QuestionsSchema): Объект с информацией о вопросе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        user_course_id (str): Идентификатор курса пользователя
    """
    markup = ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True, row_width=2
    )
    question_text = f"{question.content}\n\n"

    markup.add("1", "2", "3", "4", Buttons.skip_button.text)

    answers = "\n".join(
        f"{index}. {text['option']}"
        for index, text in enumerate(question.options, start=1)
    )
    msg = handler_message(
        bot=bot,
        text=f"{question_text}{answers}",
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="quiz",
        actin="send",
        markup=markup,
    )
    bot.register_next_step_handler(
        message=msg,
        callback=waiting_multiple_choice_question,
        bot=bot,
        question=question,
        storage=storage,
        user_course_id=user_course_id,
    )


def waiting_multiple_choice_question(
    message: Message,
    bot: TeleBot,
    storage: StorageAPI,
    question: QuestionsSchema,
    user_course_id: str,
):
    """
    Обрабатывает ответ пользователя на вопрос с несколькими вариантами ответа.

    Проверяет корректность ответа, сохраняет результат и переходит к следующему этапу обучения.

    Args:
        message (Message): Сообщение от пользователя с ответом на вопрос
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        question (QuestionsSchema): Объект с информацией о вопросе
        user_course_id (str): Идентификатор курса пользователя
    """
    user_telegram = TelegramUser(message=message)
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="quiz"
    )
    if message.text in [f"/{command.value}" for command in Commands]:
        handlers = {
            f"/{Commands.start.value}": start_command_handler,
            f"/{Commands.help.value}": help_command_handler,
            f"/{Commands.balance.value}": balance_command_handler,
            f"/{Commands.my_courses.value}": my_courses_command_handler,
        }
        handlers[message.text](message=message, bot=bot, storage=storage)
        return
    if user_telegram.message_text not in ["1", "2", "3", "4", Buttons.skip_button.text]:
        invalid_option = storage.get_translation(
            message_key=TranslationKeys.invalid_option_message,
            language_code=user_telegram.language,
        )
        markup = ReplyKeyboardMarkup(
            one_time_keyboard=True, resize_keyboard=True, row_width=2
        )
        markup.add("1", "2", "3", "4", Buttons.skip_button.text)
        msg = handler_message(
            bot=bot,
            text=invalid_option.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="quiz",
            actin="send",
            markup=markup,
        )
        bot.register_next_step_handler(
            message=msg,
            callback=waiting_multiple_choice_question,
            bot=bot,
            question=question,
            storage=storage,
            user_course_id=user_course_id,
        )
        return
    storage.patch_user_course_info(
        user_course_id=user_course_id, current_stage=CurrentStage.question.value
    )

    if user_telegram.message_text != Buttons.skip_button.text:
        markup = InlineKeyboardMarkup(row_width=2)
        buttons = []
        if question.options[int(user_telegram.message_text) - 1]["is_correct"]:
            answer_message = storage.get_translation(
                message_key=TranslationKeys.correct_answer_message,
                language_code=user_telegram.language,
            )
            storage.save_answer(
                question_id=question.id,
                answer=user_telegram.message_text,
                score=5,
                telegram_id=user_telegram.id,
            )
            answer_message = answer_message.message_text
        else:
            answer_message = storage.get_translation(
                message_key=TranslationKeys.incorrect_answer_message,
                language_code=user_telegram.language,
            )
            is_correct = next(
                option["option"] for option in question.options if option["is_correct"]
            )
            has_answer = storage.get_user_answer(
                question_id=question.id, telegram_id=user_telegram.id
            )
            answer_message = answer_message.message_text.format(is_correct=is_correct)
            storage.save_answer(
                question_id=question.id,
                answer=question.options[int(user_telegram.message_text) - 1]["option"],
                score=2,
                telegram_id=user_telegram.id,
                feedback=answer_message,
            )

            if not has_answer:
                sos_btn = InlineKeyboardButton(
                    text=Buttons.sos.text,
                    callback_data=f"{Buttons.sos.callback}_{user_course_id}",
                )
                buttons.append(sos_btn)
        next_stage_btn = InlineKeyboardButton(
            text=Buttons.next_stage.text,
            callback_data=f"{Buttons.next_stage.callback}_{user_course_id}",
        )
        buttons.append(next_stage_btn)
        markup.add(*buttons)
        handler_message(
            bot=bot,
            text=answer_message,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="quiz",
            actin="send",
            markup=markup,
        )
        return
    next_stage_education(
        user_telegram=user_telegram,
        bot=bot,
        storage=storage,
        user_course_id=user_course_id,
    )


def ask_open_question(
    question: QuestionsSchema,
    bot: TeleBot,
    storage: StorageAPI,
    user_telegram: TelegramUser,
    user_course_id: str,
):
    """
    Задает пользователю открытый вопрос.

    Отправляет пользователю вопрос и регистрирует обработчик для обработки ответа пользователя.

    Args:
        question (QuestionsSchema): Объект с информацией о вопросе
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе
        user_course_id (str): Идентификатор курса пользователя
    """
    markup = ReplyKeyboardMarkup(
        one_time_keyboard=True, resize_keyboard=True, row_width=2
    )
    markup.add(Buttons.skip_button.text)
    msg = handler_message(
        bot=bot,
        text=f"{question.content}",
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="quiz",
        actin="send",
        markup=markup,
    )
    bot.register_next_step_handler(
        message=msg,
        callback=waiting_open_question,
        bot=bot,
        question=question,
        storage=storage,
        user_course_id=user_course_id,
    )


def waiting_open_question(
    message: Message,
    bot: TeleBot,
    storage: StorageAPI,
    question: QuestionsSchema,
    user_course_id: str,
):
    """
    Обрабатывает ответ пользователя на открытый вопрос.

    Проверяет ответ пользователя, сохраняет результат и переходит к следующему этапу обучения.

    Args:
        message (Message): Сообщение от пользователя с ответом на вопрос
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        question (QuestionsSchema): Объект с информацией о вопросе
        user_course_id (str): Идентификатор курса пользователя
    """
    user_telegram = TelegramUser(message=message)
    append_user_message(
        user_telegram=user_telegram, storage=storage, type_message="quiz"
    )
    storage.patch_user_course_info(
        user_course_id=user_course_id, current_stage=CurrentStage.question.value
    )
    if message.text in [f"/{command.value}" for command in Commands]:
        handlers = {
            f"/{Commands.start.value}": start_command_handler,
            f"/{Commands.help.value}": help_command_handler,
            f"/{Commands.balance.value}": balance_command_handler,
            f"/{Commands.my_courses.value}": my_courses_command_handler,
        }
        handlers[message.text](message=message, bot=bot, storage=storage)
        return
    if user_telegram.message_text != Buttons.skip_button.text:
        buttons = []
        checking_answer = storage.get_translation(
            message_key=TranslationKeys.checking_answer_message,
            language_code=user_telegram.language,
        )
        handler_message(
            bot=bot,
            text=checking_answer.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="quiz",
            actin="send",
        )
        has_answer = storage.get_user_answer(
            question_id=question.id, telegram_id=user_telegram.id
        )
        answer = storage.check_answer(
            question=question.content,
            answer=user_telegram.message_text,
            language=user_telegram.language,
            user_course_id=user_course_id,
        )
        next_stage_btn = InlineKeyboardButton(
            text=Buttons.next_stage.text,
            callback_data=f"{Buttons.next_stage.callback}_{user_course_id}",
        )
        markup = InlineKeyboardMarkup(row_width=2)
        if not has_answer and answer.score <= 3:
            sos_btn = InlineKeyboardButton(
                text=Buttons.sos.text,
                callback_data=f"{Buttons.sos.callback}_{user_course_id}",
            )
            buttons.append(sos_btn)
        buttons.append(next_stage_btn)
        markup.add(*buttons)
        handler_message(
            bot=bot,
            text=answer.response,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="quiz",
            actin="send",
            markup=markup,
        )
        storage.save_answer(
            telegram_id=user_telegram.id,
            answer=user_telegram.message_text,
            score=answer.score,
            feedback=answer.response,
            question_id=question.id,
            question=question.content,
        )
        return
    next_stage_education(
        user_telegram=user_telegram,
        bot=bot,
        storage=storage,
        user_course_id=user_course_id,
    )
