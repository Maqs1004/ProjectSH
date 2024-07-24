import uvicorn
from fastapi import FastAPI
from app_api.db.base import Base
from app_api.db.session import engine
from fastapi.responses import JSONResponse
from app_api.core.logging_config import logger
from app_api.api.endpoints.promo.router import promo
from app_api.api.endpoints.users.router import users
from app_api.api.endpoints.other.router import others
from app_api.api.endpoints.courses.router import courses
from app_api.api.endpoints.prompts.router import prompts
from app_api.api.endpoints.gpt_models.router import models
from sqlalchemy_utils import database_exists, create_database
from app_api.api.endpoints.translation.router import translations
from app_api.api.endpoints.user_courses.router import user_courses

app = FastAPI(
    title="Skill Helper API",
    description="API для взаимодействия с обучением",
    version="1.0.0"
)
app.include_router(users)
app.include_router(models)
app.include_router(courses)
app.include_router(prompts)
app.include_router(promo)
app.include_router(translations)
app.include_router(others)
app.include_router(user_courses, prefix="/users")


@app.get(path="/")
def main():
    return JSONResponse(content={"SKILL HELPER API": "1.0.0"})


@app.get(path="/database/create")
def database():
    if not database_exists(engine.url):
        logger.info("Database does not exist and will be created.")
        create_database(engine.url)
        status = "created"
    else:
        logger.info("Database exists.")
        status = "exists"
    Base.metadata.create_all(engine)
    return JSONResponse(content={"database": status})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5011)
