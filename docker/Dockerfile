FROM python:3-alpine

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY src /app
WORKDIR /app

CMD ["python", "cloudflare_rdns.py"]
