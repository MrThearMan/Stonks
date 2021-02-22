"""Create your views here."""

import json
from django.shortcuts import render
from django.conf import settings

from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse

from . import forms as analyzer_forms
from . import utils


def index(request):
    """Front page view.

    :param request: Request for page.
    :return: HTTP response.
    """

    form = analyzer_forms.SearchForm(request.GET or None)

    err = None
    longest_bullish = None
    history_by_volume = None
    best_opening_price = None
    history_by_volume_rows = 0
    best_opening_price_rows = 0

    # Search by API
    if form.is_valid():
        data = form.cleaned_data
        try:
            data = utils.fetch_stock_history(**data)
            longest_bullish, history_by_volume, best_opening_price = utils.analyze_stock_data(data)
            history_by_volume_rows = len(history_by_volume.split("<tr>"))
            best_opening_price_rows = len(best_opening_price.split("<tr>"))

        except ConnectionError as error_con:
            settings.LOGGER.error(_(f"{error_con}"))
            err = _(f"Error: Request failed: {error_con}.")

        except ValueError as error_val:
            settings.LOGGER.error(_(f"During API search: {error_val}. Search failed."))
            err = _(f"Error: {error_val}")

    # Reading from a file
    elif request.method == "POST":
        try:
            data = utils.stock_data_from_csv(file=request.FILES.get("file"))
            longest_bullish, history_by_volume, best_opening_price = utils.analyze_stock_data(data)
            history_by_volume_rows = len(history_by_volume.split("<tr>"))
            best_opening_price_rows = len(best_opening_price.split("<tr>"))

        except KeyError as error_key:
            settings.LOGGER.error(_(f"During csv import: Key {error_key} not found. Import halted."))
            err = _(f"Error: Key {error_key} not found in CSV.")

        except ValueError as error_val:
            settings.LOGGER.error(_(f"During csv import: {error_val}. Import halted."))
            err = _(f"Error: {error_val} in CSV.")

    context = {
        "form": form,
        "error": err,
        "longest_bullish": longest_bullish,
        "history_by_volume": history_by_volume,
        "history_by_volume_rows": history_by_volume_rows,
        "best_opening_price": best_opening_price,
        "best_opening_price_rows": best_opening_price_rows,
    }
    return render(request, template_name="analyzer/index.html", context=context)


def filter_stocks(request):
    """Filter and autocomplete stocks according to what the user types.

    :param request: Request for page.
    :return: HTTP response.
    """

    q = request.GET.get("q").upper()

    with open("analyzer/static/analyzer/json/stocks.json", "r") as f:
        data = json.load(f)

    data[:] = [stock for stock in data if stock.startswith(q)]

    return JsonResponse(data, safe=False)
