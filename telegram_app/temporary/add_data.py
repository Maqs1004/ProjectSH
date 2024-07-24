import json
import os

import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_locales(API_URL: str):
    current_directory = os.getcwd()
    full_path = os.path.join(current_directory, "temporary/locale.json")
    logger.info(full_path)
    locales = json.load(open(full_path, "rb"))
    for message_key, languages in locales.items():
        for language_code, message_text in languages.items():
            data = {
                "message_key": message_key,
                "language_code": language_code,
                "message_text": message_text,
            }
            response = requests.post(f"{API_URL}/translation", json=data)
            if response.status_code == 200:
                logger.info(f"Successfully added {language_code} to {message_key}")
            elif response.status_code == 409:
                logger.info(f"Language {language_code} already exists")
            else:
                logger.error(f"Error adding {language_code} to {message_key}")


def add_models(API_URL: str):
    current_directory = os.getcwd()
    full_path = os.path.join(current_directory, "temporary/models.json")
    logger.info(full_path)
    models = json.load(open(full_path, "rb"))
    for model, info in models.items():
        response = requests.post(f"{API_URL}/models/{model}", json=info)
        if response.status_code == 200:
            logger.info(f"Successfully added {model}")
        elif response.status_code == 409:
            logger.info(f"Model {model} already exists")
        else:
            logger.error(f"Error adding {model}")


def add_instructions(API_URL: str):
    current_directory = os.getcwd()
    full_path = os.path.join(current_directory, "temporary/instructions.json")
    logger.info(full_path)
    instructions = json.load(open(full_path, "rb"))
    for instruction_key, data in instructions.items():
        response = requests.post(f"{API_URL}/prompts/{instruction_key}", json=data)
        if response.status_code == 200:
            logger.info(f"Successfully added {instruction_key}")
        elif response.status_code == 409:
            logger.info(f"Prompt {instruction_key} already exists")
        else:
            logger.error(f"Error adding {instruction_key}")
