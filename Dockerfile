# vim:set ft=dockerfile:
FROM condaforge/miniforge3
ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
LABEL org.opencontainers.image.authors="Birdhouse and Ouranosinc"
LABEL org.opencontainers.image.created="2026-07-30T20:37:38Z"
LABEL org.opencontainers.image.description="Finch WPS"
LABEL org.opencontainers.image.source="https://github.com/bird-house/finch"
LABEL org.opencontainers.image.title="FinchWPS"
LABEL org.opencontainers.image.vendor="Birdhouse"
LABEL org.opencontainers.image.version="0.13.3-dev.5"

# Set the working directory to /code
WORKDIR /code

# Create conda environment
COPY environment.yml .
RUN mamba env create -n finch -f environment.yml && \
    mamba install -n finch -c conda-forge gunicorn && \
    mamba clean --all --yes

# Add the project conda environment to the path
ENV PATH="/opt/conda/envs/finch/bin:$PATH"

# For pyproj, to avoid error "PROJ: proj_create_from_database: Open of /opt/conda/envs/finch/share/proj failed"
ENV PROJ_DATA="/opt/conda/envs/finch/share/proj"

# Copy WPS project
COPY . /code

# Install WPS project
RUN conda run -n finch pip install --no-cache-dir . --no-deps

# Start WPS service on port 5000 of 0.0.0.0
EXPOSE 5000

# Specify a non-root user to run the application
RUN useradd --create-home --shell /bin/bash --uid 1001 nonroot && \
    mkdir -p /tmp/matplotlib && \
    chown -R nonroot:nonroot /code /home/nonroot /tmp/matplotlib /opt/conda/envs/finch
USER nonroot
ENV MPLCONFIGDIR=/tmp/matplotlib

CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "finch.wsgi:application"]
# docker build -t birdhouse/finch .
# docker run -p 5000:5000 birdhouse/finch
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
