from django import forms

from baweb import models
from ..utils.bootstrap import BootStrapModelForm

class StudentInfoForm(BootStrapModelForm):
    class Meta:
        model = models.StudentInfo
        fields = [ 'name', 'gender', 'email', 'phone']


class StudentUpdateForm(BootStrapModelForm):
    class Meta:
        model = models.StudentInfo
        fields = [ 'name', 'gender', 'email', 'phone']

class StudentPicForm(BootStrapModelForm):
    class Meta:
        model = models.StudentInfo
        fields = ['student_profile_pic']