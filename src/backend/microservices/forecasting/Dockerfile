######### Author: Pardis Ebrahimi ##########

FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip && \
    TMPDIR=/var/tmp pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8003"]
