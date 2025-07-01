#!/bin/bash

# Change to the script directory
cd /Users/alexandergonzalez/PBC_Bot

# Activate virtual environment
source .venv/bin/activate

# Export all variables from .env, but skip lines that are comments or empty
set -a
[ -f .env ] && . .env
set +a

# Run the script
python book_tee_time.py >> /Users/alexandergonzalez/PBC_Bot/cron_script_run.log 2>&1 