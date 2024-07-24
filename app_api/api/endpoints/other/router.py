from redis import Redis
from sqlalchemy.orm import Session
from app_api.db.session import get_db
from fastapi import APIRouter, Depends, Path
from app_api.db.redis_connection import get_redis
from app_api.gpt_server.openai_api import LLM
from app_api.gpt_server.validation import ContentAnswerResponse
from .schemas import SummarizeSchema, SurveySchema, GenerateImageSchema, ContentQuestionSchema
from ..gpt_models.crud import get_model_by_id, get_model
from ..prompts.crud import get_prompt
from ..user_courses.crud import get_user_course, patch_user_courses
from ..user_courses.schemas import PatchUserCoursesSchema

others = APIRouter(prefix="/other", tags=["Other"])


@others.post(path="/summarize",
             response_model=SummarizeSchema,
             summary="Сумаризирует вопросы и ответа пользователя в единое целое"
             )
def other_route(survey: SurveySchema,
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Сумаризирует вопросы и ответа пользователя в единое целое

    Этот эндпоинт получает вопросы и ответы пользователя, которые ему были заданы и приводит это к небольшому
    описанию о нем.


    ### Параметры
    - `name` (str): Имя модели.

    ### Возвращает
    - `SummarizeSchema`: Схема данных сумаризации

    """
    prompt = get_prompt(db=db, redis=redis, name="summarize_answers")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    response = gpt.summarize_answers(personal_question=survey.data, model=model, user_content=prompt.user,
                                     system_content=prompt.system)
    return response.content


@others.post(path="/get-answer",
             response_model=ContentAnswerResponse,
             summary="Получает ответ по вопросу пользователя"
             )
def other_route(question: ContentQuestionSchema,
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    """
    Получает ответ заданного пользователем по пройденному материалу
    """
    prompt = get_prompt(db=db, redis=redis, name="generate_content_answers")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    response = gpt.generate_content_answers(
        model=model,
        user_content=prompt.user,
        system_content=prompt.system,
        content=question.content,
        language=question.language,
        history=question.history
    )
    user_course = get_user_course(db=db, redis=redis, user_course_id=question.user_course_id)
    patch_course = PatchUserCoursesSchema(
        input_token=user_course.input_token + response.input_tokens,
        output_token=user_course.output_token + response.output_tokens,
        spent_amount=user_course.spent_amount + response.spent_amount,
    )
    patch_user_courses(db=db, redis=redis, user_course_id=question.user_course_id, user_course=patch_course)
    return response.content


@others.post(path="/generate-image",
             summary="Генерирует изображение для курса"
             )
def other_route(image: GenerateImageSchema,
                db: Session = Depends(get_db),
                redis: Redis = Depends(get_redis)
                ):
    prompt = get_prompt(db=db, redis=redis, name="generate_prompt")
    model = get_model_by_id(db=db, redis=redis, model_id=prompt.gpt_model_id)
    gpt = LLM()
    response_prompt = gpt.generate_prompt(
        system_content=prompt.system,
        user_content=prompt.user,
        course_title=image.course_title,
        sub_module_title=image.sub_module_title,
        content_title=image.content_title,
        model=model,

    )
    model_dall_e = get_model(db=db, redis=redis, name="DALL-E 3")
    response_url = gpt.generate_image(
        model=model_dall_e,
        prompt=response_prompt.content["prompt"],
        size=image.size,
        quality=image.quality
    )
    return {"url": response_url}
