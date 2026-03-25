# FROM continuumio/miniconda3.11
FROM continuumio/miniconda3:latest
WORKDIR /app
RUN pip install pre-commit
RUN apt-get update && apt-get install -y git


ADD ./scripts/setup.sh /app/scripts/setup.sh
ADD ./requirements.txt /app/requirements.txt

# RUN bash scripts/setup.sh

RUN pip install -r requirements.txt
ADD ./ /app
CMD ["bash", "./scripts/run.sh"]