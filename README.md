# Palm Beach Country Tee Time Booking Automation

This project automates the process of booking a public golf tee time at Okeeheelee, or Osprey Point via the [ForeUp Software](https://foreupsoftware.com/index.php/booking/a/21263/21#/teetimes) website using Python and Playwright.

## Features

- Automatically selects the desired date, time range, number of players, and golf course (Okeeheelee or Osprey Point).
- Logs in with your PBC credentials.
- Fills out the booking form and confirms the reservation.
- Logs each step for easy debugging.

## Requirements

- Python 3.8+
- [Playwright](https://playwright.dev/python/) (`playwright==1.42.0`)
- [python-dotenv](https://pypi.org/project/python-dotenv/) (`python-dotenv==1.0.0`)

Install dependencies:
```bash
pip install -r requirements.txt
playwright install
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
DATE=2025-05-25                # Date to book (YYYY-MM-DD)
TIME_RANGE_START=08:00         # Earliest tee time (24h format)
TIME_RANGE_END=11:00           # Latest tee time (24h format)
PLAYERS=4                      # Number of players (1-4)
EMAIL=your@email.com           # PBC login email
PASSWORD=yourpassword          # PBC login password
COURSE=Park Ridge              # Course name: Park Ridge, Okeeheelee, or Osprey Point
```

## Usage

To run the script manually:
```bash
source .venv/bin/activate
set -a
[ -f .env ] && . .env
set +a
python book_tee_time.py
```

## Logging

All output is logged to `cron_script_run.log` in the project directory.

---
