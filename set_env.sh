#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Please run this script using 'source' or '.' like this:"
    echo "  source ${0}"
    echo "  . ${0}"
    exit 1
fi

if [ ! -f .env ]; then
    echo "Error: .env file not found."
    echo "Please create a .env file with VAR_NAME=value pairs."
    return 1
fi

set -a
source .env
set +a

echo "Environment variables from .env have been set."