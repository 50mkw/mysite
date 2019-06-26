from django.core.exceptions import SuspiciousOperation


class DisallowedModelRecLookup(SuspiciousOperation):
    """Invalid filter was passed to rec view via URL querystring"""
    pass


class DisallowedModelRecToField(SuspiciousOperation):
    """Invalid to_field was passed to rec view via URL query string"""
    pass
