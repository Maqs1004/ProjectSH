from fastapi.openapi.models import Response
from redis import Redis
from sqlalchemy.orm import Session
from app_api.db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from app_api.db.redis_connection import get_redis
from app_api.models.education import ContentType
from .schemas import (CourseTitleSchema, CreateCoursePlanSchema, QuestionsSchema, QuestionsForSurveySchema,
                      ModuleContentsSchema)
from app_api.gpt_server.openai_api import LLM
from app_api.gpt_server.validation import AllowCourseResponse, PlanResponse
from app_api.api.endpoints.gpt_models.crud import get_model_by_id
from .crud import add_course_data, get_course, get_question, get_module_content, \
    generate_main_content
from app_api.api.endpoints.prompts.crud import get_prompt
from ..user_courses.schemas import UserCoursesSchema

courses = APIRouter(prefix="/courses", tags=["Courses"])


@courses.post(path="/check-title",
              response_model=AllowCourseResponse,
              summary="Проверка темы на доступность к обучению"
              )
def course_route(course: CourseTitleSchema,
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    """
    Валидирует название курса.

    Этот эндпоинт предназначен для валидации курса. Либо пропускает этот курс к обучению, либо нет


    ### Параметры
    - `title` (str): Название курса.

    ### Возвращает
    - `UsersSchema`: Схема данных о пользователе
    """
    prompt = get_prompt(db=db, redis=redis, name="allow_topic")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    response = gpt.allow_course(title=course.title, system_content=prompt.system, model=model, language=course.language)
    return response.content


@courses.post(path="",
              response_model=PlanResponse,
              summary="Создает курс и план обучения"
              )
def course_route(create_course: CreateCoursePlanSchema,
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    """
    Создает план обучения.

    Этот эндпоинт предназначен создания плана обучения по названию курса и если есть обобщенная информация о
    пользователе которую он мог предоставить боту


    ### Параметры
    - `title` (str): Название курса.
    - `summary` (str | None): Дополнительная информация, которая была получена в ходе интервьюирования
        пользователя

    ### Возвращает
    - `UsersSchema`: Схема данных о пользователе.
    """
    prompt = get_prompt(db=db, redis=redis, name="generate_course_plan")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    response = gpt.generate_course_plan(
        course_title=create_course.title,
        summary=create_course.summary,
        promo=create_course.promo_info,
        model=model,
        system_content=prompt.system,
        user_content=prompt.user,
        language=create_course.language
    )
    course = add_course_data(db=db, course_data=response.content, create_course=create_course, redis=redis)
    return {"course_id": course.id, "plan": response.content}


@courses.post(path="/{course_id}/material/{language}",
              response_model=UserCoursesSchema,
              summary="Создаёт материала для курса (контент и вопросы)"
              )
def course_route(course_id: int,
                 language: str,
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    """
    Создает основной материал обучения в который входит обучающий материал и вопросы к нему.

    Этот эндпоинт предназначен создания материала обучения на основе плана, который пользователю был предоставлен
    заранее.


    ### Параметры
    - `course_id` (int): ID курса, для которого надо составить материал.
    - `language` (str): Язык, на котором будет подготавливаться курс

    ### Возвращает

    """

    gpt = LLM()
    course = get_course(db=db, redis=redis, course_id=course_id)
    if course.is_generated:
        raise HTTPException(status_code=409, detail=f"Course already generated")
    if not course.available:
        raise HTTPException(status_code=409, detail=f"Course not available")
    user_course = generate_main_content(db=db, course=course, redis=redis, gpt=gpt, language=language)
    return user_course


@courses.get(path="/sub-modules/{sub_module_id}/questions",
             response_model=QuestionsSchema,
             summary="Получает вопрос по sub_module_id и order_number")
def course_route(sub_module_id: int,
                 order_number: int = Query(description="Порядковый номер вопроса"),
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    question = get_question(db=db, redis=redis, sub_module_id=sub_module_id, order_number=order_number)
    return question


@courses.get(path="/sub-modules/{sub_module_id}/content",
             response_model=ModuleContentsSchema,
             summary="Получает контент по sub_module_id и order_number")
def course_route(sub_module_id: int,
                 content_type: ContentType = Query(description="Тип контента, текст или изображение"),
                 order_number: int = Query(description="Порядковый номер контента"),
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    content = get_module_content(db=db, redis=redis, sub_module_id=sub_module_id,
                                 order_number=order_number, content_type=content_type)
    return content


@courses.post(path="/questions-for-survey",
              response_model=QuestionsForSurveySchema,
              summary="Генерирует вопросы для опроса пользователя о теме")
def course_route(course: CourseTitleSchema,
                 db: Session = Depends(get_db),
                 redis: Redis = Depends(get_redis)
                 ):
    prompt = get_prompt(db=db, redis=redis, name="generate_questions_for_survey")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    response = gpt.generate_questions_for_survey(
        user_content=prompt.user,
        course_title=course.title,
        model=model,
        language=course.language
    )
    return response.content
