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

# Create conda environment
COPY environment.yml /opt/wps/environment.yml
RUN conda env create -n wps -f environment.yml \
    && rm -rf /opt/conda/pkgs/*

# Copy WPS project
COPY . /opt/wps

# Add wps environent to the PATH. No need to activate the environment.
ENV PATH /opt/conda/envs/wps/bin:$PATH

RUN python setup.py install


EXPOSE 5000

ENTRYPOINT [ "/usr/bin/tini", "--"]
CMD ["finch", "start", "-b", "0.0.0.0", "--config", "/opt/wps/etc/demo.cfg"]

# docker build -t bird-house/finch .
# docker run -p 5000:5000 bird-house/finch
# http://localhost:5000/wps?request=GetCapabilities&service=WPS
# http://localhost:5000/wps?request=DescribeProcess&service=WPS&identifier=all&version=1.0.0
