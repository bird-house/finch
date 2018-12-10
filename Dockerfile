# vim:set ft=dockerfile:
FROM continuumio/miniconda3
MAINTAINER https://github.com/bird-house/finch
LABEL Description="Finch WPS" Vendor="Birdhouse" Version="0.1.0"

# Update Debian system
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Update conda
RUN conda update -n base conda

WORKDIR /opt/wps
ARG pythonpath=/opt/python

# Create conda environment
COPY environment.yml /opt/wps/environment.yml
RUN conda env create -p ${pythonpath} -f environment.yml \
    # Install gunicorn to use as a production server
    && conda install -p ${pythonpath} gunicorn psycopg2 \
    && rm -rf /opt/conda/pkgs/*

## Add conda environent to the PATH. No need to activate the environment.
ENV PATH ${pythonpath}/bin:$PATH

# Copy WPS project
COPY . .

RUN python setup.py develop

RUN mkdir -p /data/wpsoutputs

EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "finch.wsgi:application"]

# docker build -t bird-house/finch .
# docker run -p 5000:5000 bird-house/finch
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
