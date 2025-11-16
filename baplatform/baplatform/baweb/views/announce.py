from django.shortcuts import  redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from baweb import models
from ..forms.announceform import AnnounceForm

@csrf_exempt
def announce_add(request):
    '''上传通知'''
    form  = AnnounceForm(request.POST)
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    teacher = models.TeacherInfo.objects.filter(user=user).first()
    if form.is_valid():
        obj = form.save(commit=False)
        if obj.course.teacher != teacher:
            return JsonResponse({"status":False, "msg":"没有权限"}) 
        obj.teacher = teacher
        obj.save()
        return JsonResponse({"status":True})
    return JsonResponse({"status":False, "msg":"加载失败"}) 

@csrf_exempt
def announce_edit(request, id):
    '''更新通知'''
    old_obj = models.Announce.objects.filter(id=id).first()
    form = AnnounceForm(request.POST ,instance=old_obj)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.save()
        return JsonResponse({"status":True})
    return JsonResponse({"status":False})  

@csrf_exempt
def announce_delete(request, id):
    '''删除通知'''
    models.Announce.objects.filter(id=id).delete()
    return redirect('/announce/')  
