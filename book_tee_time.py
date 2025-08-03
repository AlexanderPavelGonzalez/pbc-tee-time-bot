import os
import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
from inspector import Inspector
from enums import PlayerCountMap

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def select_day(page, date_str):
    """
    Selects the specified day in the calendar.
    Assumes the calendar is visible and the correct month is displayed,
    or the target day from the next month is visible and selectable.
    """
    logger.info(f"Attempting to select day for date: {date_str}")
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_to_select = str(date_obj.day)
        
        # Find all day elements with the target day number
        days = page.locator(f'td.day:has-text("{day_to_select}")')
        count = await days.count()
        logger.info(f"Found {count} day elements with value {day_to_select}")
        
        clicked = False
        for i in range(count):
            class_attr = await days.nth(i).get_attribute('class')
            text_content = (await days.nth(i).text_content()).strip()
            logger.info(f"Day {i}: class='{class_attr}', text='{text_content}'")
    
            # Check if this day is not disabled and text matches exactly
            if 'disabled' not in class_attr and text_content == day_to_select:
                logger.info(f"Clicking day {day_to_select} at index {i} (class: {class_attr})")
                await days.nth(i).click()
                clicked = True
                break
        
        if not clicked:
            raise Exception(f'No enabled day "{day_to_select}" found to click!')

        await asyncio.sleep(1)     
        logger.info(f"Successfully clicked on day {day_to_select}.")
        await page.screenshot(path="daySelected.png")
        logger.info("day selected screenshot")

    except Exception as e:
        logger.error(f"Error selecting date in calendar: {str(e)}")
        raise # Re-raise the exception to be caught by the main booking function's error handling

async def select_tee_time(page, time_range_start, time_range_end, players):
    """
    Selects a tee time that matches the specified criteria.
    """
    # Wait for tee times to load after date selection
    try:
        logger.info("Waiting for tee time cards to appear after date selection...")
        await page.wait_for_selector('.time.time-tile-ob-no-details', timeout=5000)  # Increased timeout to 30 seconds
        logger.info("Tee time cards found successfully after date selection")
    except PlaywrightTimeoutError:
        logger.error("Timeout waiting for tee time cards after date selection")
        # Log the current page content for debugging
        content = await page.content()
        logger.info(f"Current page content: {content[:1000]}...")  # Log first 1000 chars
        raise
    logger.info(f"Attempting to select tee time between {time_range_start} and {time_range_end} for {players} players")
    try:
        # Use the correct selector for individual tee time cards
        tee_time_cards = await page.query_selector_all('.time.time-tile-ob-no-details')
        if not tee_time_cards:
            raise Exception("No tee time cards found")

        # Parse the input time range for comparison
        start_time_obj = datetime.strptime(time_range_start, '%H:%M').time()
        # If end time is less than start time, assume it's PM
        end_time_str = time_range_end
        if datetime.strptime(end_time_str, '%H:%M').time() < start_time_obj:
            end_time_str = f"{int(end_time_str.split(':')[0]) + 12}:{end_time_str.split(':')[1]}"
        end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
        target_players = int(players)

        for card in tee_time_cards:
            try:
                # Extract time and player count
                time_element = await card.query_selector('.times-booking-start-time-label')
                time_text = await time_element.text_content() if time_element else "N/A"

                players_element = await card.query_selector('.time-summary-ob-player-count')
                players_text = await players_element.text_content() if players_element else "0 Players"

                # Parse tee time
                today = datetime.now().date()
                time_str_lower = time_text.lower()
                if 'am' in time_str_lower or 'pm' in time_str_lower:
                    tee_time_dt_object = datetime.strptime(f'{today} {time_text}', '%Y-%m-%d %I:%M%p')
                else:
                    tee_time_dt_object = datetime.strptime(f'{today} {time_text}', '%Y-%m-%d %H:%M')
                tee_time_time_obj = tee_time_dt_object.time()

                # Parse available players
                available_players = int(players_text.split(' Players')[0].strip())

                # Check if this tee time matches our criteria
                if tee_time_time_obj and start_time_obj <= tee_time_time_obj <= end_time_obj and available_players >= target_players:
                    logger.info(f"Selecting tee time at {time_text} with {available_players} players")
                    await card.click()
                    await asyncio.sleep(6)
                    await page.screenshot(path="teeTimeSelected.png")
                    logger.info("tee time selected screenshot")
                    return True

            except Exception as e:
                logger.warning(f"Error processing tee time card: {e}")
                continue

        raise Exception(f"No available tee times found between {time_range_start} and {time_range_end} for {players} players")

    except Exception as e:
        logger.error(f"Error selecting tee time: {e}")
        raise

async def handle_login_page(page, email, password):
    """
    Handles the login process on the new tab and returns the page object.
    """

    logger.info("=== HANDLING LOGIN PAGE START ===")
    try:
        # Get all pages in the context
        pages = page.context.pages
        logger.info(f"Found {len(pages)} open pages")

        if len(pages) <= 1:
             raise Exception("Expected a new page/tab to open for login, but found none.")

        login_page = pages[-1]
        logger.info("Found new page for login, taking screenshot")
        # Log the URL of the new page
        logger.info(f"New page URL: {login_page.url}")
        
        # Wait for the email input field to appear (indicates modal is ready)
        # This assumes the login appears as a modal on the same page.
        await login_page.wait_for_selector('input[type="text"][id="login_email"]')
        # We are alreading waiting for page to loag here. Debuggin should probably happen here
        logger.info("Login modal or page detected, proceeding with login.")

        # Fill out the email and password fields on the login modal
        await login_page.fill('input[type="text"][id="login_email"]', email)
        logger.info("Email field filled.")
        await login_page.fill('input[type="password"][id="login_password"]', password)
        logger.info("Password field filled.")

        # Click the Log In button on the login modal
        # Assuming the button has the text "Log In". Adjust selector if necessary.
        await login_page.click('button:has-text("Log In")')
        logger.info("Clicked Log In button.")

        # Wait for the login to complete. Could be the modal closing or a page update.
        # Using networkidle state as a general indicator, or wait for a specific element to disappear/appear.
        # A more robust wait here might be needed depending on what happens after login.
        await login_page.wait_for_selector('input[type="text"][id="login_email"]', state='hidden')
        logger.info("Login process initiated, waiting for load state.")

        logger.info("=== HANDLING LOGIN PAGE END ===")
        return login_page # Return the page object

    except Exception as e:
        logger.error(f"Error during login handling: {e}")
        raise # Re-raise the exception

async def select_booking_information(page, players):
    """
    Selects the booking information on the post-login page (Holes, Players, Cart - assuming Cart=Yes).
    Clicks the 'Book Time' button to proceed.
    """
    logger.info("=== SELECTING BOOKING INFORMATION START ===")

    try:
        # Select 18 Holes
        holes_18_label_selector = 'label[for="holes-eighteen"]'
        logger.info(f"Attempting to select 18 Holes using selector: {holes_18_label_selector}")
        try:
            # Use page.click which waits for the element to be visible and enabled
            await page.click(holes_18_label_selector, timeout=15000) # Increased timeout
            logger.info("Successfully selected 18 Holes.")
        except Exception as e:
            logger.error(f"Could not select 18 Holes with selector {holes_18_label_selector}: {e}")
            raise # Re-raise the exception

        # Select Players
        # Construct selector based on the 'players' argument, using the ID attribute from the Enum
        player_map_member = PlayerCountMap.from_number(players)

        if player_map_member:
            players_text_id = player_map_member.to_id_text()
            players_label_selector = f'label[for="players-{players_text_id}"]' # Using the label as per the user's fix
            logger.info(f"Attempting to select Players for {players} players using selector: {players_label_selector}")

            try:
                # Use page.wait_for_selector followed by click()
                players_button = await page.wait_for_selector(players_label_selector, timeout=15000) # Increased timeout
                await players_button.click()
                logger.info(f"Successfully selected Players for {players} players.")

            except Exception as click_error:
                logger.error(f"Could not select Players with selector {players_label_selector}: {click_error}")
                raise # Re-raise the exception
        else:
            logger.error(f"Invalid player count: {players}. Cannot construct ID-based selector using Enum.")
            raise ValueError(f"Invalid player count: {players}") # Raise error for invalid player count

        # Select Cart = Yes (assuming selector based on inspection)
        # TODO: Add actual selector for Cart=Yes once HTML is provided.
        # For now, this is a placeholder.
        logger.info("Selecting Cart = Yes (Placeholder - Need actual selector).")
        # await page.click('selector_for_cart_yes', timeout=15000)
        # logger.info("Successfully selected Cart = Yes.")
        
        # Click the 'Book Time' button
        book_time_button_selector = 'button.ob-book-time-continue-button'
        logger.info(f"Attempting to click Book Time button with selector: {book_time_button_selector}")

        try:
            # Use page.wait_for_selector followed by click()
            book_time_button = await page.wait_for_selector(book_time_button_selector, timeout=15000) # Increased timeout
            await book_time_button.click()
            logger.info("Successfully clicked the Book Time button.")

        except Exception as click_error:
            logger.error(f"Could not click Book Time button with selector {book_time_button_selector}: {click_error}")
            raise # Re-raise the exception

    except Exception as e:
        logger.error(f"Error during selecting booking information: {e}")
        raise # Re-raise the exception

    logger.info("=== SELECTING BOOKING INFORMATION END ===")

async def finalize_booking(page):
    """
    Handles the final steps in the payment dialog: selecting Pay at Facility,
    """
    logger.info("=== FINALIZING BOOKING START ===")

    try:
        # Wait for the payment modal to be visible
        payment_modal_selector = 'div#select-payment-type-modal[style*="display: block"]'
        logger.info(f"Waiting for payment modal to be visible with selector: {payment_modal_selector}")
        # Using page.wait_for_selector directly on the main page object, as the modal is likely part of it.
        await page.wait_for_selector(payment_modal_selector, state='visible', timeout=10000) # Increased timeout
        logger.info("Payment modal is visible.")

        # Select Pay at Facility
        pay_at_facility_selector = 'input[type="radio"][value="facility"]'
        logger.info(f"Attempting to click Pay at Facility radio button with selector: {pay_at_facility_selector}")

        try:
            # Use page.click which waits for the element to be visible and enabled
            await page.click(pay_at_facility_selector, timeout=15000) # Increased timeout
            logger.info("Successfully clicked the Pay at Facility radio button.")

        except Exception as click_error:
            logger.error(f"Could not click Pay at Facility radio button with selector {pay_at_facility_selector}: {click_error}")
            raise # Re-raise the exception

        # Click the final Book Time confirmation button in the modal
        final_book_time_button_selector = 'div#select-payment-type-modal button.peg-btn-primary:has-text("Book Time")'
        logger.info(f"Attempting to click the final Book Time button with selector: {final_book_time_button_selector}")

        try:
            # Use page.wait_for_selector followed by click()
            final_book_time_button = await page.wait_for_selector(final_book_time_button_selector, timeout=15000) # Increased timeout
            await final_book_time_button.click()
            logger.info("Successfully clicked the final Book Time button.")

            # Optional: Take a screenshot after final booking click
            await page.screenshot(path="bookingFinalized.png")
            logger.info("Screenshot after finalizing booking saved.")

        except Exception as click_error:
            logger.error(f"Could not click final Book Time button with selector {final_book_time_button_selector}: {click_error}")
            raise # Re-raise the exception

    except Exception as e:
        logger.error(f"Error during finalizing booking: {e}")
        raise # Re-raise the exception

    logger.info("=== FINALIZING BOOKING END ===")

async def select_players_filter(page, target_players):
    """
    Selects the specified player count filter button.
    """
    logger.info(f"Attempting to select player count filter for {target_players} players")
    logger.info(f"Debug - Raw target_players value: '{target_players}'")
    logger.info(f"Debug - target_players type: {type(target_players)}")
    
    try:
        # Clean up the target_players value
        target_players = str(target_players).strip()
        logger.info(f"Debug - Cleaned target_players value: '{target_players}'")
        
        # Construct the selector for the specific player button
        # We look for an <a> with class .ob-filters-btn inside .ob-filters-btn-group.players
        # that has a data-value attribute matching the target_players.
        player_button_selector = f'.ob-filters-btn-group.players a.ob-filters-btn[data-value="{target_players}"]'
        logger.info(f"Attempting to click player button with selector: {player_button_selector}")
        
        # Use page.locator and click, which handles waiting for the element.
        await page.locator(player_button_selector).click()
        logger.info(f"Successfully clicked on player filter for {target_players} players.")
        
        # Add a small wait to ensure the filter is applied and page updates
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"Error selecting player filter: {e}")
        raise # Re-raise the exception

async def select_holes_filter(page, target_holes):
    """
    Selects the specified number of holes filter button.
    """
    logger.info(f"Attempting to select number of holes filter for {target_holes} holes")

    try:
        # Construct the selector for the specific holes button
        # We look for an <a> with class .ob-filters-btn inside .ob-filters-btn-group.holes
        # that has a data-value attribute matching the target_holes.
        holes_button_selector = f'.ob-filters-btn-group.holes a.ob-filters-btn[data-value="{target_holes}"]'
        logger.info(f"Attempting to click holes button with selector: {holes_button_selector}")

        # Use page.locator and click, which handles waiting for the element.
        await page.locator(holes_button_selector).click()
        logger.info(f"Successfully clicked on holes filter for {target_holes} holes.")

        # Add a small wait to ensure the filter is applied and page updates
        await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Error selecting holes filter: {e}")
        raise # Re-raise the exception

async def book_tee_time():
    """
    Main function to book a tee time using Playwright automation.
    """
    try:
        # Get environment variables
        time_range_start = os.getenv('TIME_RANGE_START')
        time_range_end = os.getenv('TIME_RANGE_END')
        players = os.getenv('PLAYERS')
        email = os.getenv('EMAIL')
        password = os.getenv('PASSWORD')
        osprey_only = os.getenv('OSPREY_ONLY')
        
        # Calculate date 7 days from today
        from datetime import datetime, timedelta
        target_date = datetime.now() + timedelta(days=7)
        date = target_date.strftime('%Y-%m-%d')
        logger.info(f"Calculated target date: {date} (7 days from today)")

        # Clean up players value - remove quotes, comments, and extra whitespace
        if players:
            players = players.split('#')[0].strip().replace('"', '')
            logger.info(f"Cleaned players value: '{players}'")

        logger.info(f"Attempting to book tee time for {date} between {time_range_start} and {time_range_end} for {players} player(s). Osprey only: {osprey_only}")

        # Validate required environment variables
        required_vars = {
            'TIME_RANGE_START': time_range_start,
            'TIME_RANGE_END': time_range_end,
            'PLAYERS': players,
            'EMAIL': email,
            'PASSWORD': password,
            'OSPREY_ONLY': osprey_only
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        logger.info("Starting tee time booking process")
        
        async with async_playwright() as p:
            # Launch browser with arguments to make headless mode appear more like a regular browser
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            page = await context.new_page()

            # Create an instance of the Inspector class
            inspector = Inspector(page)
            print(f"Created inspector object: {inspector}")

            try:
                # Navigate to the booking page
                logger.info("Navigating to booking page")
                await page.goto('https://foreupsoftware.com/index.php/booking/a/21263/21#/teetimes')
                
                # Click Public Tee Times button
                logger.info("Clicking Public Tee Times button")
                await page.click('div.booking-classes >> button:has-text("Public Tee Times")')
                
                # Wait for the course list or main content to load after clicking Public Tee Times
                await page.wait_for_selector('#js-course-list') # Wait for the sidebar course list
                logger.info("Waited for course list to load.")

                # Click Park Ridge in the sidebar
                logger.info("Selecting Park Ridge course")
                await page.locator('#js-course-list > div.filter-course-option[data-schedule-id="7483"] > div.filter-course-select-button-bordered.js-filter-course-select-toggle').click()

                # If osprey only, filter by osprey
                osprey_only_str = os.getenv('OSPREY_ONLY', 'false')
                osprey_only = osprey_only_str.lower() == 'true'
                if osprey_only:
                    logger.info("Filtering by Osprey only")
                    await page.locator('#js-course-list > div.filter-course-option[data-schedule-id="7480"] > div.filter-course-select-button-bordered.js-filter-course-select-toggle').click()

                # Select player count filter
                await select_players_filter(page, players)

                # Select number of holes filter (defaulting to '18' as per requirement 7)
                await select_holes_filter(page, "18")

                # Filter by date
                await select_day(page, date)

                # # Then select a matching tee time
                await select_tee_time(page, time_range_start, time_range_end, players)
                                    
                # Handle the login and get the post-login page
                post_login_page = await handle_login_page(page, email, password)

                # Select booking information
                await select_booking_information(post_login_page, players)

                # Finalize the booking
                await finalize_booking(post_login_page)

            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Error during booking process: {str(e)}")
                raise
            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

def lambda_handler(event, context):
    asyncio.run(book_tee_time())

if __name__ == "__main__":
    asyncio.run(book_tee_time())