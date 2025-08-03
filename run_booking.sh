#!/bin/bash

cd /Users/alexandergonzalez/PBC_Bot
source .venv/bin/activate

set -a
[ -f .env ] && . .env
set +a

python book_tee_time.py >> /Users/alexandergonzalez/PBC_Bot/cron_script_run.log 2>&1
