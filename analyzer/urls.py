"""Analyzer URL Configuration"""


from django.urls import path

from . import views as analyzer_views


app_name = "analyzer"

urlpatterns = [
    path("", analyzer_views.IndexView.as_view(), name="index"),
    path("filter-stocks/", analyzer_views.filter_stocks, name="filter_stocks")
]
