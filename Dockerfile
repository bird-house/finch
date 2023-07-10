# vim:set ft=dockerfile:
FROM condaforge/mambaforge
ARG DEBIAN_FRONTEND=noninteractive
LABEL org.opencontainers.image.authors="bourgault.pascal@ouranos.ca"
LABEL Description="Finch WPS" Vendor="Birdhouse" Version="0.11.1"

# Switch to code directory
WORKDIR /code

# Build finch environment
COPY environment.yml .
RUN mamba env create -n finch -f environment.yml \
    && mamba install -n finch gunicorn psycopg2 \
    && mamba clean -ay

# Copy WPS project
COPY . .

# Add the finch conda environment to the path
ENV PATH /opt/conda/envs/finch/bin:$PATH

# Start WPS service on port 5000 of 0.0.0.0
EXPOSE 5000
CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "finch.wsgi:application"]
