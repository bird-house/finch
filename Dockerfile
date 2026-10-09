# vim:set ft=dockerfile:
FROM condaforge/miniforge3
ARG DEBIAN_FRONTEND=noninteractive
ENV PIP_ROOT_USER_ACTION=ignore
LABEL org.opencontainers.image.authors="Birdhouse and Ouranosinc"
LABEL org.opencontainers.image.created="2026-10-09T05:34:42Z"
LABEL org.opencontainers.image.description="Finch WPS"
LABEL org.opencontainers.image.source="https://github.com/bird-house/finch"
LABEL org.opencontainers.image.title="FinchWPS"
LABEL org.opencontainers.image.vendor="Birdhouse"
LABEL org.opencontainers.image.version="0.14.0"

# Specify a non-root user to run the application
RUN useradd --create-home --shell /bin/bash --uid 1001 nonroot && mkdir -p /tmp/matplotlib && chown -R nonroot:nonroot /tmp/matplotlib

# Create conda environment (root-owned is fine, nonroot just needs read access)
COPY environment.yml .
RUN mamba env create -n finch -f environment.yml && \
    mamba clean --all --yes

# Add the project conda environment to the path
ENV PATH="/opt/conda/envs/finch/bin:$PATH"

# For pyproj, to avoid error "PROJ: proj_create_from_database: Open of /opt/conda/envs/finch/share/proj failed"
ENV PROJ_DATA="/opt/conda/envs/finch/share/proj"

# Copy WPS project
COPY --chown=nonroot:nonroot . /code

# Set the working directory to /code
# Must setup after copy to inherit user permissions
WORKDIR /code

# Install WPS project
RUN conda run -n finch pip install --no-cache-dir . --no-deps

# Start WPS service on port 5000 of 0.0.0.0
EXPOSE 5000

USER nonroot
ENV MPLCONFIGDIR=/tmp/matplotlib

# Align finch config and PID locations
ENV FINCH_WORKDIR=/home/nonroot/finch

CMD ["gunicorn", "--bind=0.0.0.0:5000", "-t 60", "finch.wsgi:application"]
# docker build -t birdhouse/finch .
# docker run -p 5000:5000 birdhouse/finch
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
