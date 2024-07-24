from typing import Literal

from fastapi.openapi.models import Response
from redis import Redis
from sqlalchemy.orm import Session
from app_api.db.session import get_db
from fastapi import APIRouter, Depends, Path, Query
from app_api.db.redis_connection import get_redis
from app_api.api.endpoints.users.schemas import UsersNotFoundErrorSchema
from app_api.gpt_server.openai_api import LLM
from app_api.gpt_server.validation import AnswersResponse, HelpResponse
from .schemas import (UserCoursesSchema, UserCoursesNotFoundErrorSchema, PaginatedUserCoursesSchema,
                      AddUserCoursesSchema, UserCoursesNextStageSchema, PatchUserCoursesSchema, AddUserAnswersSchema,
                      CheckAnswersSchema, HelpAnswersSchema)
from .crud import (get_user_course, get_archived_user_courses, get_unfinished_user_courses, get_active_user_courses,
                   add_user_courses, get_next_stage, patch_user_courses, add_answers, archive_user_courses,
                   resume_user_courses, pause_user_courses, restart_user_courses, get_user_courses
                   )
from ..gpt_models.crud import get_model_by_id
from ..prompts.crud import get_prompt

user_courses = APIRouter(tags=["Users"])


@user_courses.get(path="/courses/{user_course_id}",
                  response_model=UserCoursesSchema,
                  summary="Получение информации кусе пользователя",
                  responses={404: {"model": UserCoursesNotFoundErrorSchema, "description": "Course not found"}}
                  )
def user_courses_route(user_course_id: int = Path(description="ID курса пользователя", example=1),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis)
                       ):
    """
    Получает информацию о курсе пользователя по его ID.

    ### Параметры
    - `courseId` (int): ID Курса пользователя.

    ### Возвращает
    - `UserCoursesSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если курс пользователя с указанным ID не найден.
    """
    user_course = get_user_course(db=db, redis=redis, user_course_id=user_course_id)
    return user_course


@user_courses.patch(path="/courses/{user_course_id}",
                    response_model=UserCoursesSchema,
                    summary="Обновляет запись пользовательского курса",
                    responses={404: {"model": UserCoursesNotFoundErrorSchema, "description": "Course not found"}}
                    )
def user_courses_route(user_course: PatchUserCoursesSchema,
                       user_course_id: int = Path(description="ID курса пользователя", example=1),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis)
                       ):
    """
    Обновляет информацию о курсе пользователя по его ID.

    ### Параметры
    - `courseId` (int): ID Курса пользователя.

    ### Возвращает
    - `UserCoursesSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если курс пользователя с указанным ID не найден.
    """
    user_course = patch_user_courses(db=db, redis=redis, user_course_id=user_course_id, user_course=user_course)
    return user_course


@user_courses.post(path="/courses/{user_course_id}/{status}",
                   summary="Меняет статус курса",
                   response_model=UserCoursesSchema,
                   responses={404: {"model": UserCoursesNotFoundErrorSchema, "description": "Course not found"}}
                   )
def user_courses_route(
        status: Literal["pause", "archive", "resume", "restart"] = Path(description="Статус изменения"),
        user_course_id: int = Path(description="ID курса пользователя", example=1),
        db: Session = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    """
    Меняет статус курса (переведен в архив, начат заново, приостановлен, активирован).

    ### Параметры
    - `courseId` (int): ID Курса пользователя.


    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если курс пользователя с указанным ID не найден.
    """
    status_function_map = {
        "pause": pause_user_courses,
        "archive": archive_user_courses,
        "resume": resume_user_courses,
        "restart": restart_user_courses
    }
    user_course = status_function_map[status](db=db, redis=redis, user_course_id=user_course_id)
    return user_course


@user_courses.get(path="/courses/{user_course_id}/next-stage",
                  response_model=UserCoursesNextStageSchema,
                  summary="Получение следующего шага обучения",
                  responses={404: {"model": UserCoursesNotFoundErrorSchema, "description": "Course not found"}}
                  )
def user_courses_route(user_course_id: int = Path(description="ID курса пользователя", example=1),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis)
                       ):
    """
    Получает информацию о следующем шаге обучения, это может быть блок с материалом или вопросы
    его ID.

    ### Параметры
    - `courseId` (int): ID Курса пользователя.

    ### Возвращает
    - `UserCoursesSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если курс пользователя с указанным ID не найден.
    """
    next_stage = get_next_stage(db=db, redis=redis, user_course_id=user_course_id)
    return next_stage


@user_courses.post(path="/{telegram_id}/courses",
                   response_model=UserCoursesSchema,
                   summary="Добавляет запись круса пользователя",
                   responses={404: {"model": UsersNotFoundErrorSchema, "description": "User not found"}}
                   )
def user_courses_route(user_course: AddUserCoursesSchema,
                       telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis),
                       ):
    """
    Добавляет пользователю курс для дальнейшего прохождения.

    ### Параметры
    - `telegram_id` (int): Уникальный телеграм ID пользователя.

    ### Возвращает
    - `UserCoursesSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, пользователь не найден.
    """
    user_course = add_user_courses(db=db, redis=redis, telegram_id=telegram_id, user_course=user_course)
    return user_course


@user_courses.post(path="/{telegram_id}/courses/answers/save",
                   summary="Добавляет запись ответа пользователя на вопрос",
                   responses={404: {"model": UsersNotFoundErrorSchema, "description": "User not found"}}
                   )
def user_courses_route(answer: AddUserAnswersSchema,
                       telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis),
                       ):
    """
    Добавляет запись ответа пользователя на вопрос.

    ### Параметры
    - `telegram_id` (int): Уникальный телеграм ID пользователя.

    ### Возвращает
    - `UserCoursesSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, пользователь не найден.
    """
    add_answers(db=db, redis=redis, telegram_id=telegram_id, answer=answer)
    return Response(status_code=200, description="Saved successfully")


@user_courses.post(path="/courses/{user_course_id}/answers/check",
                   response_model=AnswersResponse,
                   summary="Проверят ответ пользователя"
                   )
def user_courses_route(answer: CheckAnswersSchema,
                       user_course_id: int = Path(description="ID курса пользователя", example=1),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis),
                       ):
    """
    Добавляет запись ответа пользователя на вопрос.

    ### Параметры
    - `user_course_id` (int): Уникальный телеграм ID пользовательского курса.

    ### Возвращает
    - `UserCoursesSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, пользователь не найден.
    """
    prompt = get_prompt(db=db, redis=redis, name="generate_answer")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    feedback = gpt.generate_answer(
        question=answer.question,
        answer=answer.answer,
        language=answer.language,
        system_content=prompt.system,
        user_content=prompt.user,
        model=model
    )
    user_course = get_user_course(db=db, redis=redis, user_course_id=user_course_id)
    patch_course = PatchUserCoursesSchema(
        input_token=user_course.input_token + feedback.input_tokens,
        output_token=user_course.output_token + feedback.output_tokens,
        spent_amount=user_course.spent_amount + feedback.spent_amount,
    )
    patch_user_courses(db=db, redis=redis, user_course_id=user_course_id, user_course=patch_course)
    return feedback.content


@user_courses.post(path="/courses/{user_course_id}/answers/help",
                   response_model=HelpResponse,
                   summary="Дает комментарий на неправильный ответ пользователя"
                   )
def user_courses_route(help_content: HelpAnswersSchema,
                       user_course_id: int = Path(description="ID курса пользователя", example=1),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis),
                       ):
    """
    Добавляет запись ответа пользователя на вопрос.

    ### Параметры
    - `user_course_id` (int): Уникальный телеграм ID пользовательского курса.

    ### Возвращает
    - `UserCoursesSchema`: Схема данных о курсе пользователя

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, пользователь не найден.
    """
    prompt = get_prompt(db=db, redis=redis, name="corrector")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    feedback = gpt.generate_correct(
        question=help_content.question,
        answer=help_content.answer,
        language=help_content.language,
        feedback=help_content.feedback,
        system_content=prompt.system,
        user_content=prompt.user,
        model=model
    )
    user_course = get_user_course(db=db, redis=redis, user_course_id=user_course_id)
    patch_course = PatchUserCoursesSchema(
        input_token=user_course.input_token + feedback.input_tokens,
        output_token=user_course.output_token + feedback.output_tokens,
        spent_amount=user_course.spent_amount + feedback.spent_amount,
    )
    patch_user_courses(db=db, redis=redis, user_course_id=user_course_id, user_course=patch_course)
    return feedback.content


@user_courses.get(path="/{telegram_id}/courses",
                  response_model=UserCoursesSchema | PaginatedUserCoursesSchema,
                  summary="Получение курсов пользователей пользователя по заданным"
                  )
def user_courses_route(telegram_id: int = Path(description="Уникальный телеграм ID пользователя", example=123456789),
                       status: Literal["active", "unfinished", "archived"] | None = Query(default=None),
                       page: int = Query(default=1, description="Номер страницы"),
                       db: Session = Depends(get_db),
                       redis: Redis = Depends(get_redis)
                       ):
    """
    Получает список курсов, в зависимости от статуса, если статус None, то возвращает все курсы пользователя.

    ### Параметры
    - `telegram_id` (int): Уникальный телеграм ID пользователя.
    - `status` Literal["active", "unfinished", "archived"] | None: Статус получаемых курсов.
    - `page` (int): Страница запроса.
    
    ### Возвращает
    - [`UserCoursesSchema`]: Список схем данных архивных курсов пользователей

    ### Исключения
    - `HTTPException` с кодом 404: Вызывается, если пользователь с указанным ID не найден.
    """
    if status == "active":
        user_course = get_active_user_courses(db=db, redis=redis, telegram_id=telegram_id)
    elif status == "unfinished":
        user_course = get_unfinished_user_courses(db=db, redis=redis, telegram_id=telegram_id, page=page)
    elif status == "archived":
        user_course = get_archived_user_courses(db=db, redis=redis, telegram_id=telegram_id, page=page)
    else:
        user_course = get_user_courses(db=db, redis=redis, telegram_id=telegram_id, page=page)
    return user_course
