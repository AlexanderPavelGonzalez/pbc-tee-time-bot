Always read this file before you write code. This is a requirement for you.
Write a Python script using Playwright that automates booking a tee time from:

https://foreupsoftware.com/index.php/booking/a/21263/21#/teetimes

Requirements:

1. When the script runs, it should:
   - Go to the above URL.
   - Click the “Public Tee Times” button.
   - In the left sidebar under “Courses,” click “Park Ridge” to filter the tee times by that course only.
   - Wait for available tee times to load.

2. The script should accept inputs via environment variables:
   - DATE: the date to book (e.g., "2025-05-25")
   - TIME_RANGE_START and TIME_RANGE_END: start and end times (e.g., "08:00" and "11:00")
   - PLAYERS: number of players (1–4)
   - EMAIL: PBC login email
   - PASSWORD: PBC login password

3. The script should run **headless** (no browser UI) to support CI/CD environments like GitHub Actions.

4. The script **should not handle scheduling or waiting for a time** internally; instead, it should expect to be triggered exactly at the right time (e.g., via GitHub Actions scheduled workflow).

5. When triggered, it should:
   - Filter tee times by the given date.
   - Look for available tee times on that date that fall within the desired time range.
   - Click the first available matching tee time.

6. After selecting a tee time:
   - Log in using the user-provided credentials in the modal that pops up:
     - Fill in email and password fields
     - Click the “Log In” button
     - Wait for the login process to complete before proceeding

7. Fill out the tee time form:
   - Set Holes = 18
   - Set Players = number passed in
   - Set Cart = Yes

8. Click the **“Book Time”** button on the right.

9. In the payment modal:
   - Select **“Pay at Facility”** (radio option)
   - Use the first saved credit card from the dropdown (assume one is always saved)
   - Click the second **“Book Time”** button inside the dialog to confirm the reservation.

10. Wrap all this in an `async` function named `book_tee_time()` that is called in a `__main__` block.

11. Add clear console logging for each major step and error handling to make debugging easier.

---

Additionally, write a **GitHub Actions workflow YAML** snippet that:

- Runs on Ubuntu latest
- Sets environment variables for DATE, TIME_RANGE_START, TIME_RANGE_END, PLAYERS, EMAIL, PASSWORD (assumed stored as GitHub secrets)
- Installs Python dependencies and runs `playwright install` to set up browsers
- Runs the script at 5:00 AM UTC 7 days before the booking date (use cron schedule)
- Runs the script with all required environment variables

---

Make sure the script and workflow together enable fully unattended, headless booking triggered by GitHub Actions.