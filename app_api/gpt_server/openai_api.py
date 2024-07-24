import json
import openai
import pydantic_core
from . import validation
from openai import OpenAI
from pydantic import BaseModel
from ..core.config import setting
from ..core.logging_config import logger
from typing import Optional, Type, Literal
from ..models.interaction import GPTModels, PromoCode, CourseContentVolume
from openai.types import CompletionUsage, ImagesResponse
from ..api.endpoints.gpt_models.schemas import GPTModelsSchema


class Response:
    """
    Класс для представления ответа GPT-модели, содержащий информацию о содержимом (ответ модели),
     использовании токенов и стоимости.

    Attributes:
        __content (dict): Словарь, содержащий ответ модели.
        __usage (Optional[CompletionUsage]): Объект, содержащий информацию об использовании токенов.
        __input_price (float): Стоимость одного токена запроса.
        __output_price (float): Стоимость одного токена ответа.
    """

    def __init__(self, content: dict, usage: Optional[CompletionUsage], input_price: float, output_price: float):
        """
        Инициализирует объект Response.

        Args:
            content (dict): Содержимое ответа модели.
            usage (Optional[CompletionUsage]): Использование токенов для данного запроса.
            input_price (float): Стоимость одного токена запроса.
            output_price (float): Стоимость одного токена ответа.
        """
        self.__content: dict = content
        self.__usage: Optional[CompletionUsage] = usage
        self.__input_price: float = input_price
        self.__output_price: float = output_price

    @property
    def spent_amount(self) -> float:
        """
        Возвращает общую стоимость токенов, использованных для запроса и ответа.

        Returns:
            float: Общая стоимость токенов.

        Raises:
            Exception: Если возникает ошибка при доступе к usage или при расчете стоимости.
        """
        try:
            prompt_cost = self.__input_price * self.__usage.prompt_tokens
            completion_cost = self.__output_price * self.__usage.completion_tokens
        except Exception as error:
            logger.error(f"{error}")
            return 0
        return prompt_cost + completion_cost

    @property
    def input_tokens(self):
        """
        Возвращает количество токенов, использованных в запросе.

        Returns:
            int: Количество токенов в запросе.

        Raises:
            Exception: Если возникает ошибка при доступе к usage.
        """
        try:
            return self.__usage.prompt_tokens
        except Exception as error:
            logger.error(f"{error}")
            return 0

    @property
    def output_tokens(self):
        """
           Возвращает количество токенов, использованных в ответе.

           Returns:
               int: Количество токенов в ответе.

           Raises:
               Exception: Если возникает ошибка при доступе к usage.
           """
        try:
            return self.__usage.completion_tokens
        except Exception as error:
            logger.error(f"{error}")
            return 0

    @property
    def content(self):
        """
        Возвращает содержимое ответа модели.

        Returns:
            dict: Содержимое ответа модели.
        """
        return self.__content

    @content.setter
    def content(self, value):
        """
        Устанавливает новое содержимое ответа модели.

        Args:
            value (dict): Новое содержимое ответа модели.
        """
        self.__content = value


class LLM:
    """
    Класс для взаимодействия с API OpenAI, поддерживающий генерацию текста и изображений.

    Attributes:
        OPENAI_API_KEY (str): API ключ для доступа к OpenAI.
    """

    def __init__(self):
        """
        Инициализирует объект LLM, загружая API ключ из настроек.
        """
        self.OPENAI_API_KEY = setting.OPENAI_API_KEY

    def _text_generator(
            self,
            client: OpenAI,
            model: GPTModels | GPTModelsSchema,
            messages: list,
            max_tokens: int,
            temperature: float,
            base_model: Type[BaseModel]
    ):
        """
        Генерирует текстовый ответ с использованием GPT модели.

        Args:
            client (OpenAI): Клиент для взаимодействия с API OpenAI.
            model (GPTModels | GPTModelsSchema): Модель GPT для генерации текста.
            messages (list): Список сообщений для модели.
            max_tokens (int): Максимальное количество токенов для генерации.
            temperature (float): Температура для генерации текста.
            base_model (Type[BaseModel]): Базовая модель для валидации ответа.

        Returns:
            Response: Объект сгенерированного ответа.

        Raises:
            Exception: Если возникает ошибка при валидации или генерации ответа.
        """
        completion = client.chat.completions.create(
            model=model.release,
            response_format={"type": "json_object"},
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        logger.info(f"Получен ответ от GPT: {completion.choices[0].message.content}")
        content = self._validate_json(completion.choices[0].message.content)
        response = Response(
            content=content,
            usage=completion.usage,
            input_price=model.input_price,
            output_price=model.output_price
        )
        base_model.model_validate(response.content)
        return response

    @staticmethod
    def _image_generator(
            client: OpenAI,
            prompt: str,
            model: GPTModels | GPTModelsSchema,
            size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024",
            quality: Literal["standard", "hd"] = "standard"
    ) -> ImagesResponse:
        """
        Генерирует изображение с использованием GPT модели.

        Args:
            client (OpenAI): Клиент для взаимодействия с API OpenAI.
            prompt (str): Текстовое описание для генерации изображения.
            model (GPTModels | GPTModelsSchema): Модель GPT для генерации изображения.
            size (Literal): Размер сгенерированного изображения.
            quality (Literal): Качество сгенерированного изображения.

        Returns:
            ImagesResponse: Объект сгенерированного изображения.
        """
        response = client.images.generate(
            model=model.release,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        return response

    def _make_request(
            self,
            model: GPTModels | GPTModelsSchema | None = None,
            base_model: Type[BaseModel] | None = None,
            messages: list[dict[str, str]] | None = None,
            max_tokens=4096,
            temperature=0.8,
            model_type: Literal["text", "image", "audio"] = "text",
            prompt: str | None = None,
            size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024",
            quality: Literal["standard", "hd"] = "standard"
    ) -> Response | ImagesResponse:
        """
        Синхронно отправляет запрос к API OpenAI, используя заданную модель и параметры.

        Args:
            model (GPTModels | GPTModelsSchema | None): Модель GPT для генерации.
            base_model (Type[BaseModel] | None): Базовая модель для валидации ответа.
            messages (list[dict[str, str]] | None): Список сообщений для текстовой генерации.
            max_tokens (int): Максимальное количество токенов для генерации.
            temperature (float): Температура для генерации текста.
            model_type (Literal): Тип модели ("text", "image", "audio").
            prompt (str | None): Текстовое описание для генерации изображения.
            size (Literal): Размер сгенерированного изображения.
            quality (Literal): Качество сгенерированного изображения.

        Returns:
            Response | ImagesResponse: Объект сгенерированного ответа или изображения.

        Raises:
            Exception: Если запрос не может быть выполнен после нескольких попыток.
        """
        client = OpenAI(timeout=220, max_retries=4)
        client.api_key = self.OPENAI_API_KEY
        logger.info(f"Делаем запрос в GPT model: {model.release}")
        logger.info(f"Запрос: {messages}")
        for retry in range(3):
            try:
                if model_type == "text":
                    response = self._text_generator(
                        client=client,
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        base_model=base_model
                    )
                    return response
                elif model_type == "image":
                    response = self._image_generator(
                        client=client,
                        model=model,
                        prompt=prompt,
                        size=size,
                        quality=quality
                    )
                    return response
            except openai.APIConnectionError as e:
                logger.error("The server could not be reached")
                logger.error(f"{e.__cause__}")
            except openai.RateLimitError as e:
                logger.error("A 429 status code was received; we should back off a bit.")
            except openai.APIStatusError as e:
                logger.error("Another non-200-range status code was received")
                logger.error(f"{e.status_code}")
                logger.error(f"{e.response}")
            except pydantic_core.ValidationError:
                logger.error("ValidationError - ")
            except Exception as error:
                logger.error(f"{error}")
        raise Exception("Generate error!")

    @staticmethod
    def _validate_json(data: str) -> dict:
        """
        Проверяет и преобразует строку в JSON, если строка не является
        валидным JSON-объектом, метод генерирует исключение.

        Args:
            - data (str): Строка для проверки и преобразования в JSON.

        Returns:
            - dict: Валидный JSON-объект.

        Исключения:
            - ValueError: Если строка не может быть преобразована в JSON.
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return {}

    def generate_course_plan(
            self,
            model: GPTModels | GPTModelsSchema,
            course_title: str,
            system_content: str,
            user_content: str,
            language: str,
            promo: PromoCode,
            summary: str | None = None
    ) -> Response:
        """
        Отправляет запрос модели GPT с указанной пользователем темой для создания плана обучения.

        Args:
            model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость
            course_title (str): Название темы, которую нужно обсудить с моделью GPT.
            summary (str | None): Дополнительная информация, которая была получена в ходе интервьюирования
              пользователя
            system_content: Инструкция системного сообщения
            language (str): Язык, на котором будет генерироваться план
            promo: (PromoCode): Информация о промо коде, для установки объема плана, если промо есть
            user_content: Сообщение пользователя

        Returns:
            - dict: Ответ модели GPT в формате словаря JSON.
        """
        if promo is not None:
            volume = promo.course_content_volume
        else:
            volume = "Короткий"
        user_content = user_content.format(course_title=course_title, summary=summary, volume=volume, language=language)
        if summary is None:
            user_content = user_content[:user_content.find("\n")]
        system = {"role": "system", "content": system_content}
        user = {"role": "user", "content": user_content}
        response = self._make_request(messages=[system, user], model=model, base_model=validation.PlanResponse)
        response.content = response.content["plan"]
        return response

    def allow_course(
            self,
            title: str,
            system_content: str,
            language: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет запрос модели GPT с указанной пользователем темой для проверки на возможность обучения.

        Args:
            model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость
            title (str): Название темы, которую нужно обсудить с моделью GPT
            system_content: Инструкция системного сообщения
            language (str): Язык

        Returns:
            dict: Ответ модели GPT в формате словаря JSON.
        """
        system_content = system_content.format(language=language)
        system = {"role": "system", "content": system_content}
        user = {"role": "user", "content": title}
        response = self._make_request(
            messages=[system, user],
            max_tokens=256,
            model=model,
            base_model=validation.AllowCourseResponse
        )
        return response

    def generate_module_content(
            self,
            system_content: str,
            user_content: str,
            course_title: str,
            sub_module_title: str,
            content_title: str,
            previews_sections: list,
            summary: str | None,
            is_first_time: bool,
            language: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет запрос модели GPT с указанной пользователем темой для получения по ней информации.

        Args:
            system_content (str): Инструкция системного сообщения
            user_content (str): Инструкция пользовательского сообщения
            course_title (str): Название курса, который изучается.
            sub_module_title (str): Название подтемы, которую нужно изучить.
            content_title (str): Название темы, которую нужно изуичть
            previews_sections (None|list): Название тем, которые были изучены.
            summary (str): Самари ответов пользователя про тему
            is_first_time (bool): Первый ли материал в курсе
            language (str): Язык, на котором будет подготавливаться матерьял
            model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость

        Returns:
            - Response: Ответ модели GPT в формате словаря JSON.
        """
        system = {"role": "system", "content": system_content}
        user_content = user_content.format(
            course_title=course_title,
            sub_module_title=sub_module_title,
            content_title=content_title,
            language=language
        )
        if previews_sections:
            user_content += " Учти, что до этого я изучил эти темы, что бы ты не повторялся:"
            for section_name in previews_sections:
                user_content += f" {section_name}"
        if summary is not None:
            user_content += f"\nВот что тебе надо учитывать, когда ты будешь подготавливать контент: {summary}. "
            user_content += "В материале не акцентируй внимание на том, что я рассказал о себе, просто имей ввиду "
            user_content += "эту информацию, в первую очередь сконцентрируйся на материале."
        if is_first_time:
            user_content += f" Эта наша с тобой первая встреча в обучении, поэтому поприветствуй меня"
        else:
            user_content += f" Эта наша с тобой не первая часть обучения, поэтому не нужно приветствий."
        user = {"role": "user", "content": user_content}
        response = self._make_request(messages=[system, user], model=model, base_model=validation.ContentResponse)
        return response

    def generate_open_question(
            self,
            content: str,
            user_content: str,
            language: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет запрос модели GPT с пройденной информацией для получения по ней открытого вопроса.

        Args:
            content (dict): Информация, которая была пройдена.
            user_content (str): Инструкция пользовательского сообщения
            language (str): Язык на котором будут формироваться
            model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость

        Returns:
            Response: Ответ модели GPT в формате словаря JSON.
        """
        user_content = user_content.format(content=content, language=language)
        user = {"role": "user", "content": user_content}
        response = self._make_request(model=model, messages=[user], base_model=validation.OpenQuestionResponse)
        return response

    def generate_multiple_choice_question(
            self,
            content: dict[str, dict[str, str | list[dict[str, str]]]],
            user_content,
            language: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет запрос модели GPT с пройденной информацией для получения по ней вопросов с вариантами ответа.

        Args:
            content (dict): Информация, которая была пройдена.
            user_content (str): Инструкция пользовательского сообщения
            language (str): Язык на котором будут формироваться
            model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость

        Returns:
            Response: Ответ модели GPT в формате словаря JSON.
        """
        user_content = user_content.format(content=content, language=language)
        user = {"role": "user", "content": user_content}
        response = self._make_request(
            model=model,
            messages=[user],
            base_model=validation.MultipleChoiceQuestionResponse
        )
        return response

    def generate_answer(
            self,
            question: str,
            answer: str,
            user_content: str,
            system_content: str,
            language: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет вопрос, который был задан пользователю и ответ пользователя, для проверки.

        Args:
            system_content (str): Инструкция системного сообщения
            user_content (str): Инструкция пользовательского сообщения
            question (str): Вопрос, который был задан пользователю.
            answer (str): Ответ, который дал пользователь.
            language (str): Язык на котором нужно дать комментарий
            model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость

        Returns:
            - Response: Ответ модели GPT в формате словаря JSON.
        """
        user_content = user_content.format(question=question, answer=answer, language=language)
        user = {"role": "user", "content": user_content}
        system = {"role": "system", "content": system_content}
        response = self._make_request(model=model, messages=[system, user], base_model=validation.AnswersResponse)
        return response

    def generate_questions_for_survey(
            self,
            course_title: str,
            language: str,
            user_content: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет вопрос, который был задан пользователю и ответ пользователя, для проверки.

        Args:
            user_content (str): Инструкция пользовательского сообщения
            course_title (str): Название темы, которую пользователь хочет изучить.
            language (str): Язык
            model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость

        Returns:
            - Response: Ответ модели GPT в формате словаря JSON.
        """
        user_content = user_content.format(course_title=course_title, language=language)
        user = {"role": "user", "content": user_content}
        response = self._make_request(
            model=model,
            max_tokens=1024,
            messages=[user],
            base_model=validation.SurveyResponse
        )
        return response

    def summarize_answers(
            self,
            personal_question: dict,
            user_content: str,
            system_content: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет вопросы ответы пользователя при подготовке к теме, что бы суммаризировать информацию.

        Args:
             system_content (str): Инструкция системного сообщения
             user_content (str): Инструкция пользовательского сообщения
             personal_question (dict): Словарь, где ключи это вопросы, а значения ответы на вопросы.
             model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость

        Returns:
             Response: Ответ модели GPT в формате словаря JSON.
        """
        question_answer = "\n".join(f"{question} - {answer}" for question, answer in personal_question.items())
        user_content = user_content.format(question_answer=question_answer)
        user = {"role": "user", "content": user_content}
        system = {"role": "system", "content": system_content}
        response = self._make_request(
            model=model,
            max_tokens=1024,
            messages=[system, user],
            base_model=validation.SummarizeModel
        )
        return response

    def generate_prompt(
            self,
            system_content: str,
            user_content: str,
            course_title: str,
            sub_module_title: str,
            content_title: str,
            model: GPTModels | GPTModelsSchema
    ) -> Response:
        """
        Отправляет вопросы ответы пользователя при подготовке к теме, что бы суммаризировать информацию.

        Args:
             system_content (str): Инструкция системного сообщения
             user_content (str): Инструкция пользовательского сообщения
             course_title (str): Название курса
             sub_module_title (str): Названия подмодуля
             content_title (str): название текущий темы
             model (GPTModels | GPTModelsSchema): Объект модели, содержащий название модели, стоимость

        Returns:
             Response: Ответ модели GPT в формате словаря JSON.
        """
        user_content = user_content.format(
            course_title=course_title,
            sub_module_title=sub_module_title,
            content_title=content_title
        )
        user = {"role": "user", "content": user_content}
        system = {"role": "system", "content": system_content}
        response = self._make_request(
            model=model,
            max_tokens=1024,
            messages=[system, user],
            base_model=validation.PromptResponse
        )
        return response

    def generate_image(
            self,
            prompt,
            model: GPTModels | GPTModelsSchema,
            size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] = "1024x1024",
            quality: Literal["standard", "hd"] = "standard"
    ):
        response = self._make_request(prompt=prompt, model_type="image", size=size, quality=quality, model=model)
        return response.data[0].url

    def generate_content_answers(
            self,
            system_content: str,
            user_content: str,
            content: str,
            language: str,
            history: list,
            model: GPTModels | GPTModelsSchema
    ):
        system = {"role": "system", "content": system_content}
        user = {"role": "user", "content": user_content.format(content=content, language=language)}

        messages = [system, user]
        for dialogue in history:
            messages.append(dialogue)
        response = self._make_request(
            model=model,
            max_tokens=1024,
            messages=messages,
            base_model=validation.ContentAnswerResponse
        )
        return response

    def generate_correct(
            self,
            system_content: str,
            user_content: str,
            question: str,
            answer: str,
            language: str,
            feedback: str,
            model: GPTModels | GPTModelsSchema

    ):

        system = {"role": "system", "content": system_content}
        question = {"role": "assistant", "content": question}
        answer = {"role": "user", "content": answer}
        feedback = {"role": "assistant", "content": feedback}
        help_content = {"role": "user", "content": user_content.format(language=language)}
        messages = [system, question, answer, feedback, help_content]
        response = self._make_request(
            model=model,
            max_tokens=2048,
            messages=messages,
            base_model=validation.HelpResponse
        )
        return response
