from baweb import models
from ..utils.bootstrap import BootStrapModelForm


class AnnounceForm(BootStrapModelForm):
    class Meta:
        model = models.Announce
        fields = ['announcement', 'course']