#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
import re

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
REQUIRES_PYTHON = ">=3.7"

about = {}
with open(os.path.join(here, "finch", "__version__.py"), "r") as f:
    exec(f.read(), about)

egg_regex = re.compile(r"#egg=(\w+)")
requirements = []
for req in open("requirements.txt"):
    req = req.strip()
    git_url_match = egg_regex.search(req)
    if git_url_match:
        req = git_url_match.group(1)
    requirements.append(req)

dev_reqs = [line.strip() for line in open('requirements_dev.txt')]

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX",
    "Programming Language :: Python",
    "Natural Language :: English",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.7",
    "Topic :: Scientific/Engineering :: Atmospheric Science",
    "License :: OSI Approved :: Apache Software License",
]

setup(
    name="finch",
    version=about['__version__'],
    description="A Web Processing Service for Climate Indicators.",
    long_description=README + '\n\n' + CHANGES,
    long_description_content_type="text/x-rst",
    author=about['__author__'],
    author_email=about['__email__'],
    url='https://github.com/bird-house/finch',
    python_requires=REQUIRES_PYTHON,
    classifiers=classifiers,
    license="Apache Software License 2.0",
    keywords='wps pywps birdhouse finch',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        "dev": dev_reqs,              # pip install ".[dev]"
    },
    entry_points={"console_scripts": ["finch=finch.cli:cli"]},
)
