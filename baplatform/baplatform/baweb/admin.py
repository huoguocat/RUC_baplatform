from django.contrib import admin
from .models import TeacherInfo, Course, Assignment
# Register your models here.
admin.site.register(TeacherInfo)
admin.site.register(Course)
admin.site.register(Assignment)
