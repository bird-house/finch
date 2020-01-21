"""
This script replays the cookiecutter repository creation with the original values.

The intended use is to inject template changes into an existing repo.

How-to
======
* Make sure that there are no files left uncommitted.
* Check out the commit right after the repo creation by cookiecutter
  and create a new branch that will hold the template modifications.
* Clean the repo
* Run this script from the parent directory
* Commit all files that were created or modified
* Checkout a new branch from master
* Merge the modifications made to the original version
* Fix the conflicts and merge

.. code:: bash

    git checkout -b orig_cc_update <SHA>
    git clean -fxd
    cd ..
    python finch/update_from_cc.py
    cd finch
    git add * */.*
    git commit -m 'update from cookiecutter template'
    git rebase master

"""

from cookiecutter.main import cookiecutter

if __name__ == "__main__":

    cookiecutter(
        "cookiecutter-birdhouse",
        no_input=True,
        overwrite_if_exists=True,
        extra_context={
            "full_name": "David Huard",
            "email": "huard.david@ouranos.ca",
            "github_username": "bird-house",
            "project_name": "finch",
            "project_slug": "finch",
            "project_repo_name": "finch",
            "project_short_description": "A Web Processing Service for Climate Indicators",
            "version": "0.1.0",
            "open_source_license": "Apache Software License 2.0",
            "http_port": "5000",
            "timestamp": "2018-04-16",
        },
    )
