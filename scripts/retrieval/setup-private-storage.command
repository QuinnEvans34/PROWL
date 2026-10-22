#!/bin/zsh
set -eu
cd -- "${0:A:h}/../.."
export PYTHONPATH=.
./.venv-retrieval/bin/python scripts/retrieval/setup_private_storage.py
printf '\nPress Return to close this setup window.\n'
read -r reply
