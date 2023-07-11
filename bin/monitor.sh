#!/bin/bash

set -ve

CURRENT_ENV="${TARGET_ENV:-dev}"

SENTRY_API_URL='https://sentry.io/api/0/organizations/frog-pond-labs/monitors/course-data-tools/checkins/'
SENTRY_API_LATEST_URL="${SENTRY_API_URL%/}/latest/"

SENTRY_AUTH_HEADER="Authorization: DSN $SENTRY_DSN"
CONTENT_TYPE_HEADER='Content-Type: application/json'

function start() {
    curl -X POST \
        "$SENTRY_API_URL" \
        --header "$SENTRY_AUTH_HEADER" \
        --header "$CONTENT_TYPE_HEADER" \
        --data-raw "$(jq -n --arg env "$CURRENT_ENV" '{status: "in_progress", environment: $env}')"
}

function stop() {
    curl -X PUT \
        "$SENTRY_API_LATEST_URL" \
        --header "$SENTRY_AUTH_HEADER" \
        --header "$CONTENT_TYPE_HEADER" \
        --data-raw "$(jq -n --arg env "$CURRENT_ENV" '{status: "ok", environment: $env}')"
}

function fail() {
    curl -X PUT \
        "$SENTRY_API_LATEST_URL" \
        --header "$SENTRY_AUTH_HEADER" \
        --header "$CONTENT_TYPE_HEADER" \
        --data-raw "$(jq -n --arg env "$CURRENT_ENV" '{status: "error", environment: $env}')"
}

function report_status() {
    if [ "$1" = "start" ]; then
        start
    elif [ "$1" = "stop" ]; then
        stop
    elif [ "$1" = "fail" ]; then
        fail
    else
        echo "Invalid argument. Usage: report_status [start|stop|fail]"
    fi
}

report_status "$1"
