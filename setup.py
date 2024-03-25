#!/usr/bin/env python

"""The setup script."""

import os

from setuptools import find_namespace_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.rst")).read()
CHANGES = open(os.path.join(here, "CHANGES.rst")).read()
REQUIRES_PYTHON = ">=3.8"

about = {}
with open(os.path.join(here, "finch", "__version__.py")) as f:
    exec(f.read(), about)

reqs = [line.strip() for line in open("requirements.txt")]
dev_reqs = [line.strip() for line in open("requirements_dev.txt")]
docs_reqs = [line.strip() for line in open("requirements_docs.txt")]
prod_reqs = [line.strip() for line in open("requirements_prod.txt")]

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Natural Language :: English",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: Atmospheric Science",
]

setup(
    name="birdhouse-finch",
    version=about["__version__"],
    description="A Web Processing Service for Climate Indicators.",
    long_description=README + "\n\n" + CHANGES,
    long_description_content_type="text/x-rst",
    author=about["__author__"],
    author_email=about["__email__"],
    url="https://github.com/bird-house/finch",
    python_requires=REQUIRES_PYTHON,
    classifiers=classifiers,
    license="Apache Software License 2.0",
    license_files=["LICENSE"],
    keywords="wps pywps birdhouse finch",
    packages=find_namespace_packages(".", include=["finch*"]),
    include_package_data=True,
    package_data={"finch": ["*.yml"]},
    install_requires=reqs,
    test_suite="tests",
    extras_require={
        "dev": dev_reqs,  # pip install ".[dev]"
        "docs": docs_reqs,  # pip install ".[docs]"
        "prod": prod_reqs,  # pip install ".[prod]"
    },
    entry_points={"console_scripts": ["finch=finch.cli:cli"]},
    zip_safe=False,
)
