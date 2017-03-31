#!/bin/bash
DIR="$(dirname $0)"
ansible-playbook "$DIR/deploy.yaml" -i "$DIR/hosts" --ask-become-pass $@
