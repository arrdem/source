#!/bin/bash

mkvirtualenv source

workon source

pip install -r tools/python/requirements.txt

for d in $(find . -type d -path "*/src/python"); do
    d="$(realpath "${d}")"
    echo "Adding subproject ${d}"
    add2virtualenv "${d}"
done
