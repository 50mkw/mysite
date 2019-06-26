from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RecConfig(AppConfig):
    """Simple AppConfig which does not do automatic discovery."""

    default_site = 'rec.sites.RecSite'
    name = 'rec'
    verbose_name = _("Reconciliation")
