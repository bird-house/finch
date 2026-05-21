# vim:set ft=dockerfile:
FROM condaforge/mambaforge
ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
LABEL org.opencontainers.image.authors="https://github.com/bird-house/finch"
LABEL Description="Finch WPS" Vendor="Birdhouse" Version="0.13.3-dev.2"

# Set the working directory to /code
WORKDIR /code

# Create conda environment
COPY environment.yml .
RUN mamba env create -n finch -f environment.yml && mamba install -n finch gunicorn && mamba clean --all --yes

# Add the project conda environment to the path
ENV PATH=/opt/conda/envs/finch/bin:$PATH

# Copy WPS project
COPY . /code

# Install WPS project
RUN pip install . --no-deps

# Start WPS service on port 5000 of 0.0.0.0
EXPOSE 5000

# Specify a non-root user to run the application
RUN useradd --create-home --shell /bin/bash --uid 1000 nonroot && mkdir -p /tmp/matplotlib && chown -R nonroot:nonroot /code /home/nonroot /tmp/matplotlib /opt/conda/envs/finch
USER nonroot
ENV MPLCONFIGDIR=/tmp/matplotlib

CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "finch.wsgi:application"]
