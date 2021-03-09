"""Create your utility functions here."""

import re
import requests
import datetime
import pandas as pd
import numpy as np

from decimal import Decimal
from django.conf import settings
from django.utils.translation import gettext as _


class FetchError(Exception):
    """"""
    def __init__(self, message):
        settings.LOGGER.error(message)
        super(FetchError, self).__init__(message)


def format_stock_data(data: "pd.DataFrame") -> "pd.DataFrame":
    """Format stock data with correct types and order by date (ascending)."""

    # Copied so that formatted data can be separated from unformatted if wanted
    data = data.copy()

    try:
        data.replace(to_replace="N/A", value=np.nan, inplace=True)

        # Convert columns to correct types
        data["Date"] = pd.to_datetime(data['Date'], format='%m/%d/%Y')
        data["Volume"] = pd.to_numeric(data["Volume"])

        for column in ["Open", "Close/Last", "High", "Low"]:
            data[column] = data[column].apply(lambda x: Decimal(re.sub(r"[^\d.,]", "", x)))

        data = data.sort_values(by="Date").reset_index(drop=True)

    # One of the values for a column was not wat expected.
    # "Date" -column values should be in format '%m/%d/%Y'
    # "Volume" -column values should be integers
    # "Open", "Close/Last", "High" and "Low" -columns should be dollar amounts ($xx.yy)
    except ValueError as error:
        raise FetchError(_(f"Formatting failed: A value for a column was not what expected. {error}."))

    # One of the columns: "Date", "Volume", "Open", "Close/Last", "High" or "Low" was not found.
    # Check that provided csv has correct headers.
    # Check for leading or trailing whitespace in column headers.
    except KeyError as key:
        raise FetchError(_(f"Formatting failed: A column with key {key} was not found."))

    return data


def fetch_stock_history(stock_symbol: str, start_date: "datetime.date", end_date: datetime.date = None) -> "pd.DataFrame":

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
        data = requests.get(settings.NASDAQ_HISTORICAL_API_URL(stock_symbol, start_date, end_date), headers=headers)
    except requests.RequestException as e:
        raise FetchError(_(f"Nasdaq API did not respond. {e}."))

    if not data.text.strip():
        raise FetchError(_(f"No stock data for stock '{stock_symbol}'."))

    data_rows = data.text.strip().split("\n")
    data_columns = data_rows.pop(0).split(", ")

    stock_df = pd.DataFrame(columns=data_columns)

    for i, row in enumerate(data_rows):
        stock_df.loc[i] = row.split(", ")

    return format_stock_data(stock_df)


def stock_data_from_csv(file: str) -> "pd.DataFrame":

    try:
        data = pd.read_csv(file)
    except FileNotFoundError:
        raise FetchError(_(f"File '{file}' not found."))

    # Strip whitespace from column headers
    data.rename(columns=lambda x: x.strip(), inplace=True)

    # Strip whitespace from data values
    for column in data.columns:
        try:
            data[column] = data[column].str.strip()
        except AttributeError:
            pass  # if numeric dtype

    return format_stock_data(data)


def longest_bullish_streak(data: "pd.DataFrame") -> int:
    """How many days was the longest bullish (upward) trend in the given data?
    Both start and end date are included to the date range.
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


def history_by_volume_and_price_delta(data: "pd.DataFrame", dateformat: str = None) -> "pd.DataFrame":
    """Sort stock history by the highest trading volume and the most significant stock price change within a day.
    If two dates have the same volume, the one with the more significant price change should come first.
    """

    # Prevent changes to original
    data = data.copy()

    # Drops in stock price are equally significant as increaces -> abs
    data["Price_change"] = (data["High"] - data["Low"]).abs()
    data.drop(columns=["Close/Last", "Open", "High", "Low"], inplace=True)

    if dateformat is not None:
        data["Date"] = data["Date"].dt.strftime(dateformat)

    # Mergesort should be used so that the effects of price delta sort are maintained after volume sort
    data.sort_values(by="Price_change", ascending=False, kind="mergesort", inplace=True)
    data.sort_values(by="Volume", ascending=False, kind="mergesort", inplace=True)
    data.reset_index(drop=True, inplace=True)

    data.rename(columns={
        "Volume": _("Volume"),
        "Date": _("Date"),
        "Price_change": _("Price Change (%)")
    }, inplace=True)

    return data


def best_opening_price_compared_to_five_day_SMA(data: "pd.DataFrame", dateformat: str = None) -> "pd.DataFrame":
    """Sort stock history by the best opening price compared to 5 days simple moving average (SMA)."""

    # Prevent changes to original
    data = data.copy()

    data["SMA"] = data["Close/Last"].rolling(window=5).mean()
    data["SMA"] = data["SMA"].apply(lambda x: Decimal(x))  # no rounding for accuracy

    # Calculate with Decimals and convert to numeric for sorting
    data["Price_change"] = (data["Open"] / data["SMA"]) * Decimal(100) - Decimal(100)
    data["Price_change"] = pd.to_numeric(data["Price_change"], errors="coerce")
    data["Price_change"] = np.round(data["Price_change"], decimals=2)

    data.drop(columns=["Close/Last", "Volume", "Open", "High", "Low", "SMA"], inplace=True)

    if dateformat is not None:
        data["Date"] = data["Date"].dt.strftime(dateformat)

    data.sort_values(by="Price_change", ascending=False, inplace=True)
    data.reset_index(drop=True, inplace=True)

    data.rename(columns={
        "Date": _("Date"),
        "Price_change": _("Price Change ($)")
    }, inplace=True)

    return data

