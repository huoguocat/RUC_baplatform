from django.shortcuts import render, redirect

from baweb import models
from ..forms.studentforms import StudentUpdateForm

def student_page(request, pk):
    return render(request,"student_page.html", {"pk":pk})

def student_info(request, pk):
    studentinfo = models.StudentInfo.objects.filter(user_id=pk).first() 
    return render(request, "student_info.html", {"studentinfo":studentinfo})

def student_edit(request, pk):
    if request.method == 'GET':
        form = StudentUpdateForm()
        render(request, "change.html", {'form':form})
    
    obj = models.StudentInfo.objects.filter(user_id=pk).first() 
    form = StudentUpdateForm(request.POST, instance=obj)
    #print(form)
    if form.is_valid():
        profile = form.save(commit=False)
        #print(request.FILES)
        if 'student_profile_pic' in request.FILES:
            #print("加载图片")
            profile.student_profile_pic = request.FILES['student_profile_pic']
        profile.save()
        return redirect('/student/{}/info'.format(pk))
    return render(request,"change.html", {'form':form})