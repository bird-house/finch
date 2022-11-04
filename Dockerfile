# vim:set ft=dockerfile:
FROM condaforge/mambaforge
MAINTAINER https://github.com/bird-house/finch
LABEL Description="Finch WPS" Vendor="Birdhouse" Version="0.9.2"

WORKDIR /code

COPY environment.yml .
RUN mamba env create -n finch -f environment.yml \
    && mamba install -n finch gunicorn psycopg2 \
    && mamba clean -ay

COPY . .

ENV PATH /opt/conda/envs/finch/bin:$PATH

EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "finch.wsgi:create_app()"]
