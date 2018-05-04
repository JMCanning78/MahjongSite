#!/bin/bash

MY_PATH="$(dirname "$0")"

echo $MY_PATH
source $MY_PATH/venv/bin/activate
export LIBGIT2=$VIRTUAL_ENV
python3 $MY_PATH/main.py $@
