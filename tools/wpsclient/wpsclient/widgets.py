"""Django 4.2-compatible drop-in for the old ``splitjson.widgets.SplitJSONWidget``.

The original widget came from the ``django-SplitJSONWidget-form`` git package,
which predates modern Django widget APIs and does not work on Django 4.2. This
minimal shim keeps ``wpsclient.forms`` / ``wpsclient.views`` working by rendering
the JSON value in a textarea. It accepts (and ignores) the legacy ``debug`` kwarg.
"""
import json

from django import forms


class SplitJSONWidget(forms.Textarea):
    def __init__(self, attrs=None, debug=False):
        self.debug = debug
        super().__init__(attrs=attrs)

    def format_value(self, value):
        if value in (None, ""):
            return value
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, indent=2)
            except (TypeError, ValueError):
                return value
        return value
