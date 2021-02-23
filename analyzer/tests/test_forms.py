"""Test your forms here."""

from django import test
from django.urls import reverse, resolve
from django.utils.translation import gettext_lazy as _

from analyzer import forms as analyzer_forms


class TestForms(test.TestCase):
    """Test analyzer forms."""
