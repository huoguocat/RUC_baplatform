from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse

from baweb import models
from ..forms.courseforms import CourseCommentForm

def comment_list(request, id):
    title = '任务评价'
    assignment = models.Assignment.objects.filter(id=id).first()
    comment_list = models.AssignmentComment.objects.filter(assignment=assignment).all()
    context = { 
        "comment_list":comment_list,
        'id':id,
        'title':title,
    }
    return render(request, 'comment_list.html', context)

@csrf_exempt
def comment_add(request, id):
    '''上传评论'''
    form  = CourseCommentForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        course = models.Course.objects.filter(id=id).first()
        obj.course = course
        info_dict = request.session.get('info')
        user = models.User.objects.filter(id=info_dict['id']).first()
        obj.user = user
        obj.save()
        return JsonResponse({"status":True})
    return JsonResponse({"status":False}) 

@csrf_exempt
def comment_edit(request, id, cid):
    '''编辑评论'''
    old_obj = models.CourseComment.objects.filter(id=cid).first()
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    if user != old_obj.user:
        return HttpResponse("没有编辑权限")
    form = CourseCommentForm(request.POST ,instance=old_obj)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.save()
        return JsonResponse({"status":True})
    return JsonResponse({"status":False})  

@csrf_exempt
def comment_delete(request, id, cid):
    '''删除评论'''
    old_obj = models.CourseComment.objects.filter(id=cid).first()
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    if user.type == 1:
        if user != old_obj.user:
            return HttpResponse("没有删除权限")
    models.CourseComment.objects.filter(id=cid).delete()
    return redirect('/course/{}/comment/list'.format(id))  

def mycomment_list(request, id):
    title = '我的评价'
    assignment = models.Assignment.objects.filter(id=id).first()
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    comment_list = models.AssignmentComment.objects.filter(assignment=assignment, user=user).all()
    context = { 
        "comment_list":comment_list,
        'id':id,
        'title':title,
    }
    return render(request, 'comment_list.html', context)