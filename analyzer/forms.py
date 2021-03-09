"""Create your forms here"""

from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, HTML


class SearchForm(forms.Form):
    """Form to search for stock data."""

    stock_symbol = forms.CharField(
        label=_("Stock"),
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'off',
            }
        ),
        max_length=10,
        required=True
    )
    start_date = forms.DateField(
        label=_("Start Date"),
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%d %m %Y"
        ),
        required=True
    )
    end_date = forms.DateField(
        label=_("End Date (optional)"),
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%d %m %Y"
        ),
        required=False
    )

    helper = FormHelper()
    helper.form_method = 'GET'
    helper.layout = Layout(
        Div(
            Div(
                "stock_symbol",
                css_class="col-sm"
            ),
            css_class="row"
        ),
        Div(
            Div(
                "start_date",
                Div(
                    HTML(
                        f'<span id="id_ytd"><button type="button" class="btn btn-link p-0">'
                        f'<abbr title="Year-to-date = {_("From first trading day of the current calendar year.")}">'
                        f'YTD</abbr>'
                        f'</button></span>'
                        f'<span id="id_1year"><button type="button" class="btn btn-link p-0">1Y</button></span>'
                        f'<span id="id_6month"><button type="button" class="btn btn-link p-0">6M</button></span>'
                        f'<span id="id_1month"><button type="button" class="btn btn-link p-0">1M</button></span>'
                        f'<span id="id_5day"><button type="button" class="btn btn-link p-0">5D</button></span>'
                    ),
                    css_id="div_id_select_predefined"
                ),
                css_class="col-sm"
            ),
            Div(
                "end_date",
                css_class="col-sm"
            ),
            css_class="row"
        ),
        HTML(
            f'<button type="submit" class="btn btn-success btn-block mt-3">{_("Search")}</button>'
        )
    )