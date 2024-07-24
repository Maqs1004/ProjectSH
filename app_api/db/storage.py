import requests
from app_api.core.config import setting
from app_api.core.logging_config import logger


def download_file_from_url(url: str) -> bytes | None:
    """
    Скачивает файл по указанному URL.

    Args:
        url (str): URL для скачивания файла.

    Returns:
        bytes | None: Содержимое файла в виде байтов, если загрузка успешна, иначе None.

    Raises:
        requests.RequestException: Если возникает ошибка при выполнении запроса.
    """
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        logger.info(f"File downloaded from {url[:30]}...")
        return response.content
    else:
        logger.error(f"Failed to download file from {url[:30]}...")
        return None


def upload_file(file_content: bytes) -> str | None:
    """
    Загружает файл в систему SeaweedFS.

    Args:
        file_content (bytes): Содержимое файла для загрузки.

    Returns:
        str | None: Идентификатор загруженного файла (fid), если загрузка успешна, иначе None.

    Raises:
        requests.RequestException: Если возникает ошибка при выполнении запроса.
        KeyError: Если в ответе сервера отсутствует ключ 'fid'.
    """
    response = requests.get(f"{setting.SEAWEEDFS_MASTER_URL}/dir/assign")
    fid_info = response.json()
    fid = fid_info['fid']
    upload_url = f"{setting.SEAWEEDFS_VOLUME_URL}/{fid}"
    upload_response = requests.post(upload_url, files={'file': ('uploaded_file', file_content)})

    if upload_response.status_code == 201:
        logger.info("File uploaded successfully")
        return fid
    else:
        logger.error("Failed to upload file")
