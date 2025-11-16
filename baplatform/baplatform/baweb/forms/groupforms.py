from django import forms

from baweb import models
from ..utils.bootstrap import BootStrapModelForm, BootStrapForm

class GroupForm(BootStrapModelForm):
    class Meta:
        model = models.Group
        fields = ['name']

class GroupMemberForm(BootStrapForm):
    username = forms.CharField(
        label="学生学号",
        widget = forms.TextInput,
        required=True
    )