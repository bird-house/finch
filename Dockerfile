# vim:set ft=dockerfile:
FROM continuumio/miniconda3
MAINTAINER https://github.com/bird-house/finch
LABEL Description="Finch WPS" Vendor="Birdhouse" Version="0.9.1"

# Update Debian system
RUN apt-get update && apt-get install -y \
    build-essential git \
    && rm -rf /var/lib/apt/lists/* \
    && conda update conda -n base \
    && conda install mamba -n base -c conda-forge -c defaults

WORKDIR /code

COPY environment.yml .
RUN conda config --add channels conda-forge \
    && mamba env create -n finch -f environment.yml \
    && mamba install -c conda-forge -n finch gunicorn psycopg2 \
    && rm -rf /opt/conda/pkgs/*

COPY . .

ENV PATH /opt/conda/envs/finch/bin:$PATH

EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "finch.wsgi:application"]
