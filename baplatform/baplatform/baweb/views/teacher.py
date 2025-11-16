from django.shortcuts import render, redirect

from baweb import models
from ..forms.teacherforms import TeacherUpdateForm

def teacher_page(request, pk):
    teacherinfo = models.TeacherInfo.objects.filter(user_id=pk).first()
    return render(request,"teacher_page.html", {"teacherinfo":teacherinfo})

def teacher_info(request, pk):
    teacherinfo = models.TeacherInfo.objects.filter(user_id=pk).first() 
    return render(request, "teacher_info.html", {"teacherinfo":teacherinfo})

def teacher_edit(request, pk):
    if request.method == 'GET':
        form = TeacherUpdateForm()
        render(request, "change.html", {'form':form})
    
    obj = models.TeacherInfo.objects.filter(user_id=pk).first() 
    form = TeacherUpdateForm(request.POST, instance=obj)
    if form.is_valid():
        profile = form.save(commit=False)
        #print(request.FILES)
        if 'teacher_profile_pic' in request.FILES:
            #print("加载图片")
            profile.teacher_profile_pic = request.FILES['teacher_profile_pic']
        profile.user = obj.user
        profile.save()
        return redirect('/teacher/{}/info'.format(pk))
    return render(request,"change.html", {'form':form})