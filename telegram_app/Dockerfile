FROM python:3.11-slim

RUN apt-get update &&  apt-get install -y build-essential libpq-dev nginx && apt-get clean
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app
COPY . .
CMD ["python", "-m", "main"]