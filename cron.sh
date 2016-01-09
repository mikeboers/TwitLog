#!/bin/bash

here="$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd)"

source venv/bin/activate
source .env.sh

twitlog-followers
twitlog-analytics
