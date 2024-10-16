#!/usr/bin/env bash

gunicorn -b :8080 app:app --timeout 120
