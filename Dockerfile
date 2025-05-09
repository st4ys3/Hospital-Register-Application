FROM python:3.10

RUN apt update && apt install -y default-mysql-client git && apt clean && apt-get install -y cron 

WORKDIR /app

COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/crontab.sh

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

ENTRYPOINT ["/app/crontab.sh"]