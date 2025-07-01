# Palm Beach Country Tee Time Booking Automation

This project automates the process of booking a public golf tee time at Okeeheelee, or Osprey Point via the [ForeUp Software](https://foreupsoftware.com/index.php/booking/a/21263/21#/teetimes) website using Python and Playwright.

## Features

- Automatically selects the desired date, time range, number of players, and golf course (Park Ridge, Okeeheelee, or Osprey Point).
- Logs in with your PBC credentials.
- Fills out the booking form and confirms the reservation.
- Runs headlessly for automation (e.g., via cron or GitHub Actions).
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

Or use the provided shell script:
```bash
./run_booking.sh
```

## Automation with Cron

To schedule the script to run automatically (e.g., every Saturday and Sunday at 5:00 AM and 6:00 AM EST), add this to your crontab:
```
0 5,6 * * 6,0 /Users/alexandergonzalez/PBC_Bot/run_booking.sh
```
> **Note:** Your computer must be on and awake for cron jobs to run.

## Logging

All output is logged to `cron_script_run.log` in the project directory.

## Running on a Raspberry Pi or Server

You can run this project on a Raspberry Pi or any always-on Linux server for reliable automation. Just clone the repo, set up Python and Playwright, and configure your `.env` and cron job as above.

## GitHub Actions (Optional)

You can also automate bookings using GitHub Actions. See `main_prompt.md` for a sample workflow.

---

Let us know if you have any questions or want to contribute! 