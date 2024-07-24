from types import SimpleNamespace

from redis import Redis
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app_api.models.education import UserCourseTracker, ContentType, UserAnswers
from app_api.api.dependencies import get_record, Cache, get_records, patch_record, add_record
from .schemas import UserCoursesSchema, PaginatedUserCoursesSchema, AddUserCoursesSchema, PatchUserCoursesSchema, \
    AddUserAnswersSchema, UserAnswersSchema
from app_api.models.education import CurrentStage
from app_api.api.endpoints.users.crud import get_user
from ..courses.crud import (get_course, get_module, get_sub_module, get_module_content, get_question,
                            get_module_by_id, get_sub_module_by_id)


def get_user_course(
        db: Session,
        redis: Redis,
        user_course_id: int,
        only_check=False,
) -> UserCoursesSchema | None | UserCourseTracker:
    """
    Извлекает запись курсе пользователя по ID.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        user_course_id (int): ID Курса
        only_check (bool): Флаг, указывающий что при отсутствии записи не выводить ошибку

    Returns:
        Union[PromptsSchema, None, Prompts]: Объект курса пользователя, если он найден; иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=UserCourseTracker,
        base_model=UserCoursesSchema,
        identifier=user_course_id,
        only_check=only_check,
        cache_key="user_course:id",
        filters=[["id", user_course_id, "eq"]],
    )
    return query


def get_archived_user_courses(
        db: Session,
        redis: Redis,
        telegram_id: int,
        page: int,
) -> PaginatedUserCoursesSchema | None | dict:
    """
    Извлекает архивные курсы пользователя по telegram_id.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        telegram_id (int): Telegram ID пользователя
        page (int): Страница для пагинации

    Returns:
        Union[PaginatedUserCoursesSchema | None | dict]: Записи архивных курсов.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    queries = get_records(
        db=db,
        page=page,
        redis=redis,
        sql_model=UserCourseTracker,
        base_model=PaginatedUserCoursesSchema,
        cache_key=f"archived_user_courses:user:{user.id}",
        filters=[["user_id", user.id, "eq"], ["archived", True, "eq"]],
        extract_base_model=UserCoursesSchema
    )
    return queries


def get_unfinished_user_courses(
        db: Session,
        redis: Redis,
        telegram_id: int,
        page: int,
) -> PaginatedUserCoursesSchema | None | dict:
    """
    Извлекает незаконченные курсы пользователя по telegram_id.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        telegram_id (int): Telegram ID пользователя
        page (int): Страница для пагинации

    Returns:
        Union[PaginatedUserCoursesSchema | None | dict]: Записи незаконченных курсов.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    queries = get_records(
        db=db,
        page=page,
        redis=redis,
        sql_model=UserCourseTracker,
        base_model=PaginatedUserCoursesSchema,
        cache_key=f"unfinished_user_courses:user:{user.id}",
        filters=[["user_id", user.id, "eq"], ["archived", False, "eq"],
                 ["finished", False, "eq"], ["active", False, "eq"]],
        extract_base_model=UserCoursesSchema
    )
    return queries


def get_user_courses(
        db: Session,
        redis: Redis,
        telegram_id: int,
        page: int,
) -> PaginatedUserCoursesSchema | None | dict:
    """
    Извлекает все курсы пользователя по telegram_id.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        telegram_id (int): Telegram ID пользователя
        page (int): Страница для пагинации

    Returns:
        Union[PaginatedUserCoursesSchema | None | dict]: Записи незаконченных курсов.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    queries = get_records(
        db=db,
        page=page,
        redis=redis,
        sql_model=UserCourseTracker,
        base_model=PaginatedUserCoursesSchema,
        cache_key=f"user_courses:user:{user.id}",
        filters=[["user_id", user.id, "eq"]],
        extract_base_model=UserCoursesSchema
    )
    return queries


def get_active_user_courses(
        db: Session,
        redis: Redis,
        telegram_id: int,
        only_check=False,
) -> UserCoursesSchema | None | UserCourseTracker:
    """
    Извлекает активный курс пользователя по telegram_id.

    Args:
        db (Session): Сессия SQL Alchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        telegram_id (int): Telegram ID пользователя
        only_check (bool): Флаг, указывающий что при отсутствии записи не выводить ошибку

    Returns:
        Union[UserCoursesSchema | None | UserCourseTracker]: Объект курса пользователя, если он найден; иначе None.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    query = get_record(
        db=db,
        redis=redis,
        sql_model=UserCourseTracker,
        base_model=UserCoursesSchema,
        identifier=user.id,
        only_check=only_check,
        cache_key=f"active_user_courses:user",
        filters=[["user_id", user.id, "eq"], ["active", True, "eq"]],
    )
    return query


def add_user_courses(
        db: Session,
        redis: Redis,
        telegram_id: int,
        user_course: AddUserCoursesSchema,
) -> UserCoursesSchema | None | UserCourseTracker:
    """
    Добавляет новый курс для пользователя по telegram_id.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        telegram_id (int): Telegram ID пользователя.
        user_course (AddUserCoursesSchema): Данные о новом курсе пользователя.

    Returns:
        UserCoursesSchema | None | UserCourseTracker: Объект добавленного курса пользователя,
        если добавление успешно; иначе None.
    """
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )

    course = get_course(
        db=db,
        redis=redis,
        course_id=user_course.course_id
    )

    cache = Cache(redis=redis, cache_key=f"active_user_courses:user:{user.id}", base_model=UserCoursesSchema)
    query = db.scalars(select(UserCourseTracker).filter_by(active=True, user_id=user.id)).first()
    if query is not None:
        query.active = False
        cache.delete_keys_by_pattern(pattern=f"unfinished_user_courses:user:{user.id}*")

    user_course = UserCourseTracker(
        user_id=user.id,
        course_id=course.id,
        title=course.title,
        current_module_id=course.stat_modul_id,
        current_sub_module_id=course.stat_sub_modul_id,
        current_stage=user_course.current_stage,
        plan=course.default_plan,
    )

    cache.delete_key()
    db.add(user_course)
    db.commit()
    db.refresh(user_course)
    cache.set(query=user_course)

    return user_course


def get_next_stage(
        db: Session,
        redis: Redis,
        user_course_id: int,
):
    """
    Определяет и возвращает следующую стадию курса пользователя.

    Функция последовательно проверяет текущую стадию курса пользователя и,
    в зависимости от её значения, определяет следующую стадию. Если текущая стадия
    курса завершена, функция переходит к следующему содержимому, следующему вопросу,
    следующему подмодулю или следующему модулю в зависимости от текущего состояния курса.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        user_course_id (int): ID курса пользователя

    Returns:
        dict: Словарь, содержащий следующую стадию курса и соответствующие данные.
        Если курс завершен, возвращается стадия "completed".

    Raises:
        HTTPException: Если курс пользователя не найден (404) или не активен (409).
    """
    user_course = get_user_course(db=db, redis=redis, user_course_id=user_course_id)
    current_stage = user_course.current_stage
    current_order_number = user_course.current_order_number
    if user_course is None:
        raise HTTPException(status_code=404, detail=f"User course`{user_course_id}` not found")
    if not user_course.active:
        raise HTTPException(status_code=409, detail=f"User course must be active")
    if current_stage == CurrentStage.education.value:
        next_content = get_module_content(
            db=db,
            redis=redis,
            sub_module_id=user_course.current_sub_module_id,
            order_number=user_course.current_order_number + 1,
            only_check=True,
            content_type=ContentType.text
        )
        if next_content:
            return {
                "stage": CurrentStage.education.value,
                "data": {
                    "current_module_id": user_course.current_module_id,
                    "current_sub_module_id": user_course.current_sub_module_id,
                    "current_order_number": next_content.order_number
                }
            }
        current_stage = CurrentStage.question.value
        current_order_number = 0
    if current_stage == CurrentStage.ask_question.value:
        return {
            "stage": CurrentStage.ask_question.value,
            "data": {
                "current_module_id": user_course.current_module_id,
                "current_sub_module_id": user_course.current_sub_module_id,
                "current_order_number": user_course.current_order_number
            }
        }
    if current_stage == CurrentStage.question.value:
        next_question = get_question(
            db=db,
            redis=redis,
            sub_module_id=user_course.current_sub_module_id,
            order_number=current_order_number + 1,
            only_check=True
        )
        if next_question:
            return {
                "stage": CurrentStage.question.value,
                "data": {
                    "current_module_id": user_course.current_module_id,
                    "current_sub_module_id": user_course.current_sub_module_id,
                    "current_order_number": next_question.order_number
                }
            }
    current_sub_module = get_sub_module_by_id(
        db=db,
        redis=redis,
        id=user_course.current_sub_module_id,
        only_check=True
    )
    next_sub_module = get_sub_module(
        db=db,
        redis=redis,
        module_id=user_course.current_module_id,
        order_number=current_sub_module.order_number + 1,
        only_check=True
    )
    if next_sub_module:
        next_content = get_module_content(
            db=db,
            redis=redis,
            sub_module_id=next_sub_module.id,
            order_number=1,
            only_check=True,
            content_type=ContentType.text
        )
        return {
            "stage": CurrentStage.education.value,
            "data": {
                "current_module_id": user_course.current_module_id,
                "current_sub_module_id": next_sub_module.id,
                "current_order_number": next_content.order_number
            }
        }

    current_module = get_module_by_id(
        db=db,
        redis=redis,
        id=user_course.current_module_id,
        only_check=True
    )
    next_module = get_module(
        db=db,
        redis=redis,
        course_id=user_course.course_id,
        order_number=current_module.order_number + 1,
        only_check=True
    )
    if next_module:
        next_sub_module = get_sub_module(
            db=db,
            redis=redis,
            module_id=next_module.id,
            order_number=1,
            only_check=True
        )
        if next_sub_module:
            next_content = get_module_content(
                db=db,
                redis=redis,
                sub_module_id=next_sub_module.id,
                order_number=1,
                only_check=True,
                content_type=ContentType.text
            )
            return {
                "stage": CurrentStage.education.value,
                "data": {
                    "current_module_id": next_module.id,
                    "current_sub_module_id": next_sub_module.id,
                    "current_order_number": next_content.order_number
                }
            }
    return {"stage": CurrentStage.completed.value}


def patch_user_courses(
        db: Session,
        redis: Redis,
        user_course_id: int,
        user_course: PatchUserCoursesSchema
) -> UserCoursesSchema | UserCourseTracker | None:
    """
    Обновляет информацию о курсе пользователя по его ID.

    Функция использует схему patch для обновления записи о курсе пользователя в базе данных и кэше.
    После успешного обновления соответствующие ключи в кэше удаляются.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        user_course_id (int): ID курса пользователя
        user_course (PatchUserCoursesSchema): Данные для обновления курса пользователя

    Returns:
        UserCoursesSchema | UserCourseTracker: Обновленный объект курса пользователя, если обновление успешно,
        иначе None.
    """
    user_course: UserCourseTracker | None = patch_record(
        db=db,
        redis=redis,
        identifier=user_course_id,
        sql_model=UserCourseTracker,
        filters=[["id", user_course_id, "eq"]],
        base_model=UserCoursesSchema,
        patch_schema=user_course,
        cache_key=f"user_course:id:{user_course_id}",
    )
    if user_course:
        cache = Cache(redis=redis)
        cache.delete_keys_by_pattern(pattern=f"active_user_courses:user:{user_course.user_id}*")
        cache.delete_keys_by_pattern(pattern=f"unfinished_user_courses:user:{user_course.user_id}*")
        cache.delete_keys_by_pattern(pattern=f"archived_user_courses:user:{user_course.user_id}*")
        cache.delete_keys_by_pattern(pattern=f"user_courses:user:{user_course.user_id}*")
    return user_course


def add_answers(
        db: Session,
        redis: Redis,
        telegram_id: int,
        answer: AddUserAnswersSchema

):
    user = get_user(
        db=db,
        redis=redis,
        telegram_id=telegram_id
    )
    answer = UserAnswers(
        user_id=user.id,
        question_id=answer.question_id,
        answer=answer.answer,
        score=answer.score,
        feedback=answer.feedback
    )
    record = add_record(
        db=db,
        redis=redis,
        record=answer,
        base_model=UserAnswersSchema,
        cache_key=f"user_answer:user_id:{user.id}:question_id:{answer.question_id}",
        ex=600
    )
    return record


def edit_stage_user_courses(
        db: Session,
        redis: Redis,
        user_course_id: int,
        edited_user_course: PatchUserCoursesSchema

):
    user_course = patch_record(
        db=db,
        redis=redis,
        identifier=user_course_id,
        sql_model=UserCourseTracker,
        filters=[["id", user_course_id, "eq"]],
        base_model=UserCoursesSchema,
        patch_schema=edited_user_course,
        cache_key=f"user_course:id:{user_course_id}",
    )

    cache = Cache(redis=redis)
    cache.delete_keys_by_pattern(pattern=f"active_user_courses:user:{user_course.user_id}*")
    cache.delete_keys_by_pattern(pattern=f"unfinished_user_courses:user:{user_course.user_id}*")
    cache.delete_keys_by_pattern(pattern=f"archived_user_courses:user:{user_course.user_id}*")
    return user_course


def archive_user_courses(

        db: Session,
        redis: Redis,
        user_course_id: int,
):
    user_course = get_user_course(
        db=db,
        redis=redis,
        user_course_id=user_course_id

    )
    usage_count = user_course.usage_count + 1
    edited_user_course = PatchUserCoursesSchema(
        archived=True,
        active=False,
        finished=True,
        usage_count=usage_count,
        current_stage=CurrentStage.completed
    )
    user_course = edit_stage_user_courses(
        db=db,
        redis=redis,
        user_course_id=user_course_id,
        edited_user_course=edited_user_course
    )
    return user_course


def pause_user_courses(

        db: Session,
        redis: Redis,
        user_course_id: int,
):
    edited_user_course = PatchUserCoursesSchema(archived=False, active=False, finished=False)

    user_course = edit_stage_user_courses(
        db=db,
        redis=redis,
        user_course_id=user_course_id,
        edited_user_course=edited_user_course
    )
    return user_course


def resume_user_courses(
        db: Session,
        redis: Redis,
        user_course_id: int,
):
    edited_user_course = PatchUserCoursesSchema(archived=False, active=True, finished=False)

    user_course = edit_stage_user_courses(
        db=db,
        redis=redis,
        user_course_id=user_course_id,
        edited_user_course=edited_user_course
    )
    return user_course


def restart_user_courses(
        db: Session,
        redis: Redis,
        user_course_id: int
):
    user_course = get_user_course(
        db=db,
        redis=redis,
        user_course_id=user_course_id

    )
    course = get_course(
        db=db,
        redis=redis,
        course_id=user_course.course_id
    )

    edited_user_course = PatchUserCoursesSchema(
        archived=False,
        active=True,
        finished=False,
        current_module_id=course.stat_modul_id,
        current_sub_module_id=course.stat_sub_modul_id,
        current_stage=CurrentStage.education,
        current_order_number=1,
        plan=course.default_plan
    )

    user_course = edit_stage_user_courses(
        db=db,
        redis=redis,
        user_course_id=user_course_id,
        edited_user_course=edited_user_course
    )
    return user_course
