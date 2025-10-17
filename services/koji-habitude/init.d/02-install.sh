#! /bin/bash


python3 -m pip install --user PyYAML pydantic click

python3 -m pip install --user --no-deps --force-reinstall \
        /mnt/koji-habitude/dist/koji_habitude-0.1.0-py3-none-any.whl


# The end.
