"""Create your views here."""

import json
import pandas as pd
from functools import wraps

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse_lazy

from django.views import generic as generic_views

from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse

from . import forms as analyzer_forms
from . import utils


def render_with_error_in_context_on_fail(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except utils.FetchError as error:
            view = args[0]  # self
            return view.render_to_response(view.get_context_data(error=error))

    return wrapper


class IndexView(generic_views.FormView):
    template_name = "analyzer/index.html"
    form_class = analyzer_forms.SearchForm
    success_url = reverse_lazy("analyzer:index")

    def get(self, request, *args, **kwargs):
        """Search with API."""
        # return super().post(request, *args, **kwargs)

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return super().get(request, *args, **kwargs)

    @render_with_error_in_context_on_fail
    def post(self, request, *args, **kwargs):
        """Data added from file."""
        data = utils.stock_data_from_csv(file=request.FILES.get("file"))
        analysis = self.analyze_stock_data(data)
        return self.render_to_response(self.get_context_data(data=analysis))

    @render_with_error_in_context_on_fail
    def form_valid(self, form):
        cleaned_data = form.cleaned_data
        data = utils.fetch_stock_history(**cleaned_data)
        analysis = self.analyze_stock_data(data)
        return self.render_to_response(self.get_context_data(data=analysis))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["data"] = self.request.GET or None

        # super().get_form_kwargs() will add request.FILES to kwargs on POST
        # but if it is present, form fields wil try to validate.
        # POST is used to read data from file, so fields should not validate.
        if "files" in kwargs:
            kwargs.pop("files")

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {"error": None, "data": None} | context

    @staticmethod
    def analyze_stock_data(data: "pd.DataFrame", dateformat: str = "%d.%m.%Y"):
        return {
            "longest_bullish": utils.longest_bullish_streak(data),
            "history_by_volume": utils.history_by_volume_and_price_delta(data, dateformat),
            "best_opening_price": utils.best_opening_price_compared_to_five_day_SMA(data, dateformat),
        }



def filter_stocks(request):

    q = request.GET.get("q").upper()

    with open("analyzer/static/analyzer/json/stocks.json", "r") as f:
        data = json.load(f)

    data[:] = [stock for stock in data if stock.startswith(q)]

    return JsonResponse(data, safe=False)
