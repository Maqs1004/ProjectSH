from __future__ import annotations
import logging
import json
import requests
from requests import Response
from core.logging_config import logger
from schemas.course_schemas import (
    UserCoursesSchema,
    ModuleContentsSchema,
    PaginatedUserCoursesSchema,
)
from schemas.create_education_schemas import (
    CreatedEducationStage,
    CheckTitleCourse,
    CreatedCourse,
    PreparingQuestions,
    SummarizeAnswers,
)
from schemas.education_schemas import (
    UserCoursesNextStageSchema,
    QuestionsSchema,
    QuestionAnswersSchema,
    ContentAnswerSchema,
    UserAnswersSchema,
    HelpSchema,
)
from schemas.user_schemas import UsersSchema, TranslationSchema, UserBalance
from core.config import setting
from api.redis_connection import RedisClient
from typing import Literal
import typing

if typing.TYPE_CHECKING:
    from handlers.dependencies import TelegramUser


class StorageAPI:
    """
    Инициализирует API клиент с настройками URL, клиентом Redis и логгером.
    """

    def __init__(self):
        self.url = setting.API_URL
        self.redis_storage = RedisClient()
        self.file_storage_url = setting.SEAWEEDFS_VOLUME_URL
        self.logger = logging.getLogger(__name__)
        # self.redis_storage.clear()

    def __make_request(
        self, method: str, path: str, timeout: int = 60, *args, **kwargs
    ) -> Response | None:
        """
        Отправляет HTTP-запрос к заданному пути с указанным методом и тайм-аутом.

        Args:
            method (str): HTTP-метод для запроса (например, 'GET', 'POST').
            path (str): Путь в API для отправки запроса.
            timeout (int): Время ожидания ответа от сервера (по умолчанию 60 секунд).
            *args: Дополнительные позиционные аргументы для requests.request.
            **kwargs: Дополнительные именованные аргументы для requests.request.

        Returns:
            Response | None: Ответ от сервера, если запрос был успешным, иначе None.
        """
        try:
            self.logger.info(f"SEND TO: {self.url}/{path}, method: {method}")
            response = requests.request(
                method=method,
                url=f"{self.url}/{path}",
                timeout=timeout,
                *args,
                **kwargs,
            )
            self.logger.info(
                f"STATUS CODE FROM: {self.url}/{path} - {response.status_code}"
            )
            return response
        except Exception as error:
            self.logger.error(f"ERROR IN {self.url}/{path} - {error}")

    def get_translation(
        self, message_key: str, language_code: str
    ) -> TranslationSchema | None:
        """
        Получает перевод по заданному ключу сообщения и коду языка.

        Args:
            message_key (str): Ключ сообщения для перевода.
            language_code (str): Код языка для перевода.

        Returns:
            TranslationSchema | None: Экземпляр TranslationSchema с данными перевода, если запрос был успешным,
             иначе None.
        """
        params = {"message_key": message_key, "language_code": language_code}
        response = self.__make_request(method="GET", path="translation", params=params)
        if response.status_code == 200:
            translation = TranslationSchema.model_validate(response.json())
        elif response.status_code == 404:
            translation = TranslationSchema(
                message_key=message_key,
                language_code=language_code,
                message_text="Text not found",
            )
        else:
            translation = TranslationSchema(
                message_key=message_key,
                language_code=language_code,
                message_text="Text not found",
            )
        return translation

    def get_user(self, user_telegram: TelegramUser):
        """
        Получает информацию о пользователе по его идентификатору Telegram.

        Args:
            user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.

        Returns:
            UsersSchema | None: Экземпляр UsersSchema с данными пользователя, если запрос был успешным, иначе None.
        """
        hash_user = self.redis_storage.get(UsersSchema, f"user:{user_telegram.id}")
        if hash_user:
            return hash_user
        response = self.__make_request(path=f"users/{user_telegram.id}", method="GET")
        if response.status_code == 200:
            json_data = response.json()
            user = UsersSchema.model_validate(json_data)
            self.redis_storage.set(f"user:{user_telegram.id}", json_data, 86400)
            return user
        if response.status_code == 404:
            return None

    def get_active_user_course(
        self, user_telegram: TelegramUser
    ) -> UserCoursesSchema | None:
        """
        Получает активный курс пользователя по его идентификатору Telegram.

        Args:
            user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.

        Returns:
            UserCoursesSchema | None: Экземпляр UserCoursesSchema с данными активного курса, если запрос был успешным,
             иначе None.
        """
        response = self.__make_request(
            path=f"users/{user_telegram.id}/courses/active", method="GET"
        )
        if response.status_code == 200:
            user_course = UserCoursesSchema.model_validate(response.json())
            return user_course
        elif response.status_code == 404:
            return None

    def get_unfinished_user_courses(
        self, user_telegram, page: str = 1
    ) -> PaginatedUserCoursesSchema:
        """
        Получает незаконченные курсы пользователей.

        Args:
            user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.
            page (int): Номер страницы по которой делается пагинация, по умолчанию 1

        Returns:
            PaginatedUserCoursesSchema | None: Экземпляр UserCoursesSchema с данными активного курса, если запрос
             был успешным, иначе None.
        """
        params = {"page": page}
        response = self.__make_request(
            path=f"users/{user_telegram.id}/courses/unfinished",
            method="GET",
            params=params,
        )
        if response.status_code == 200:
            user_course = PaginatedUserCoursesSchema.model_validate(response.json())
            return user_course

    def get_archived_user_courses(
        self, user_telegram, page: str = "1"
    ) -> PaginatedUserCoursesSchema:
        """
        Получает архивные курсы пользователей.

        Args:
            user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.
            page (int): Номер страницы по которой делается пагинация, по умолчанию 1

        Returns:
            PaginatedUserCoursesSchema | None: Экземпляр UserCoursesSchema с данными активного курса, если запрос
             был успешным, иначе None.
        """
        params = {"page": page}
        response = self.__make_request(
            path=f"users/{user_telegram.id}/courses/archived",
            method="GET",
            params=params,
        )
        if response.status_code == 200:
            user_course = PaginatedUserCoursesSchema.model_validate(response.json())
            return user_course

    def add_user(self, user_telegram: TelegramUser):
        """
        Добавляет нового пользователя по его идентификатору Telegram.

        Args:
            user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.

        Returns:
            UsersSchema | None: Экземпляр UsersSchema с данными пользователя, если запрос был успешным, иначе None.
        """
        user_data = {
            "chat_id": user_telegram.chat_id,
            "username": user_telegram.user_name,
        }
        response = self.__make_request(
            path=f"users/{user_telegram.id}", method="POST", json=user_data
        )
        if response.status_code == 200:
            user = UsersSchema.model_validate(response.json())
            return user
        elif response.status_code == 409:
            return None

    def check_title(self, course_title: str, language: str) -> CheckTitleCourse:
        """
        Проверяет название курса на корректность и возможность изучения.

        Args:
            course_title (str): Название курса.
            language (str): Язык, на котором нужно вернуть ответ.

        Returns:
            CheckTitleCourse: Экземпляр CheckTitleCourse с результатом проверки.
        """
        data = {"title": course_title, "language": language}
        response = self.__make_request(
            path="courses/check-title", method="POST", json=data
        )
        if response.status_code == 200:
            check = CheckTitleCourse.model_validate(response.json())
            return check

    def get_preparing_questions(
        self, course_title: str, language: str
    ) -> PreparingQuestions:
        """
        Получает вопросы для подготовки курса по названию и возвращает на том языке, который установлен.

        Args:
            course_title (str): Название курса
            language (str): Язык, на котором нужно вернуть ответ

        Returns:
            PreparingQuestions: Экземпляр PreparingQuestions с вопросами для подготовки.
        """
        data = {"title": course_title, "language": language}
        response = self.__make_request(
            path="courses/questions-for-survey", method="POST", json=data
        )
        if response.status_code == 200:
            questions = PreparingQuestions.model_validate(response.json())
            return questions

    def set_prepare_stage(self, user_telegram_id: int, stage: str, extra_info: dict):
        """
        Устанавливает стадию подготовки курса в кэше.

        Args:
            user_telegram_id (int): Идентификатор пользователя в Telegram.
            stage (str): Текущая стадия подготовки курса.
            extra_info (dict): Дополнительная информация о стадии.
        """
        data = {"stage": stage, "extra_info": extra_info}
        self.redis_storage.set(
            f"created_course:user_telegram_id:{user_telegram_id}", data
        )

    def get_prepare_stage(self, user_telegram_id: int) -> CreatedEducationStage | None:
        """
        Получает стадию подготовки курса для пользователя из кэша.

        Args:
            user_telegram_id (int): Идентификатор пользователя в Telegram.

        Returns:
            CreatedEducationStage | None: Экземпляр CreatedEducationStage с информацией о стадии подготовки,
             если данные найдены, иначе None.
        """
        cache_key = f"created_course:user_telegram_id:{user_telegram_id}"
        stage = self.redis_storage.get(CreatedEducationStage, cache_key=cache_key)
        return stage

    def create_course(self, extra_info: dict) -> CreatedCourse:
        """
        Создает новый курс с использованием предоставленной информации.

        Args:
            extra_info (dict): Информация о создаваемом курсе (title, promo_info, questions, summary, language).

        Returns:
            CreatedCourse: Экземпляр CreatedCourse с данными созданного курса.
        """
        response = self.__make_request(
            path=f"courses", method="POST", json=extra_info, timeout=600
        )
        if response.status_code == 200:
            course = CreatedCourse.model_validate(response.json())
            return course

    def add_course_user(
        self, user_telegram_id: int, course_id: int, current_stage: str
    ) -> UserCoursesSchema:
        """
        Добавляет курс пользователю.

        Args:
            user_telegram_id (int): Идентификатор пользователя в Telegram.
            course_id (int): Идентификатор курса.
            current_stage (str): Текущая стадия курса.

        Returns:
            UserCoursesSchema: Экземпляр UserCoursesSchema с данными о добавлении пользователя к курсу.
        """
        data = {"course_id": course_id, "current_stage": current_stage}
        response = self.__make_request(
            path=f"users/{user_telegram_id}/courses", method="POST", json=data
        )
        if response.status_code == 200:
            user_course = UserCoursesSchema.model_validate(response.json())
            return user_course

    def create_material(self, course_id: str | int, language: str) -> UserCoursesSchema:
        """
        Создает учебный материал для курса на указанном языке.

        Args:
            course_id (str): Идентификатор курса.
            language (str): Язык учебного материала.

        Returns:
            bool: True, если материал успешно создан.
        """
        response = self.__make_request(
            path=f"courses/{course_id}/material/{language}", method="POST", timeout=600
        )
        if response.status_code == 200:
            user_course = UserCoursesSchema.model_validate(response.json())
            return user_course

    def summarize(self, questions_answer: dict):
        """
        Создает краткий пересказ на основе предоставленных ответов на вопросы.

        Args:
            questions_answer (dict): Ответы и вопросы.

        Returns:
            SummarizeAnswers: Экземпляр SummarizeAnswers с данными сводки.
        """
        response = self.__make_request(
            path=f"other/summarize", method="POST", json={"data": questions_answer}
        )
        if response.status_code == 200:
            summarize_answers = SummarizeAnswers.model_validate(response.json())
            return summarize_answers

    def get_user_balance(self, telegram_id: int) -> UserBalance | None:
        """
        Получает баланс пользователя по его идентификатору Telegram.

        Args:
            telegram_id (int): Идентификатор пользователя в Telegram.

        Returns:
            UserBalance | None: Экземпляр UserBalance с данными о балансе пользователя, если запрос был успешным,
             иначе None.
        """
        response = self.__make_request(
            path=f"users/{telegram_id}/balance", method="GET"
        )
        if response.status_code == 200:
            user_balance = UserBalance.model_validate(response.json())
            return user_balance

    def check_promo_code(self, telegram_id: int, promo_code: str) -> Response:
        """
        Проверяет промокод на доступность для пользователя по его идентификатору Telegram.

        Args:
            telegram_id (int): Идентификатор пользователя в Telegram.
            promo_code (str): Промокод для проверки.

        Returns:
            Response: Ответ от сервера с результатом проверки промокода.
        """
        response = self.__make_request(
            path=f"promo/{promo_code}/user/{telegram_id}", method="GET"
        )
        return response

    def change_quantity_user_course(
        self, telegram_id: int, count_course: int, action: str
    ):
        """
        Выполняет оплату, списывая указанную сумму с баланса пользователя.

        Args:
            telegram_id (int): Идентификатор пользователя в Telegram
            count_course (int): Количество курсов
            action (str): Действие которое нужно выполнить, добавить курсы или списать


        Returns:
            bool | None: В случае успешной операции отправляется True иначе None.
        """
        json_data = {"action": action, "count_course": count_course}
        response = self.__make_request(
            path=f"users/{telegram_id}/balance", method="PATCH", json=json_data
        )
        if response.status_code == 200:
            return True
        return False

    def apply_promo_code(self, telegram_id, code):
        """
        Применяет промокод для пользователя по его идентификатору Telegram.

        Args:
            telegram_id (int): Идентификатор пользователя в Telegram.
            code (str): Промокод для применения.

        Returns:
            Response: Ответ от сервера с результатом применения промокода.
        """
        response = self.__make_request(
            path=f"promo/{code}/user/{telegram_id}", method="POST"
        )
        return response

    def get_user_course_info(self, user_course_id: str) -> UserCoursesSchema:
        """
        Получает информацию о курсе пользователя по его идентификатору.

        Args:
            user_course_id (str): Идентификатор курса пользователя.

        Returns:
            UserCoursesSchema: Экземпляр UserCoursesSchema с информацией о курсе.
        """
        response = self.__make_request(
            path=f"users/courses/{user_course_id}", method="GET"
        )
        if response.status_code == 200:
            user_course_info = UserCoursesSchema.model_validate(response.json())
            return user_course_info

    def get_modul_content(
        self, sub_module_id, order_number, content_type
    ) -> ModuleContentsSchema:
        """
        Получает контент модуля по идентификатору подмодуля, номеру порядка и типу контента.

        Args:
            sub_module_id (int): Идентификатор подмодуля.
            order_number (int): Номер порядка контента.
            content_type (str): Тип контента.

        Returns:
            ModuleContentsSchema: Экземпляр ModuleContentsSchema с данными контента.
        """
        params = {"order_number": order_number, "content_type": content_type}
        response = self.__make_request(
            path=f"courses/sub-modules/{sub_module_id}/content",
            method="GET",
            params=params,
        )
        if response.status_code == 200:
            module_content = ModuleContentsSchema.model_validate(response.json())
            return module_content

    def get_image(self, fid: str):
        """
        Получает изображение по его идентификатору из хранилища файлов.

        Args:
            fid (str): Идентификатор файла изображения.

        Returns:
            bytes | None: Содержимое файла в байтах, если загрузка успешна, иначе None.
        """
        response = requests.get(f"{self.file_storage_url}/{fid}")
        if response.status_code == 200:
            logger.info("File downloaded successfully")
            return response.content
        else:
            logger.error("Failed to download file")

    def patch_user_course_info(self, user_course_id: str, **kwargs):
        """
        Обновляет информацию о курсе пользователя по его идентификатору.

        Args:
            user_course_id (str): Идентификатор курса пользователя.
            **kwargs: Поля для обновления информации о курсе.

        Returns:
            UserCoursesSchema | None: Экземпляр UserCoursesSchema с обновленными данными о курсе, если запрос был
             успешным, иначе None.
        """
        response = self.__make_request(
            path=f"users/courses/{user_course_id}", method="PATCH", json=kwargs
        )
        if response.status_code == 200:
            user_course_info = UserCoursesSchema.model_validate(response.json())
            return user_course_info

    def get_next_stage_education(self, user_course_id):
        """
        Получает следующую стадию обучения для пользователя по идентификатору курса.

        Args:
            user_course_id (str): Идентификатор курса пользователя.

        Returns:
            UserCoursesNextStageSchema | None: Экземпляр UserCoursesNextStageSchema с данными о следующей
             стадии обучения, если запрос был успешным, иначе None.
        """
        response = self.__make_request(
            path=f"users/courses/{user_course_id}/next-stage", method="GET"
        )
        if response.status_code == 200:
            next_stage = UserCoursesNextStageSchema.model_validate(response.json())
            return next_stage

    def get_question_content(
        self, sub_module_id: int, order_number: int
    ) -> QuestionsSchema:
        """
        Получает содержимое вопроса по идентификатору подмодуля и порядковому номеру.

        Args:
            sub_module_id (int): Идентификатор подмодуля.
            order_number (int): Номер порядка вопроса.

        Returns:
            QuestionsSchema | None: Экземпляр QuestionsSchema с данными вопроса, если запрос был успешным, иначе None.
        """
        params = {"order_number": order_number}
        response = self.__make_request(
            path=f"courses/sub-modules/{sub_module_id}/questions",
            params=params,
            method="GET",
        )
        if response.status_code == 200:
            questions = QuestionsSchema.model_validate(response.json())
            return questions

    def save_answer(
        self,
        telegram_id: int,
        question_id: int,
        answer: str,
        score: int,
        question: str | None = None,
        feedback: str | None = None,
    ):
        """
        Сохраняет ответ пользователя на вопрос.

        Args:
            telegram_id (int): Идентификатор пользователя в Telegram.
            question_id (int): Идентификатор вопроса.
            answer (str): Ответ пользователя.
            score (int): Оценка за ответ.
            question (str | None, optional): Текст вопроса (по умолчанию None).
            feedback (str | None, optional): Обратная связь (по умолчанию None).
        """
        json_data = {
            "question_id": question_id,
            "answer": answer,
            "score": score,
            "feedback": feedback,
            "question": question,
        }
        self.__make_request(
            path=f"users/{telegram_id}/courses/answers/save",
            json=json_data,
            method="POST",
        )

    def check_answer(
        self, question: str, answer: str, language: str, user_course_id: str
    ) -> QuestionAnswersSchema:
        """
        Проверяет ответ пользователя на вопрос.

        Args:
            question (str): Текст вопроса.
            answer (str): Ответ пользователя.
            language (str): Язык на котором нужно вернуть ответ.
            user_course_id (str): Идентификатор курса пользователя.

        Returns:
            QuestionAnswersSchema | None: Экземпляр QuestionAnswersSchema с результатами проверки, если запрос
             был успешным, иначе None.
        """
        json_data = {"question": question, "answer": answer, "language": language}
        response = self.__make_request(
            path=f"users/courses/{user_course_id}/answers/check",
            json=json_data,
            method="POST",
        )
        if response.status_code == 200:
            return QuestionAnswersSchema.model_validate(response.json())

    def get_answer(
        self, content: dict, history: list, language: str, user_course_id: str
    ):
        """
        Получает ответ на основе предоставленного контента и истории.

        Args:
            content (dict): Контент для анализа.
            history (list): История предыдущих вопросов и ответов.
            language (str): Язык на котором нужно вернуть ответ.
            user_course_id (str): Идентификатор курса пользователя.

        Returns:
            ContentAnswerSchema | None: Экземпляр ContentAnswerSchema с данными ответа, если запрос был успешным,
             иначе None.
        """
        json_data = {
            "content": json.dumps(content, ensure_ascii=False),
            "history": history,
            "language": language,
            "user_course_id": int(user_course_id),
        }
        response = self.__make_request(
            path=f"other/get-answer",
            json=json_data,
            method="POST",
        )
        content_answer = ContentAnswerSchema.model_validate(response.json())
        return content_answer

    def set_course_status(
        self,
        user_course_id: str | int,
        status: Literal["resume", "restart", "pause", "archive"],
    ):
        """
        Устанавливает статус курса пользователя.

        Args:
            user_course_id (str): Идентификатор курса пользователя.
            status (Literal["pause", "archive", "active", "rediscover"]): Новый статус курса.
        """
        response = self.__make_request(
            path=f"users/courses/{user_course_id}/{status}",
            method="POST",
        )
        if response.status_code == 200:
            user_course = UserCoursesSchema.model_validate(response.json())
            return user_course

    def get_correct_feedback(
        self,
        user_course_id: str,
        question: str,
        answer: str,
        feedback: str,
        language: str,
    ) -> HelpSchema:
        """
        Получает комментаий на неправильный ответ.

        Args:
            user_course_id (str): Идентификатор курса пользователя.
            question: (str): Вопрос бота
            answer: (str): Ответ пользователя
            feedback: (str): Комментарий/ответ бота
            language: (str): Язык на котором нужно дать ответ
        """
        json_data = {
            "question": question,
            "answer": answer,
            "feedback": feedback,
            "language": language,
        }
        response = self.__make_request(
            path=f"users/courses/{user_course_id}/answers/help",
            method="POST",
            json=json_data,
        )
        if response.status_code == 200:
            response = HelpSchema.model_validate(response.json())
            return response

    def get_user_answer(self, telegram_id: int, question_id: int) -> UserAnswersSchema:
        """
        Получает ответ пользователя по id вопроса.

        Args:
            telegram_id (int): ID телеграм пользователя
            question_id (int): ID вопроса
        """
        params = {"question_id": question_id}
        response = self.__make_request(
            path=f"users/{telegram_id}/answers", method="GET", params=params
        )
        if response.status_code == 200:
            response = UserAnswersSchema.model_validate(response.json())
            return response

    def add_invoices(self, user_telegram: TelegramUser):
        """
        Добавляет инвойс об оплате.

        Args:
            user_telegram (TelegramUser): Объект TelegramUser с информацией о пользователе.
        """
        response = self.__make_request(
            path=f"users/{user_telegram.id}/invoices",
            method="POST",
            json={"payment_info": user_telegram.payment_info},
        )
        if response.status_code == 200:
            return True
