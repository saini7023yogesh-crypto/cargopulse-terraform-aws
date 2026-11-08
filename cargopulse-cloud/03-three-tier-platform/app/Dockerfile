FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
RUN groupadd -r app && useradd -r -g app app
WORKDIR /srv/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
USER app
EXPOSE 8000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-"]
