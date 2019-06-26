# ACTION_CHECKBOX_NAME is unused, but should stay since its import from here
# has been referenced in documentation.
from rec.decorators import register
from rec.filters import (
    AllValuesFieldListFilter, BooleanFieldListFilter, ChoicesFieldListFilter,
    DateFieldListFilter, FieldListFilter, ListFilter, RelatedFieldListFilter,
    RelatedOnlyFieldListFilter, SimpleListFilter,
)
from rec.helpers import ACTION_CHECKBOX_NAME
from rec.options import (
    HORIZONTAL, VERTICAL, ModelRec, StackedInline, TabularInline,
)
from rec.sites import RecSite, site
from django.utils.module_loading import autodiscover_modules

__all__ = [
    "register", "ACTION_CHECKBOX_NAME", "ModelRec", "HORIZONTAL", "VERTICAL",
    "StackedInline", "TabularInline", "ListFilter",
    "SimpleListFilter", "FieldListFilter", "BooleanFieldListFilter",
    "RelatedFieldListFilter", "ChoicesFieldListFilter", "DateFieldListFilter",
    "AllValuesFieldListFilter", "RelatedOnlyFieldListFilter",
]

def autodiscover():
    autodiscover_modules('rec', register_to=site)

default_app_config = 'rec.apps.RecConfig'