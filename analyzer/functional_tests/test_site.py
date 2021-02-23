"""Run functional test for your site here."""

import os
import math
import datetime
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .testserver import StaticLiveServerTestCase_Chrome
from selenium.common.exceptions import NoSuchElementException


def setMonth_js(date, month):
    """Emulates JavaScript Date.prototype.setMonth() functionality.

    :param date: Date to change month in.
    :type date: datetime.date
    :param month: Month to set to. Special rules: 0 = last year December, -1 = last year November,
                  13 = January next year, etc.. If day is out of range in set month, sets day to
                  the next month by the remainder (e.g. 31.3 - 1 month -> 3.3 (or 2.3. on leap years))
    :type month: int
    :return: New date.
    :rtype: datatime.date
    """

    new_day = date.day

    # in Javascript: 0 = January, 11 = December. -1 = last year December, 12 = next year January, etc.
    month -= 1

    if month < 0:
        years_back = -1 - math.floor(-month / 11)
        date = date.replace(year=date.year + years_back)

        month = (11 + 1) - (-month % 11)

    if month > 11:
        years_forward = math.floor(month / 11)
        date = date.replace(year=date.year + years_forward)

        month = (month % 11) - 1

    date = date.replace(day=1)
    date = date.replace(month=month + 1)  # + 1 because January is 0 in JavaScript and 1 in Python
    date += datetime.timedelta(days=new_day - 1)

    return date


def setFullYear_js(date, year):
    """Emulates JavaScript Date.prototype.setFullYear() functionality.

    :param date: Date to change month in.
    :type date: datetime.date
    :param year: Year to set to. If day of the month is out of range in set year, sets day to
                 the next month by the remainder (e.g. 29.2 -> 1.3 from leap years to non-leap years)
    :type year: int
    :return: New date.
    :rtype: datatime.date
    """

    new_day = date.day

    date = date.replace(day=1)
    date = date.replace(year=year)
    date += datetime.timedelta(days=new_day - 1)

    return date


class TestSiteFunctionality(StaticLiveServerTestCase_Chrome):
    """Test site functionality with a headless browser."""

    def test_predefined_buttons(self):
        """Test searching last trading year of Apple stock."""

        # ~~ User should be on the front page

        stock = "AAPL"
        end_date = datetime.date.today()

        start_dates = [
            end_date - datetime.timedelta(days=5),
            setMonth_js(date=end_date, month=end_date.month - 1),
            setMonth_js(date=end_date, month=end_date.month - 6),
            setFullYear_js(date=end_date, year=end_date.year - 1),
            datetime.date(year=end_date.year, month=1, day=1),
        ]

        button_ids = ["id_5day", "id_1month", "id_6month", "id_1year", "id_ytd"]

        stock_field = self.browser.find_element_by_name("stock")
        start_date_field = self.browser.find_element_by_name("start_date")

        # Set data for fields and search
        stock_field.send_keys(stock)

        # ~~ User pressess the buttons in order

        for start_date, button_id in zip(start_dates, button_ids):
            date_button = self.browser.find_element_by_id(button_id).find_element_by_tag_name("button")
            date_button.click()
            self.assertEqual(
                start_date_field.get_attribute("value"),
                start_date.strftime("%Y-%m-%d"),
                msg=f"Pressing button '{button_id}' does not give correct value."
            )

    def test_search_start_date_to_current_date(self):
        """Test searching Apple stock with just a start date."""

        # ~~ User should be on the front page

        stock = "AAPL"
        start_date = datetime.date.today() - datetime.timedelta(days=60)

        stock_field = self.browser.find_element_by_name("stock")
        submit_button = self.browser.find_element_by_css_selector("button[type='submit']")

        # Set data for fields and search
        stock_field.send_keys(stock)
        # 'set_keys' does not work for date inputs for some reason...
        self.browser.execute_script(f"document.getElementById('id_start_date').value = '{start_date}'")
        submit_button.click()

        # ~~ Searches for Apple stock for the last 30 days

        try:
            self.browser.find_element_by_id("longest_bullish")
        except NoSuchElementException:
            self.fail("Longest Bullish -value was not found!")

        try:
            self.browser.find_element_by_id("history_by_volume")
        except NoSuchElementException:
            self.fail("History by Volume -table was not found!")

        try:
            self.browser.find_element_by_id("best_opening_price")
        except NoSuchElementException:
            self.fail("Best Opening Price -table was not found!")

        self.assertURLEqual(
            self.browser.current_url,
            self.live_server_url + f"/?stock={stock}&start_date={start_date}&end_date="
        )

    def test_search_start_date_to_end_date(self):
        """Test searching Apple stock on a custom interval."""

        # ~~ User should be on the front page

        stock = "AAPL"
        end_date = datetime.date.today() - datetime.timedelta(days=20)
        start_date = end_date - datetime.timedelta(days=60)

        stock_field = self.browser.find_element_by_name("stock")
        submit_button = self.browser.find_element_by_css_selector("button[type='submit']")

        # Set data for fields and search
        stock_field.send_keys(stock)
        # 'set_keys' does not work for date inputs for some reason...
        self.browser.execute_script(f"document.getElementById('id_start_date').value = '{start_date}'")
        self.browser.execute_script(f"document.getElementById('id_end_date').value = '{end_date}'")
        submit_button.click()

        # ~~ Searches for Apple stock for the last 30 days

        try:
            self.browser.find_element_by_id("longest_bullish")
        except NoSuchElementException:
            self.fail("Longest Bullish -value was not found!")

        try:
            self.browser.find_element_by_id("history_by_volume")
        except NoSuchElementException:
            self.fail("History by Volume -table was not found!")

        try:
            self.browser.find_element_by_id("best_opening_price")
        except NoSuchElementException:
            self.fail("Best Opening Price -table was not found!")

        self.assertURLEqual(
            self.browser.current_url,
            self.live_server_url + f"/?stock={stock}&start_date={start_date}&end_date={end_date}"
        )

    def test_analyze_from_csv(self):
        """Test analyzing stock from csv."""

        # ~~ User should be on the front page

        dropzone = self.browser.find_element_by_id("csv-upload").find_element_by_css_selector("input[type='file']")

        with open("analyzer/functional_tests/HistoricalQuotes.csv", "r") as fp:
            file_abs_path = os.path.abspath(fp.name)

        dropzone.send_keys(file_abs_path)

        # ~~ CSV uploaded, page will reload

        try:
            self.browser.find_element_by_id("longest_bullish")
        except NoSuchElementException:
            self.fail("Longest Bullish -value was not found!")

        try:
            self.browser.find_element_by_id("history_by_volume")
        except NoSuchElementException:
            self.fail("History by Volume -table was not found!")

        try:
            self.browser.find_element_by_id("best_opening_price")
        except NoSuchElementException:
            self.fail("Best Opening Price -table was not found!")

        self.assertURLEqual(
            self.browser.current_url,
            self.live_server_url + "/"
        )

