from bs4 import BeautifulSoup, NavigableString
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from api.client import StorageAPI
from handlers.dependencies import TelegramUser, handler_message
from handlers.utils import Buttons, TranslationKeys
from schemas.course_schemas import ModuleContentsSchema, UserCoursesSchema


def show_content(
    text_content: ModuleContentsSchema,
    image_content: ModuleContentsSchema | None,
    bot: TeleBot,
    storage: StorageAPI,
    user_telegram: TelegramUser,
    education_course: UserCoursesSchema,
):
    """
    Подготавливает материал для пользователя и отправляет ему в виде сообщения

    Args:

    """
    text_content_data = text_content.content_data
    main_title = f"{clean_and_escape_html(text_content_data.get('title', ''))}"
    if image_content:
        image = storage.get_image(fid=image_content.content_data["fid"])
        bot.send_photo(
            chat_id=user_telegram.chat_id,
            photo=image,
            caption=main_title,
            parse_mode="HTML",
        )
    else:
        handler_message(
            bot=bot,
            text=main_title,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="education",
            actin="send",
            parse_mode="HTML",
        )
    introduction = f"{clean_and_escape_html(text_content_data.get('introduction', ''))}"
    handler_message(
        bot=bot,
        text=introduction,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="education",
        actin="send",
        parse_mode="HTML",
    )
    sections = text_content_data.get("sections", [])
    for section in sections:
        body = ""
        title = section.get("title")
        content = section.get("content")
        if title:
            body += f"{clean_and_escape_html(title)}\n\n"
        if content:
            body += f"{clean_and_escape_html(content)}\n"
        handler_message(
            bot=bot,
            text=body,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="education",
            actin="send",
            parse_mode="HTML",
        )
    conclusion = f"{text_content_data.get('conclusion', '')}"
    markup = InlineKeyboardMarkup(row_width=5)
    user_course_id = education_course.id
    buttons = []
    rating_up_btn = InlineKeyboardButton(
        text=Buttons.rating_up.text,
        callback_data=f"{Buttons.rating_up.callback}_{user_course_id}",
    )
    buttons.append(rating_up_btn)
    rating_down_btn = InlineKeyboardButton(
        text=Buttons.rating_down.text,
        callback_data=f"{Buttons.rating_down.callback}_{user_course_id}",
    )
    buttons.append(rating_down_btn)
    if education_course.usage_count == 0:
        ask_question_btn = InlineKeyboardButton(
            text=Buttons.ask_question.text,
            callback_data=f"{Buttons.ask_question.callback}_{user_course_id}",
        )
        buttons.append(ask_question_btn)
    next_stage_btn = InlineKeyboardButton(
        text=Buttons.next_stage.text,
        callback_data=f"{Buttons.next_stage.callback}_{user_course_id}",
    )
    buttons.append(next_stage_btn)
    markup.add(*buttons)
    handler_message(
        bot=bot,
        text=conclusion,
        chat_id=user_telegram.chat_id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="education",
        actin="send",
        parse_mode="HTML",
        markup=markup,
    )


def clean_and_escape_html(html):
    """
    Очищает HTML-код от всех тегов, кроме разрешенных, и преобразует специальные символы в HTML-сущности.

    Эта функция удаляет все HTML-теги из входной строки, за исключением тех, которые указаны в списке разрешенных.
    Также она заменяет символы "<" и ">" на соответствующие HTML-сущности (&lt; и &gt;)
    в текстовых участках, которые не являются тегами.
    Это предотвращает выполнение потенциально вредоносного кода при отображении строки как HTML.

    Args:
        - html (str): Строка, содержащая HTML-код, который нужно очистить.

    Returns:
        - str: Очищенная и безопасная для отображения как HTML строка.
    """
    allowed_tags = ["code", "b", "i", "u", "s", "pre"]
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()

    # Замена символов "<" и ">" на HTML-сущности в не-теговых частях
    for content in soup.descendants:
        if isinstance(content, NavigableString):
            content.replace_with(content.replace("<", "&lt;").replace(">", "&gt;"))

    return str(soup)


def rating_up(call: CallbackQuery, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает повышение рейтинга курса.

    Вызывает функцию изменения рейтинга с операцией "повышение".

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_course_id = call.data.split(f"{Buttons.rating_up.callback}_")[1]
    edit_rating(
        call=call,
        bot=bot,
        storage=storage,
        operation="up",
        user_course_id=user_course_id,
    )


def rating_down(call: CallbackQuery, bot: TeleBot, storage: StorageAPI):
    """
    Обрабатывает понижение рейтинга курса.

    Вызывает функцию изменения рейтинга с операцией "понижение".

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
    """
    user_course_id = call.data.split(f"{Buttons.rating_down.callback}_")[1]
    edit_rating(
        call=call,
        bot=bot,
        storage=storage,
        operation="down",
        user_course_id=user_course_id,
    )


def edit_rating(
    call: CallbackQuery,
    bot: TeleBot,
    storage: StorageAPI,
    operation: str,
    user_course_id: str,
):
    """
    Изменяет рейтинг курса.

    Увеличивает или уменьшает рейтинг курса в зависимости от операции и обновляет информацию о курсе.

    Args:
        call (CallbackQuery): Запрос обратного вызова от пользователя
        bot (TeleBot): Экземпляр Telegram бота
        storage (StorageAPI): Экземпляр для работы с хранилищем данных
        operation (str): Операция изменения рейтинга ("up" для повышения, "down" для понижения)
        user_course_id (str): Идентификатор курса пользователя
    """
    user_telegram = TelegramUser(call)
    user_course = storage.get_user_course_info(user_course_id=user_course_id)
    if operation == "up":
        rating = user_course.rating + 1
    elif operation == "down":
        rating = user_course.rating - 1
    else:
        rating = user_course.rating
    storage.patch_user_course_info(user_course_id=user_course_id, rating=rating)
    markup = InlineKeyboardMarkup(row_width=5)
    buttons = []
    next_stage_btn = InlineKeyboardButton(
        text=Buttons.next_stage.text,
        callback_data=f"{Buttons.next_stage.callback}_{user_course_id}",
    )
    if user_course.usage_count == 0:
        ask_question_btn = InlineKeyboardButton(
            text=Buttons.ask_question.text,
            callback_data=f"{Buttons.ask_question.callback}_{user_course_id}",
        )
        buttons.append(ask_question_btn)
    buttons.append(next_stage_btn)
    markup.add(*buttons)
    handler_message(
        bot=bot,
        text=call.message.text,
        chat_id=call.message.chat.id,
        user_telegram=user_telegram,
        storage=storage,
        type_message="system",
        actin="edit",
        message_id=call.message.message_id,
        markup=markup,
    )


def check_activity(
    storage: StorageAPI, user_course_id: str, user_telegram: TelegramUser, bot: TeleBot
):
    """
    Проверяет активность курса пользователя.

    Если курс неактивен, отправляет сообщение пользователю и возвращает None. Иначе возвращает информацию о курсе.

    Args:
        storage (StorageAPI): Экземпляр для работы с хранилищем данных.
        user_course_id (str): Идентификатор курса пользователя.
        user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.
        bot (TeleBot): Экземпляр Telegram бота.

    Returns:
        current_education_stage: Информация о текущем этапе курса или None, если курс неактивен.
    """
    current_education_stage = storage.get_user_course_info(
        user_course_id=user_course_id
    )
    if not current_education_stage.active:
        inactive_course = storage.get_translation(
            message_key=TranslationKeys.inactive_course_message,
            language_code=user_telegram.language,
        )
        handler_message(
            bot=bot,
            text=inactive_course.message_text,
            chat_id=user_telegram.chat_id,
            user_telegram=user_telegram,
            storage=storage,
            type_message="system",
            actin="edit",
            message_id=user_telegram.message_id,
        )
        return
    return current_education_stage
