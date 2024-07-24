import random
import threading
from typing import Type
from redis import Redis
from sqlalchemy import select
from collections import Counter
from sqlalchemy.orm import Session, scoped_session

from app_api.db.storage import download_file_from_url, upload_file
from app_api.gpt_server.openai_api import LLM
from app_api.db.session import SessionLocal
from app_api.models.education import CurrentStage
from concurrent.futures import ThreadPoolExecutor
from app_api.models.education import UserCourseTracker
from app_api.api.endpoints.prompts.crud import get_prompt
from ..prompts.schemas import PromptsSchema
from ...dependencies import get_record, Cache, patch_record
from app_api.api.endpoints.gpt_models.crud import get_model_by_id
from app_api.api.endpoints.user_courses.schemas import UserCoursesSchema
from app_api.models.education import Courses, Modules, SubModules, ModuleContents, Questions, QuestionType, ContentType
from .schemas import (CreateCoursePlanSchema, CourseSchema, ModulesSchema, SubModulesSchema, ModuleContentsSchema,
                      QuestionsSchema, PatchCourseSchema)


def add_course_data(
        db: Session,
        create_course: CreateCoursePlanSchema,
        course_data: dict,
        redis: Redis
) -> Courses:
    """
    Добавляет данные курса, включая модули, подмодули и содержимое, в базу данных и кэш Redis.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных
        create_course (CreateCoursePlanSchema): Схема для создания курса, содержащая заголовок и описание курса
        course_data (dict): Словарь, содержащий данные курса, организованные по модулям и подмодулям
        redis (Redis): Клиент Redis для кэширования данных

    Returns:
        Courses: Объект курса, добавленный в базу данных.
    """
    course = Courses(title=create_course.title, summary=create_course.summary)
    db.add(course)
    db.flush()
    default_plan = {"modules": []}
    module_order = 0
    first_module_id = None
    first_sub_module_id = None
    for module_title, modules in course_data.items():
        module_order += 1
        module_cache_key = f"module:order_number:{module_order}:course_id:{course.id}"
        module_cache = Cache(redis=redis, cache_key=module_cache_key, base_model=ModulesSchema)
        module = Modules(title=module_title, order_number=module_order, course_id=course.id)
        db.add(module)
        db.flush()
        module_cache.set(query=module, ex=259200)
        if first_module_id is None:
            first_module_id = module.id
        module_plan = {"module_id": module.id, "completed": False, "sub_modules": []}
        sub_module_order = 0
        for module_info in modules:
            for sub_title, topics in module_info.items():
                sub_module_order += 1
                sub_module_cache_key = f"sub_module:order_number:{sub_module_order}:module_id:{module.id}"
                sub_module_cache = Cache(redis=redis, cache_key=sub_module_cache_key, base_model=SubModulesSchema)
                sub_module = SubModules(title=sub_title, order_number=sub_module_order, module_id=module.id)
                db.add(sub_module)
                db.flush()
                sub_module_cache.set(query=sub_module, ex=259200)
                if first_sub_module_id is None:
                    first_sub_module_id = sub_module.id
                sub_module_plan = {"sub_module_id": sub_module.id, "completed": False, "contents": []}
                content_order = 0
                for topic in topics:
                    content_order += 1
                    content = ModuleContents(title=topic, order_number=content_order, sub_module_id=sub_module.id)
                    db.add(content)
                    db.flush()  # Получаем ID содержимого
                    content_plan = {"content_id": content.id, "completed": False}
                    sub_module_plan["contents"].append(content_plan)
                module_plan["sub_modules"].append(sub_module_plan)
        default_plan["modules"].append(module_plan)
    course.stat_modul_id = first_module_id
    course.stat_sub_modul_id = first_sub_module_id
    course.default_plan = default_plan
    db.commit()
    return course


def get_course(
        db: Session,
        redis: Redis,
        course_id: int,
        only_check=False,
) -> CourseSchema | None | Courses:
    """
    Извлекает информацию о курсе по его ID.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных
        redis (Redis): Клиент Redis для доступа к кэшу
        course_id (int): ID курса
        only_check (bool): Флаг, указывающий, нужно ли только проверить наличие записи (по умолчанию False)

    Returns:
        CourseSchema | None | Courses: Схема курса, если найдена, иначе None.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=Courses,
        base_model=CourseSchema,
        identifier=course_id,
        only_check=only_check,
        cache_key="course:id",
        filters=[["id", course_id, "eq"]],
    )
    return query


def get_module(
        db: Session,
        redis: Redis,
        course_id: int,
        order_number: int,
        only_check: bool,
) -> ModulesSchema:
    """
    Извлекает модуль по указанным параметрам курса и порядковому номеру.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        course_id (int): ID курса.
        order_number (int): Порядковый номер модуля в курсе.
        only_check (bool): Флаг, указывающий, нужно ли только проверить наличие записи.

    Returns:
        ModulesSchema: Схема модуля, соответствующая указанным параметрам.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=Modules,
        base_model=ModulesSchema,
        identifier=course_id,
        only_check=only_check,
        cache_key=f"module:order_number:{order_number}:course_id",
        filters=[["course_id", course_id, "eq"], ["order_number", order_number, "eq"]]
    )
    return query


def get_module_by_id(
        db: Session,
        redis: Redis,
        id: int,
        only_check: bool,
) -> ModulesSchema:
    """
    Извлекает модуль по его ID.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        id (int): ID модуля.
        only_check (bool): Флаг, указывающий, нужно ли только проверить наличие записи.

    Returns:
        ModulesSchema: Схема модуля, соответствующая указанным параметрам.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=Modules,
        base_model=ModulesSchema,
        identifier=id,
        only_check=only_check,
        cache_key=f"module:id",
        filters=[["id", id, "eq"]]
    )
    return query


def get_sub_module_by_id(
        db: Session,
        redis: Redis,
        id: int,
        only_check: bool
) -> SubModulesSchema:
    """
    Извлекает подмодуль по его ID.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        id (int): ID подмодуля.
        only_check (bool): Флаг, указывающий, нужно ли только проверить наличие записи.

    Returns:
        SubModulesSchema: Схема подмодуля, соответствующая указанным параметрам.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=SubModules,
        base_model=SubModulesSchema,
        identifier=id,
        only_check=only_check,
        cache_key=f"sub_module:id",
        filters=[["id", id, "eq"]]
    )
    return query


def get_sub_module(
        db: Session,
        redis: Redis,
        module_id: int,
        order_number: int,
        only_check: bool
) -> SubModulesSchema:
    """
    Извлекает подмодуль по указанным параметрам модуля и порядковому номеру.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        module_id (int): ID модуля.
        order_number (int): Порядковый номер подмодуля в модуле.
        only_check (bool): Флаг, указывающий, нужно ли только проверить наличие записи.

    Returns:
        SubModulesSchema: Схема подмодуля, соответствующая указанным параметрам.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=SubModules,
        base_model=SubModulesSchema,
        identifier=module_id,
        only_check=only_check,
        cache_key=f"sub_module:order_number:{order_number}:module_id",
        filters=[["module_id", module_id, "eq"], ["order_number", order_number, "eq"]]
    )
    return query


def get_module_content(
        db: Session,
        redis: Redis,
        content_type: ContentType,
        sub_module_id: int,
        order_number: int,
        only_check: bool = False,
) -> ModuleContentsSchema:
    """
    Извлекает содержимое модуля по указанным параметрам.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        content_type (ContentType): Тип контента (текст или изображение).
        sub_module_id (int): ID подмодуля.
        order_number (int): Порядковый номер контента в подмодуле.
        only_check (bool): Флаг, указывающий, нужно ли только проверить наличие записи (по умолчанию False).

    Returns:
        ModuleContentsSchema: Схема содержимого модуля, соответствующая указанным параметрам.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=ModuleContents,
        base_model=ModuleContentsSchema,
        identifier=sub_module_id,
        only_check=only_check,
        cache_key=f"module_content:order_number:{order_number}:sub_module_id:content_type:{content_type}",
        filters=[["sub_module_id", sub_module_id, "eq"], ["order_number", order_number, "eq"],
                 ["content_type", content_type, "eq"]]
    )
    return query


def get_question(
        db: Session,
        redis: Redis,
        sub_module_id: int,
        order_number: int,
        only_check: bool = False,
) -> QuestionsSchema:
    """
    Извлекает вопрос по указанным параметрам.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных.
        redis (Redis): Клиент Redis для доступа к кэшу.
        sub_module_id (int): ID подмодуля.
        order_number (int): Порядковый номер вопроса в подмодуле.
        only_check (bool): Флаг, указывающий, нужно ли только проверить наличие записи (по умолчанию False).

    Returns:
        QuestionsSchema: Схема вопроса, соответствующая указанным параметрам.
    """
    query = get_record(
        db=db,
        redis=redis,
        sql_model=Questions,
        base_model=QuestionsSchema,
        identifier=sub_module_id,
        only_check=only_check,
        cache_key=f"get_question:order_number:{order_number}:sub_module_id",
        filters=[["sub_module_id", sub_module_id, "eq"], ["order_number", order_number, "eq"]]
    )
    return query


def update_content_data_and_questions(
        course_title: str,
        summary: str,
        language: str,
        first_time: bool,
        sub_module: Type[SubModules] | SubModules,
        redis: Redis,
        gpt: LLM,
        ScopedSession: scoped_session
):
    """
    Обновляет данные контента и вопросы для указанного подмодуля курса.

    Функция генерирует текстовый и изображенный контент для подмодуля курса,
    а также создаёт вопросы с несколькими вариантами ответа и открытые вопросы,
    используя GPT-модель.

    Args:
        course_title (str): Название курса
        summary (str): Краткое содержание ответов пользователя о курсе
        language (str): Язык контента
        first_time (bool): Флаг, указывающий, генерируется ли контент в первый раз
        sub_module (Type[SubModules] | SubModules): Объект подмодуля, для которого генерируется контент
        redis (Redis): Клиент Redis для кэширования данных
        gpt (LLM): Объект LLM для генерации контента и вопросов
        ScopedSession (scoped_session): Скоуп сессия для работы с базой данных

    Returns:
        dict: Словарь с информацией о затратах, потраченных и выходных токенах.
    """
    session = ScopedSession()
    query = select(ModuleContents).order_by(ModuleContents.order_number.desc())
    query = query.filter_by(sub_module_id=sub_module.id)
    module_contents = session.execute(query).scalars().all()
    generated_contents = []
    previews_sections = []
    spent_amount = 0
    input_token = 0
    output_token = 0
    prompt_content = get_prompt(db=session, redis=redis, name="generate_module_content")
    generate_prompt = get_prompt(db=session, redis=redis, name="generate_prompt")
    generate_image = get_prompt(db=session, redis=redis, name="generate_image")
    model_image = get_model_by_id(db=session, redis=redis, model_id=generate_image.gpt_model_id)
    model_prompt = get_model_by_id(db=session, redis=redis, model_id=generate_prompt.gpt_model_id)
    model_content = get_model_by_id(db=session, redis=redis, model_id=prompt_content.gpt_model_id)
    for content in module_contents:
        content_cache_key = f"module_content:order_number:{content.order_number}:sub_module_id:{content.sub_module_id}"
        text_content_cache_key = f"{content_cache_key}:content_type:{ContentType.text}"
        content_cache = Cache(redis=redis, cache_key=text_content_cache_key, base_model=ModuleContentsSchema)
        generated_content = gpt.generate_module_content(
            user_content=prompt_content.user,
            system_content=prompt_content.system,
            course_title=course_title,
            sub_module_title=sub_module.title,
            content_title=content.title,
            previews_sections=previews_sections,
            is_first_time=first_time,
            summary=summary,
            model=model_content,
            language=language
        )
        first_time = False
        spent_amount += generated_content.spent_amount
        input_token += generated_content.input_tokens
        output_token += generated_content.output_tokens
        content.content_data = generated_content.content["response"]
        content.content_type = ContentType.text
        session.add(content)
        session.flush()
        generated_contents.append(generated_content.content["response"])
        previews_sections.append(content.title)
        content_cache.set(query=content, ex=259200)
        image_content_cache_key = f"{content_cache_key}:content_type:{ContentType.image}"
        content_cache = Cache(redis=redis, cache_key=image_content_cache_key, base_model=ModuleContentsSchema)
        generate_prompt_image = gpt.generate_prompt(
            system_content=generate_prompt.system,
            user_content=generate_prompt.user,
            content_title=course_title,
            sub_module_title=sub_module.title,
            course_title=content.title,
            model=model_prompt
        )
        spent_amount += generate_prompt_image.spent_amount
        input_token += generate_prompt_image.input_tokens
        output_token += generate_prompt_image.output_tokens
        url_image = gpt.generate_image(prompt=generate_prompt_image.content["prompt"], model=model_image)
        image = download_file_from_url(url_image)
        fid = upload_file(image)
        image_content = ModuleContents(
            sub_module_id=content.sub_module_id,
            title=content.title,
            content_type=ContentType.image,
            content_data={"fid": fid},
            order_number=content.order_number
        )
        session.add(image_content)
        session.flush()
        spent_amount += 0.04
        content_cache.set(query=image_content, ex=259200)
    prompt_multiple_choice = get_prompt(db=session, redis=redis, name="generate_multiple_choice_question")
    model_multiple_choice = get_model_by_id(db=session, redis=redis, model_id=prompt_multiple_choice.gpt_model_id)
    question_order_number = 0
    for generated_content in generated_contents:
        question_order_number += 1
        mc_questions = gpt.generate_multiple_choice_question(
            content=generated_content,
            model=model_multiple_choice,
            user_content=prompt_multiple_choice.user,
            language=language
        )
        spent_amount += mc_questions.spent_amount
        input_token += mc_questions.input_tokens
        output_token += mc_questions.output_tokens
        question = Questions(
            sub_module_id=sub_module.id,
            content=mc_questions.content["question"],
            question_type=QuestionType.multiple_choice,
            options=mc_questions.content["answers"],
            order_number=question_order_number
        )
        question_cache_key = f"question:order_number:{question.order_number}:sub_module_id:{sub_module.id}"
        question_cache = Cache(redis=redis, cache_key=question_cache_key, base_model=QuestionsSchema)
        session.add(question)
        session.flush()
        question_cache.set(query=question, ex=259200)
    prompt_open = get_prompt(db=session, redis=redis, name="generate_open_question")
    model_open = get_model_by_id(db=session, redis=redis, model_id=prompt_open.gpt_model_id)
    random_content = random.choice(generated_contents)
    open_question_content = gpt.generate_open_question(
        content=random_content,
        user_content=prompt_open.user,
        model=model_open,
        language=language

    )
    spent_amount += open_question_content.spent_amount
    input_token += open_question_content.input_tokens
    output_token += open_question_content.output_tokens
    open_question = Questions(
        sub_module_id=sub_module.id,
        content=open_question_content.content["question"],
        question_type=QuestionType.open,
        order_number=question_order_number + 1
    )
    question_cache_key = f"question:order_number:{open_question.order_number}:sub_module_id:{sub_module.id}"
    question_cache = Cache(redis=redis, cache_key=question_cache_key, base_model=QuestionsSchema)
    session.add(open_question)
    session.flush()
    question_cache.set(query=open_question, ex=259200)
    session.commit()
    return {"spent_amount": spent_amount, "input_token": input_token, "output_token": output_token}


def generate_main_content(
        db: Session,
        language: str,
        course: CourseSchema,
        redis: Redis,
        gpt: LLM
):
    """
    Генерирует основной контент курса, обновляет и сохраняет его в базу данных и кэш.

    Функция обновляет состояние курса на "недоступно" до завершения генерации контента.
    Генерируется текстовый контент и изображения, а также создаются вопросы для каждого
    подмодуля курса. Вся информация сохраняется в базу данных и кэш.

    Args:
        db (Session): Сессия SQLAlchemy для доступа к базе данных
        language (str): Язык контента
        course (CourseSchema): Схема курса, для которого генерируется контент
        redis (Redis): Клиент Redis для кэширования данных
        gpt (LLM): Объект LLM для генерации контента и вопросов
    """
    course_patch = PatchCourseSchema(available=False)
    patch_record(
        db=db,
        redis=redis,
        identifier=course.id,
        sql_model=Courses,
        filters=[["id", course.id, "eq"]],
        base_model=CourseSchema,
        patch_schema=course_patch,
        cache_key=f"course:id:{course.id}",
    )
    costs = []
    sub_modules = db.query(SubModules).filter(SubModules.module.has(course_id=course.id)).order_by(SubModules.id).all()
    ScopedSession = scoped_session(SessionLocal)
    first_time = True
    with ThreadPoolExecutor() as executor:
        futures = []
        for sub_module in sub_modules:
            futures.append(executor.submit(
                update_content_data_and_questions,
                course_title=course.title,
                summary=course.summary,
                sub_module=sub_module,
                redis=redis,
                language=language,
                gpt=gpt,
                first_time=first_time,
                ScopedSession=ScopedSession
            )
            )
            first_time = False
        for future in futures:
            costs.append(future.result())
    course_patch = PatchCourseSchema(is_generated=True, available=True)
    patch_record(
        db=db,
        redis=redis,
        identifier=course.id,
        sql_model=Courses,
        filters=[["id", course.id, "eq"]],
        base_model=CourseSchema,
        patch_schema=course_patch,
        cache_key=f"course:id:{course.id}",
    )
    total = sum((Counter(item) for item in costs), Counter())
    query = select(UserCourseTracker).filter_by(course_id=course.id)
    user_course = db.scalars(query).first()
    user_course.current_stage = CurrentStage.generated
    user_course.input_token = total["input_token"]
    user_course.output_token = total["output_token"]
    user_course.spent_amount = total["spent_amount"]
    db.commit()
    db.refresh(user_course)
    cache = Cache(redis=redis, cache_key=f"user_course:id:{user_course.id}", base_model=UserCoursesSchema)
    cache.delete_key()
    cache.set(query=user_course, ex=259200)
    cache.delete_keys_by_pattern(pattern=f"archived_user_courses:user:{user_course.user_id}*")
    cache.delete_keys_by_pattern(pattern=f"unfinished_user_courses:user:{user_course.user_id}*")
    cache.delete_keys_by_pattern(pattern=f"active_user_courses:user:{user_course.user_id}*")
    cache.delete_keys_by_pattern(pattern=f"user_courses:user:{user_course.user_id}*")
    return user_course


def generate_main_content_threading(
        db: Session,
        course: CourseSchema,
        redis: Redis,
        gpt: LLM
):
    main_thread = threading.Thread(target=generate_main_content, args=(db, course, redis, gpt))
    main_thread.start()
