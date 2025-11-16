from django import forms

from baweb import models
from ..utils.bootstrap import BootStrapModelForm

class CourseForm(BootStrapModelForm):
    class Meta:
        model = models.Course
        fields = ['name', 'course_profile_pic']

class CoursePicForm(BootStrapModelForm):
    class Meta:
        model = models.Course
        fields = ['course_profile_pic']

class CourseFileForm(BootStrapModelForm):
    class Meta:
        model = models.CourseFiles
        fields = ['file', 'file_name']

class CourseAssignmentForm(BootStrapModelForm):
    class Meta:
        model = models.Assignment
        fields =  ['name', 'ddl', 'is_group']

class CourseStudentImportForm(forms.Form):
    file = forms.FileField(label='学生表')

class CourseCommentForm(BootStrapModelForm):
    class Meta:
        model = models.CourseComment
        fields = ['comment']