FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/app

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8066", "-k", "uvicorn.workers.UvicornWorker", "app.api_app:api_app"]