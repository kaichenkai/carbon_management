from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoefficientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'coefficients'
    verbose_name = _('系数管理')
