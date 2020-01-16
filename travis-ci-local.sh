#!/bin/bash

# Run the travis ci build locally inside a docker image

BUILDID="build-$RANDOM"

# At the time of writing, this is the closest docker image version
# that last ran on travis-ci
INSTANCE="travisci/ci-sardonyx:packer-1554885359-f909ac5"

docker run --name $BUILDID -dit $INSTANCE /sbin/init

travis_commands='\
git clone --depth=50 --branch=xclim13 https://github.com/bird-house/finch.git bird-house/finch
cd bird-house/finch
source ~/virtualenv/python3.6/bin/activate
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
sh miniconda.sh -b -p /home/travis/miniconda
export PATH=/home/travis/miniconda/bin:$PATH
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda info -a
conda create -n finch python=$TRAVIS_PYTHON_VERSION
conda env update -f environment.yml
source activate finch
conda install pytest flake8
pip install -e .
finch start --daemon --bind-host 0.0.0.0 --port 5000
sleep 2
pytest -m \"not online\"
flake8
'

docker exec -t $BUILDID sh -c "su - -c \"$travis_commands\" travis"

# Note: comment the next line to leave the container running
# so that you won't have to reinstall all the libraries on every test run
docker stop $BUILDID && docker rm $BUILDID
