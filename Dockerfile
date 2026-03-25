FROM continuumio/miniconda3:latest
WORKDIR /app

RUN apt-get update && apt-get install -y git build-essential && apt-get clean

ADD ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ADD ./ /app

EXPOSE 8000

CMD ["bash", "./scripts/run.sh"]