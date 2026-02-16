FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Сначала копируем весь проект
COPY . /app

# Ставим зависимости.
# Если у тебя зависимости описаны в pyproject.toml, то pip установит их.
RUN pip install --upgrade pip \
 && pip install .

CMD ["python", "-m", "pigeon_mail_bot.main"]
