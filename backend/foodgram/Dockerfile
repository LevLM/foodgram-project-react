FROM python:3.7-slim
WORKDIR /app
COPY . .
RUN pip3 install -r ./requirements.txt --no-cache-dir
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]
ONBUILD RUN python manage.py migrate
ONBUILD RUN python manage.py collectstatic --noinput
