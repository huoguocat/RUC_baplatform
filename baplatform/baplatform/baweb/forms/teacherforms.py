from django import forms

from baweb import models
from ..utils.bootstrap import BootStrapForm, BootStrapModelForm

class TeacherInfoForm(BootStrapModelForm):
    class Meta:
        model = models.TeacherInfo
        fields = [ 'name', 'gender', 'email', 'phone']


class TeacherUpdateForm(BootStrapModelForm):
    class Meta:
        model = models.TeacherInfo
        fields = [ 'name', 'gender', 'email', 'phone']

class TeacherPicForm(BootStrapModelForm):
    class Meta:
        model = models.TeacherInfo
        fields = ['teacher_profile_pic']