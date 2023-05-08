FROM python:3.11-slim

WORKDIR /app

RUN apt install tzdata
RUN echo "Asia/Seoul" > /etc/timezone; \
    echo "Asia/Seoul" > /etc/localtime
ENV TZ=Asia/Seoul

COPY . .
RUN pip install cryptography
RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "index.py"]
