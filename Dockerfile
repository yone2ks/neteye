FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=manage.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_DEBUG=1

ENV NET_TEXTFSM=/app/ntc-templates/ntc_templates/templates/

CMD ["python", "manage.py"]

