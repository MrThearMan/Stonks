"""Create your utility functions here."""

import re
import requests
import datetime
import pandas as pd
import numpy as np

from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext as _


def format_stock_data(data):
    """Format stock data with correct types and order by date (ascending).

    :param data: Unformatted Stock data.
    :type data: pd.DataFrame
    :return: Formatted Stock data.
    :rtype: pd.DataFrame
    :raises KeyError: One of the columns: "Date", "Volume", "Open", "Close/Last", "High" or "Low" was not found.
                      Check that provided csv has correct headers.
                      Check for leading or trailing whitespace in column headers.
    :raises ValueError: One of the values for a column was not wat expected.
                        "Date"-column values should be in format '%m/%d/%Y'
                        "Volume"-column values should be integers
                        "Open", "Close/Last", "High" and "Low" -columns should be dollar amounts ($xx.yy)
    """

    # Copied so that formatted data can be separated from unformatted if wanted
    data = data.copy()

    data.replace(to_replace="N/A", value=np.nan, inplace=True)

    # Convert columns to correct types
    data["Date"] = pd.to_datetime(data['Date'], format='%m/%d/%Y')
    data["Volume"] = pd.to_numeric(data["Volume"])

    for column in ["Open", "Close/Last", "High", "Low"]:
        data[column] = data[column].apply(lambda x: Decimal(re.sub(r"[^\d.,]", "", x)))

    return data.sort_values(by="Date").reset_index(drop=True)


def fetch_stock_history(stock, start_date, end_date=None, **kwargs):
    """Fetch stock history for wanted stock. Sorted by date (ascending).

    :param stock: Symbol of the stock to fetch.
    :type stock: str
    :param start_date: Start date of the stock history lookup.
    :type start_date: datetime.date
    :param end_date: End date of the stock history lookup.
    :type end_date: datetime.date or None
    :return: Pandas Dataframe of the stock history.
    :rtype: pd.DataFrame
    :raises ConnectionError: Request failed.
    :raises ValueError: No data was fetched. Possible improper stock symbol.
    """

    start_date = start_date.strftime("%Y-%m-%d")

    if end_date is None:
        end_date = datetime.date.today().strftime("%Y-%m-%d")
    else:
        end_date = end_date.strftime("%Y-%m-%d")

    # required headers for nasdaq.com API CORS policy
    headers = {
        "Accept-Encoding": "deflate",
        "Connection": "keep-alive",
        "User-Agent": "Script"
    }

    try:
        data = requests.get(f"https://www.nasdaq.com/api/v1/historical/{stock}/stocks/{start_date}/{end_date}",
                            headers=headers)
    except requests.RequestException as e:
        settings.LOGGER(_(f"REQUEST FOR STOCK '{stock}' FAILED."))
        raise ConnectionError(e)

    if not data.text.strip():
        raise ValueError(_(f"No stock data for stock '{stock}'."))

    data_rows = data.text.strip().split("\n")
    data_columns = data_rows.pop(0).split(", ")

    stock_df = pd.DataFrame(columns=data_columns)

    for i, row in enumerate(data_rows):
        stock_df.loc[i] = row.split(", ")

    stock_df = format_stock_data(stock_df)

    return stock_df


def stock_data_from_csv(file):
    """Read stock data from file.

    :param file: File location.
    :type file: str
    :return: Dataframe constructed form the CSV
    :rtype: pd.DataFrame
    :raises FileNotFoundError: File not found.
    """

    data = pd.read_csv(file)

    # Strip whitespace from column headers
    data.rename(columns=lambda x: x.strip(), inplace=True)

    # Strip whitespace from data values
    for column in data.columns:
        try:
            data[column] = data[column].str.strip()
        except AttributeError:
            pass  # if numeric dtype

    return format_stock_data(data)


def format_table(html_string):
    """Format table as bootstrap table.

    - Adds scrope="row" and scrope="col" as well as "#" to index header

    :param html_string: String representation of the table html.
    :type html_string: str
    :return: Formatted html.
    :rtype: str
    """

    volumes = html_string.split("tr")
    volumes[1] = volumes[1].replace('<th><', '<th>#<')
    volumes = [volume.replace('<th>', '<th scope="row">') for volume in volumes]
    volumes[1] = volumes[1].replace('scope="row"', 'scope="col"')
    html_string = "tr".join(volumes)

    return html_string


def longest_bullish_streak(data):
    """How many days was the longest bullish (upward) trend within a given date range?

    - Definition of an upward trend shall be: “Closing price of day N is higher than closing price of day N-1”
    - Both start and end date shall be included to the date range.

    :param data: Stock data.
    :type data: pd.DataFrame
    :return: The max amount of days the stock price was increasing in a row.
    :rtype: int
    """

    longest_streak = 0
    current_streak = 1  # start day shall be included
    last_price = data["Close/Last"][0]

    for current_price in data["Close/Last"]:
        if current_price > last_price:
            current_streak += 1
            if current_streak > longest_streak:
                longest_streak = current_streak
        else:
            current_streak = 1
        last_price = current_price

    return longest_streak


def history_by_volume_and_price_delta(data):
    """Sort stock history by the highest trading volume and the most significant stock price change within a day.

    - If two dates have the same volume, the one with the more significant price change should come first

    :param data: Stock data.
    :type data: pd.DataFrame
    :return: Dates, Volumes and Price Changes sorted first by Price Change and then Volume (decending)
    :rtype: pd.DataFrame
    """

    # Prevent changes to original
    data = data.copy()

    # Drops in stock price are equally significant as increaces -> abs
    data["Price_change"] = (data["High"] - data["Low"]).abs()
    data.drop(columns=["Close/Last", "Open", "High", "Low"], inplace=True)

    # Mergesort should be used so that the effects of price delta sort are maintained after volume sort
    data.sort_values(by="Price_change", ascending=False, kind="mergesort", inplace=True)
    data.sort_values(by="Volume", ascending=False, kind="mergesort", inplace=True)
    data.reset_index(drop=True, inplace=True)

    return data


def best_opening_price_compared_to_five_day_SMA(data):
    """Sort stock history by the best opening price compared to 5 days simple moving average (SMA).

    - SMA: Average of the five most recent daily closing prices.

    :param data: Stock data.
    :type data: pd.DataFrame
    :return: Dates and Price Change Percentages sorted by the latter.
    :rtype: pd.DataFrame
    """

    # Prevent changes to original
    data = data.copy()

    # Rolling average
    data["SMA"] = data["Close/Last"].rolling(window=5).mean()
    data["SMA"] = data["SMA"].apply(lambda x: Decimal(x))  # no rounding for accuracy

    # Calculate with Decimals and convert to numeric for sorting
    data["Price_change"] = (data["Open"] / data["SMA"]) * Decimal(100) - Decimal(100)
    data["Price_change"] = pd.to_numeric(data["Price_change"], errors="coerce")
    data["Price_change"] = np.round(data["Price_change"], decimals=2)

    data.drop(columns=["Close/Last", "Volume", "Open", "High", "Low", "SMA"], inplace=True)

    data.sort_values(by="Price_change", ascending=False, inplace=True)
    data.reset_index(drop=True, inplace=True)

    return data


def analyze_stock_data(data):
    """Perform analysis on given data and return html acceptable forms of analysis.

    :param data: Data to analyze.
    :type data: pd.DataFrame
    :return: Analysis results.
    :rtype: tuple[int, pd.DataFrame, pd.DataFrame]
    """

    longest_bullish = longest_bullish_streak(data)

    history_by_volume = history_by_volume_and_price_delta(data) \
        .to_html(table_id="id_history_by_volume",
                 classes=["table", "table-hover"],
                 justify="left",
                 border=0)

    history_by_volume = format_table(history_by_volume)
    history_by_volume = history_by_volume.replace("Date", _("Date"))
    history_by_volume = history_by_volume.replace("Volume", _("Volume"))
    history_by_volume = history_by_volume.replace("Price_change", _("Price Change ($)"))

    best_opening_price = best_opening_price_compared_to_five_day_SMA(data) \
        .to_html(table_id="best_opening_price",
                 classes=["table", "table-hover"],
                 justify="left",
                 border=0)

    best_opening_price = format_table(best_opening_price)
    best_opening_price = best_opening_price.replace("Date", _("Date"))
    best_opening_price = best_opening_price.replace("Price_change", _("Price Change (%)"))

    return longest_bullish, history_by_volume, best_opening_price

