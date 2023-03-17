#!/usr/bin/env bash

{ [[ -n $ZSH_EVAL_CONTEXT && $ZSH_EVAL_CONTEXT =~ :file$ ]] || [[ -n $BASH_VERSION && "$0" != "${BASH_SOURCE[0]}" ]]; } && SOURCED=1 || SOURCED=0

if [[ $SOURCED == 0 ]]; then
    echo "This script needs to be sourced!"
    echo "Example: source ./pulumi-state-login.sh"
else
    REMOTE_STATE_S3_BUCKET_URI="s3://pulumi-remote-state"
    pulumi login "${REMOTE_STATE_S3_BUCKET_URI}"
    pulumi stack select WeatherAlerting.dev
fi
