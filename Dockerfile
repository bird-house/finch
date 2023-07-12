# vim:set ft=dockerfile:
FROM condaforge/mambaforge
ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
LABEL org.opencontainers.image.authors="bourgault.pascal@ouranos.ca"
LABEL Description="Finch WPS" Vendor="Birdhouse" Version="0.11.1"

# Switch to /code directory
WORKDIR /code
COPY . ./

# Build finch environment
COPY environment.yml .
RUN mamba env create -n finch -f environment.yml
RUN mamba install -n finch gunicorn psycopg2
RUN mamba clean --all --yes

# Add the finch conda environment to the path
ENV PATH /opt/conda/envs/finch/bin:$PATH

RUN pip install . --no-deps

# Start WPS service on port 5000 of 0.0.0.0
EXPOSE 5000
CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "finch.wsgi:application"]
