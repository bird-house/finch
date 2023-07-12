# vim:set ft=dockerfile:
FROM condaforge/mambaforge
ARG DEBIAN_FRONTEND=noninteractive
LABEL org.opencontainers.image.authors="bourgault.pascal@ouranos.ca"
LABEL Description="Finch WPS" Vendor="Birdhouse" Version="0.11.1"

# Switch to /code directory
WORKDIR /code
COPY . ./

# Build finch environment
COPY environment.yml .
RUN mamba env create -n finch -f environment.yml
RUN mamba install -n gunicorn psycopg2
RUN pip install -e . --no-deps
RUN mamba clean --all --yes

# Add the finch conda environment to the path
ENV PATH /opt/conda/envs/finch/bin:$PATH

# Start WPS service on port 5000 of 0.0.0.0
EXPOSE 5000
CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "finch.wsgi:application"]
