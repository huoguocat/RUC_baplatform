from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from baweb import models
#coding=UTF-8

def home_page(request):
    return render(request, 'home.html')

@csrf_exempt
def home_load(request):
    course_list = models.Course.objects.filter()
    imgs = []
    coursename = []
    courseid = []
    coursenumber = 0
    for course in course_list:
        exists = models.TeacherDisabled.objects.filter(teacher=course.teacher.user)
        if exists:
            continue
        if course.course_profile_pic:
            imgs.append(course.course_profile_pic.url)
        else:
            imgs.append("")
        courseid.append(course.id)
        coursename.append(course.name)
        coursenumber = coursenumber+1
    teacher_list = models.TeacherInfo.objects.filter()
    descriptions = []
    teacherpic = []
    teachernumber = 0
    teacher_names = []
    teacher_ids = []
    for teacher in teacher_list:
        exists = models.TeacherDisabled.objects.filter(teacher=teacher.user)
        if exists:
            continue
        teacher_ids.append(teacher.user_id)
        teacher_names.append(teacher.name)
        descriptions.append(teacher.description_richtext)
        if teacher.teacher_profile_pic:
            teacherpic.append(teacher.teacher_profile_pic.url)
        else:
            teacherpic.append("")
        teachernumber += 1
    if coursenumber != 0 and teachernumber != 0: 
        res = {
            "status":True,
            "coursename": coursename,
            "courseid":  courseid,
            "imgs":imgs,
            "coursenumber": min(coursenumber, 8),
            "teachernumber": teachernumber,
            "descriptions": descriptions,  
            "teacherpic":teacherpic, 
            "teachernames": teacher_names,
            "teacherids": teacher_ids,
        }
    else:
        res = {
            "status":False,
        }
    return JsonResponse(res)