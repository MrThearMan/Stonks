"""Create your template tags here."""

import pandas as pd
from django import template

register = template.Library()


@register.inclusion_tag("analyzer/snippets/stock_data_table.html")
def pandas_table(table: "pd.DataFrame", title: str, table_id: str):
    return {
        "table": table.to_dict("split"),
        "title": title,
        "table_id": table_id,
        "rows": len(table.index)
    }


@register.filter(name='enumerate')
def enumerate_iterable(iterable):
    return enumerate(iterable)
