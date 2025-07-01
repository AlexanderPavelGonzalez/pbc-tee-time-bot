import logging
from datetime import datetime
from enum import Enum
from enums import PlayerCountMap # Import the Enum from the new file

# This class is used to inspect the html of the components on PBC booking page.
class Inspector:
    def __init__(self, page):
        self.page = page # Keep this, as other methods might use the initial page
        self.logger = logging.getLogger(__name__)
        print("Inspector class initialized!") 

    async def inspect_calendar(self, date):
        """
        Helper function to inspect page structure and elements
        """
        self.logger.info("=== CALENDAR INSPECTION START ===")

        # Take a screenshot
        await self.page.screenshot(path="debug_screenshot.png")
        self.logger.info("Screenshot saved as debug_screenshot.png")


        # --- Calendar Inspection ---
        self.logger.info("Attempting to find and inspect calendar element")
        # Try to find a likely calendar container or the month/year header
        # This selector is a starting point and may need adjustment based on the actual page HTML
        calendar_container = await self.page.query_selector('div.datepicker-days table') # Common pattern for Bootstrap datepickers

        if calendar_container:
            self.logger.info("Found a potential calendar element. Logging its HTML structure:")
            calendar_html = await calendar_container.inner_html()
            self.logger.info(f"Calendar HTML structure:\n{calendar_html[:5000]}...") # Log first 1000 characters to avoid excessive output
        else:
            self.logger.info("Could not find a potential calendar element using selector 'div.datepicker-days table'.")
        # --- End Calendar Inspection ---

        # --- Date Selection Test ---
        # Test the date selection logic here
        self.logger.info("Attempting to test date selection in inspect_page")
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                day_to_select = str(date_obj.day)

                # Directly attempt to click the day in the calendar table.
                # We specifically look for a 'td' with class 'day' that does NOT have the 'disabled' class
                # and contains the text of the day to select.
                day_selector = f'td.day:not(.disabled):has-text("{day_to_select}")'
                self.logger.info(f"Attempting to select day {day_to_select} with selector: {day_selector}")

                day_element = await self.page.query_selector(day_selector)

                if day_element:
                    await day_element.click()
                    self.logger.info(f"Successfully clicked on day {day_to_select} during inspection.")
                else:
                    self.logger.warning(f"Could not find selectable day {day_to_select} with selector: {day_selector}. It might be disabled or the calendar structure is different.")

            except Exception as e:
                self.logger.error(f"Error selecting date during inspection: {str(e)}")
        else:
            self.logger.info("Date environment variable not set, skipping date selection test.")
        # --- End Date Selection Test ---

        self.logger.info("=== CALENDAR INSPECTION END ===")

    async def inspect_tee_times(self, time_range_start, time_range_end, players):
        """
        Helper function to inspect tee time elements on the page.
        """
        self.logger.info("=== TEE TIME INSPECTION START ===")
        self.logger.info(f"Inspecting tee times for range: {time_range_start} to {time_range_end} for {players} players")

        try:
            # Use the correct selector for individual tee time cards
            tee_time_cards = await self.page.query_selector_all('.time.time-tile-ob-no-details')
            self.logger.info(f"Found {len(tee_time_cards)} potential tee time cards with selector '.time.time-tile-ob-no-details'.")

            if not tee_time_cards:
                self.logger.info("No individual tee time cards found with selector '.time.time-tile-ob-no-details'.")
                self.logger.info("=== TEE TIME INSPECTION END ===")
                return # Exit if no cards found

            self.logger.info("Iterating through tee time cards to find a match...")

            # Parse the input time range for comparison
            try:
                # Assuming time_range_start and time_range_end are in 'HH:MM' 24-hour format
                start_time_obj = datetime.strptime(time_range_start, '%H:%M').time()
                # If end time is less than start time, assume it's PM
                end_time_str = time_range_end
                if datetime.strptime(end_time_str, '%H:%M').time() < start_time_obj:
                    # Convert to 24-hour format by adding 12 hours
                    end_time_str = f"{int(end_time_str.split(':')[0]) + 12}:{end_time_str.split(':')[1]}"
                end_time_obj = datetime.strptime(end_time_str, '%H:%M').time()
                target_players = int(players)
                self.logger.info(f"Parsed target time range: {start_time_obj} to {end_time_obj}, Target players: {target_players}")
            except (ValueError, TypeError) as e:
                self.logger.error(f"Error parsing time range or player count: {e}")
                self.logger.info("=== TEE TIME INSPECTION END ===")
                return # Exit if parsing fails

            found_matching_tee_time = False

            for i, card in enumerate(tee_time_cards): # Iterate through all cards to find the first match
                try:
                    # Extract time using the correct selector within the card
                    time_element = await card.query_selector('.times-booking-start-time-label')
                    time_text = await time_element.text_content() if time_element else "N/A"

                    # Extract player count using the correct selector within the card
                    players_element = await card.query_selector('.time-summary-ob-player-count')
                    players_text = await players_element.text_content() if players_element else "0 Players"

                    # Parse tee time string (e.g., '1:57pm', '10:30am') into a time object for comparison
                    tee_time_time_obj = None
                    try:
                        # Need a base date for datetime parsing, today will do.
                        today = datetime.now().date()
                        # Try parsing with minute first, then hour, and AM/PM
                        # Check if it contains 'am' or 'pm' (case-insensitive)
                        time_str_lower = time_text.lower()
                        if 'am' in time_str_lower or 'pm' in time_str_lower:
                            # Handle potential single digit hour without leading zero. %I for 12-hour format, %p for AM/PM.
                            tee_time_dt_object = datetime.strptime(f'{today} {time_text}', '%Y-%m-%d %I:%M%p')
                        else:
                            # Assuming 24-hour format if am/pm is missing (unlikely based on screenshot, but good to handle)
                            tee_time_dt_object = datetime.strptime(f'{today} {time_text}', '%Y-%m-%d %H:%M')
                        tee_time_time_obj = tee_time_dt_object.time()
                    except ValueError as ve:
                         self.logger.warning(f"Could not parse tee time string '{time_text}': {ve}. Skipping this tee time.")
                         continue # Skip to the next card if parsing fails

                    # Parse available players count (assuming format like 'X Players')
                    available_players = 0
                    try:
                        # Extract the number part before ' Players'
                        available_players = int(players_text.split(' Players')[0].strip())
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Could not parse player count string '{players_text}': {e}. Assuming 0 available players.")
                        # available_players remains 0

                    # Check if time is within range and player count is sufficient
                    if tee_time_time_obj and start_time_obj <= tee_time_time_obj <= end_time_obj and available_players >= target_players:
                        self.logger.info(f"Match found! Tee time at {time_text} with {available_players} players meets criteria.")
                        found_matching_tee_time = True
                        # Exit the loop after finding the first match
                        break

                except Exception as e:
                    self.logger.warning(f"Error processing tee time card {i+1}: {e}. Skipping this card.")
                    continue # Continue to the next card on error

            if not found_matching_tee_time:
                 self.logger.info("No tee times found within the specified time range and player count.")

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during tee time inspection: {e}")

        self.logger.info("=== TEE TIME INSPECTION END ===")

    async def inspect_login_page(self):
        """
        Helper function to inspect the login page that opens in a new tab.
        """
        self.logger.info("=== LOGIN PAGE INSPECTION START ===")

        try:
            # Get all pages in the context
            pages = self.page.context.pages
            self.logger.info(f"Found {len(pages)} open pages")

            if len(pages) > 1:
                # The new page should be the last one opened
                new_page = pages[-1]
                self.logger.info("Found new page, taking screenshot")

                # Take a screenshot of the new page
                await new_page.screenshot(path="loginPage.png")
                self.logger.info("Screenshot saved as loginPage.png")

                # Log the URL of the new page
                self.logger.info(f"New page URL: {new_page.url}")

                # Log the page title
                title = await new_page.title()
                self.logger.info(f"New page title: {title}")

            else:
                self.logger.warning("No new page found. Expected a new tab to open after selecting tee time.")

        except Exception as e:
            self.logger.error(f"Error during login page inspection: {e}")

        self.logger.info("=== LOGIN PAGE INSPECTION END ===")

    async def inspect_player_filter(self, target_players):
        """
        Helper function to inspect the player count filter buttons.
        """
        self.logger.info("=== PLAYER FILTER INSPECTION START ===")
        self.logger.info(f"Looking for player count filter buttons, target: {target_players} players")

        try:
            # Find the player filter button group
            player_filter_group = await self.page.query_selector('.ob-filters-btn-group.players')
            if not player_filter_group:
                self.logger.error("Could not find player filter button group")
                return

            # Get all player count buttons
            player_buttons = await player_filter_group.query_selector_all('.ob-filters-btn')
            self.logger.info(f"Found {len(player_buttons)} player count buttons")

            # Log the data-value and text content of each button
            for button in player_buttons:
                data_value = await button.get_attribute('data-value')
                text = await button.text_content()
                is_active = await button.get_attribute('class')
                self.logger.info(f"Button - Value: {data_value}, Text: {text}, Classes: {is_active}")

                # If this button matches our target player count, log it
                if data_value == str(target_players):
                    self.logger.info(f"Found matching button for {target_players} players")
                    # Take a screenshot of the button
                    # await button.screenshot(path="playerButton.png")
                    # self.logger.info("Screenshot of matching button saved as playerButton.png")
                    pass # Keep the inspection logic for now, screenshot commented out

        except Exception as e:
            self.logger.error(f"Error during player filter inspection: {e}")

        self.logger.info("=== PLAYER FILTER INSPECTION END ===")

    async def inspect_holes_filter(self, target_holes):
        """
        Helper function to inspect the number of holes filter buttons.
        """
        self.logger.info("=== HOLES FILTER INSPECTION START ===")
        self.logger.info(f"Looking for number of holes filter buttons, target: {target_holes} holes")

        try:
            # Find the holes filter button group
            holes_filter_group = await self.page.query_selector('.ob-filters-btn-group.holes')
            if not holes_filter_group:
                self.logger.error("Could not find holes filter button group")
                return

            # Get all holes buttons
            holes_buttons = await holes_filter_group.query_selector_all('.ob-filters-btn')
            self.logger.info(f"Found {len(holes_buttons)} holes buttons")

            # Log the data-value and text content of each button
            for button in holes_buttons:
                data_value = await button.get_attribute('data-value')
                text = await button.text_content()
                is_active = await button.get_attribute('class')
                self.logger.info(f"Button - Value: {data_value}, Text: {text}, Classes: {is_active}")

                # If this button matches our target holes count, log it
                if data_value == str(target_holes):
                    self.logger.info(f"Found matching button for {target_holes} holes")
                    # Take a screenshot of the button
                    # await button.screenshot(path="holesButton.png")
                    # self.logger.info("Screenshot of matching button saved as holesButton.png")
                    pass # Keep the inspection logic for now, screenshot commented out

        except Exception as e:
            self.logger.error(f"Error during holes filter inspection: {e}")

        self.logger.info("=== HOLES FILTER INSPECTION END ===")

    async def inspect_booking_page(self, page_to_inspect, players):
        """
        Helper function to inspect the booking page that appears after login.
        Accepts the page object directly.
        """
        self.logger.info("=== BOOKING PAGE INSPECTION START ===")

        try:
            self.logger.info("Inspecting post-login booking page, taking screenshot")

            # Take a screenshot of the booking page
            await page_to_inspect.screenshot(path="bookingPage.png")
            self.logger.info("Screenshot saved as bookingPage.png")

            # Log the URL of the booking page
            self.logger.info(f"Booking page URL: {page_to_inspect.url}")

            # Log the page title
            title = await page_to_inspect.title()
            self.logger.info(f"Booking page title: {title}")

            # --- Inspection: Check for the presence of key booking form elements ---
            self.logger.info("Inspecting for booking form elements...")

            # Check for 18 Holes option
            holes_18_selector = 'label[for="holes-eighteen"]'
            holes_18_element = await page_to_inspect.query_selector(holes_18_selector)
            if holes_18_element:
                self.logger.info(f"Found 18 Holes label with selector: {holes_18_selector}")
            else:
                self.logger.warning(f"Could not find 18 Holes label with selector: {holes_18_selector}")

            # Check for Players options (check for the container or a specific player label)
            players_container_selector = '.player-selections' # Assuming this container exists
            players_container = await page_to_inspect.query_selector(players_container_selector)
            if players_container:
                 self.logger.info(f"Found players selection container with selector: {players_container_selector}")
                 # Optionally inspect specific player labels
                 for num_players in range(1, 5): # Check for 1, 2, 3, 4 player labels
                    try:
                        player_map_member = PlayerCountMap.from_number(num_players)
                        if player_map_member:
                            players_text_id = player_map_member.to_id_text()
                            player_label_selector = f'label[for="players-{players_text_id}"]'
                            player_label_element = await page_to_inspect.query_selector(player_label_selector)
                            if player_label_element:
                                self.logger.info(f"Found player label for {num_players} players with selector: {player_label_selector}")
                            else:
                                self.logger.warning(f"Could not find player label for {num_players} players with selector: {player_label_selector}")
                        else:
                             self.logger.warning(f"Could not map numerical player count {num_players} to text ID.")
                    except Exception as inspect_error:
                         self.logger.warning(f"Error inspecting player label for {num_players} players: {inspect_error}")
            else:
                 self.logger.warning(f"Could not find players selection container with selector: {players_container_selector}")

            # Check for Cart options
            # TODO: Add selector for Cart options once HTML is provided
            self.logger.info("Checking for Cart options (Selector needed).")

            # Check for Book Time button
            book_time_button_selector = 'button.ob-book-time-continue-button'
            book_time_button = await page_to_inspect.query_selector(book_time_button_selector)
            if book_time_button:
                 self.logger.info(f"Found Book Time button with selector: {book_time_button_selector}")
            else:
                 self.logger.warning(f"Could not find Book Time button with selector: {book_time_button_selector}")

            # --- End Inspection ---

        except Exception as e:
            self.logger.error(f"Error during post-login booking page inspection: {e}")

        self.logger.info("=== BOOKING PAGE INSPECTION END ===")

    async def inspect_payment_dialog(self, page_to_inspect):
        """
        Helper function to inspect the payment dialog modal.
        Accepts the page object directly.
        """
        self.logger.info("=== PAYMENT DIALOG INSPECTION START ===")

        try:
            # Wait for the payment modal to be visible
            payment_modal_selector = 'div#select-payment-type-modal[style*="display: block"]'
            self.logger.info(f"Waiting for payment modal to be visible with selector: {payment_modal_selector}")
            await page_to_inspect.wait_for_selector(payment_modal_selector, state='visible', timeout=10000) # Increased timeout
            self.logger.info("Payment modal is visible.")

            # Take a screenshot of the page with the modal visible
            await page_to_inspect.screenshot(path="paymentDialog.png")
            self.logger.info("Screenshot saved as paymentDialog.png")

            # --- Inspection: Check for the presence of key payment dialog elements ---
            self.logger.info("Inspecting for payment dialog elements...")

            # Check for Pay at Facility radio button
            pay_at_facility_selector = 'input[type="radio"][value="facility"]'
            pay_at_facility_element = await page_to_inspect.query_selector(pay_at_facility_selector)
            if pay_at_facility_element:
                self.logger.info(f"Found Pay at Facility radio button with selector: {pay_at_facility_selector}")
            else:
                self.logger.warning(f"Could not find Pay at Facility radio button with selector: {pay_at_facility_selector}")

            # Check for the final Book Time confirmation button
            final_book_time_button_selector = 'div#select-payment-type-modal button.peg-btn-primary:has-text("Book Time")'
            final_book_time_button = await page_to_inspect.query_selector(final_book_time_button_selector)

            if final_book_time_button:
                self.logger.info(f"Found the final Book Time button with selector: {final_book_time_button_selector}")
            else:
                self.logger.warning(f"Could not find the final Book Time button with selector: {final_book_time_button_selector}.")
            # --- End inspection of payment dialog elements ---

        except Exception as e:
            self.logger.error(f"Error during payment dialog inspection: {e}")

        self.logger.info("=== PAYMENT DIALOG INSPECTION END ===")