FROM python:3.11-buster

WORKDIR /app

RUN mkdir /data/ && rm -rf /var/lib/apt/lists/*

RUN ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime


RUN pip install --default-timeout=120 --upgrade pip -i https://mirrors.aliyun.com/pypi/simple

COPY ./requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt && rm -f requirements.txt

RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/

ADD . /app

EXPOSE 7890

CMD ["/bin/sh", "entrypoint.sh"]
