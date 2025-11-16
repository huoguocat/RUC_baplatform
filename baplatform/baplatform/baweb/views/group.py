from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse

from baweb import models
from ..forms.userforms import UserChangePasswordForm
from ..forms.groupforms import GroupForm, GroupMemberForm

def group_list(request, id):
    '''小组列表'''
    course = models.Course.objects.filter(id=id).first()
    group_list = models.Group.objects.filter(course=course).all()
    info_dict = request.session.get('info')
    username = info_dict['name']
    user_id = info_dict['id']
    changepwd_form = UserChangePasswordForm
    groupform = GroupForm
    user = models.User.objects.filter(id=user_id).first()
    if user.type == 2:
        is_teacher = True
        if course.teacher.user != user:
            return redirect('/')
    else:
        student = models.StudentInfo.objects.filter(user=user).first()
        exists = models.StudentCourse.objects.filter(student=student,course=course)
        is_teacher = False
        if not exists:
            return redirect('/')
    content = {
        "username": username,
        "id": user_id,
        "changepwd_form": changepwd_form,
        "course": course,
        "group_list":group_list,
        "groupform": groupform,
        "is_teacher": is_teacher,
    }
    return render(request, 'group_list.html', content)

@csrf_exempt
def group_add(request, id):
    '''新建小组'''
    course = models.Course.objects.filter(id=id).first()
    form = GroupForm(data=request.POST)
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    student = models.StudentInfo.objects.filter(user=user).first()
    exists = models.StudentCourse.objects,filter(student=student, coures=course)
    if not exists:
        return JsonResponse({"status":False})
    if form.is_valid():
        obj = form.save(commit=False)
        obj.course = course
        obj.save()
        models.GroupMember.objects.create(student=student, is_head=True, group=obj)
        return JsonResponse({"status":True})
    return JsonResponse({"status":False})

def group_delete(request, id, gid):
    course = models.Course.objects.filter(id=id).first()
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    student = models.StudentInfo.objects.filter(user=user).first()
    exists = models.StudentCourse.objects.filter(student=student, coures=course)
    if not exists:
        return redirect("/")
    group = models.Group.objects.filter(id=gid).first()
    exists = models.GroupMember.objects.filter(group=group, student=student).exists
    if not exists:
        return redirect("/")
    member = models.GroupMember.objects.filter(group=group, student=student).first()
    if not member.is_head:
        return redirect("/course/{}/group/list".format(id))
    models.Group.objects.filter(id=gid).delete()
    return redirect("/course/{}/group/list".format(id))

def member_list(request, id):
    '''小组成员列表'''
    group = models.Group.objects.filter(id=id).first()
    member_list = models.GroupMember.objects.filter(group=group).all()
    info_dict = request.session.get('info')
    username = info_dict['name']
    user_id = info_dict['id']
    changepwd_form = UserChangePasswordForm
    groupmemberform = GroupMemberForm
    user = models.User.objects.filter(id=info_dict['id']).first()
    student = models.StudentInfo.objects.filter(user=user).first()
    obj = models.GroupMember.objects.filter(student=student, group=group).first()
    if obj:
        is_head = obj.is_head
    else:
        is_head = False
    context = { 
        "username": username,
        "id": user_id,
        "changepwd_form": changepwd_form,
        "course": group.course,
        "group":group, 
        "member_list":member_list,
        "is_head":is_head, 
        "groupmemberform": groupmemberform
    }
    return render(request, 'member_list.html', context)
@csrf_exempt
def member_add(request, id):
    '''添加小组成员'''
    group = models.Group.objects.filter(id=id).first()
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    student = models.StudentInfo.objects.filter(user=user).first()
    member = models.GroupMember.objects.filter(group=group, student=student).first()
    if not member.is_head:
        return JsonResponse({"status":False,"msg":"没有权限"})
    username = request.POST.get('username')
    exists = models.User.objects.filter(username=username).exists()
    if exists:
        user = models.User.objects.filter(username=username).first()
        student = models.StudentInfo.objects.filter(user=user).first()
        if models.GroupMember.objects.filter(group=group, student=student).exists():
            return JsonResponse({"status":False, "msg":"该同学已在小组"})
        else:    
            models.GroupMember.objects.create(group=group, student=student, is_head=False)
            return JsonResponse({"status":True})
    return JsonResponse({"status":False,"msg":"学号不存在"})

   
def member_delete(request, id, sid):
    '''删除小组成员'''
    group = models.Group.objects.filter(id=id).first()
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    student = models.StudentInfo.objects.filter(user=user).first()
    member = models.GroupMember.objects.filter(group=group, student=student).first()
    if not member.is_head:
        return redirect("/group/{}/member/list".format(id))
    user = models.User.objects.filter(id=sid).first()
    student = models.StudentInfo.objects.filter(user=user).first()
    models.GroupMember.objects.filter(group=group, student=student, is_head=False).delete()
    return redirect("/group/{}/member/list".format(id))