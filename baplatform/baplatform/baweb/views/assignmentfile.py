from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
from baweb import models
from ..forms.assignmentforms import AssignmentFileForm, AssignmentSubmitForm, AssignmentMarkForm

def file_list(request, id):
    assignment = models.Assignment.objects.filter(id=id).first()
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    if user.type == 2:
        file_list = models.AssignmentFile.objects.filter(assignment=assignment).all()
    else: 
        student = models.StudentInfo.objects.filter(user=user).first()
        file_list = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).all()
    return render(request, 'assignmentfile_list.html', {"file_list":file_list, 'id':id})

@csrf_exempt
def file_add(request, id):
    '''上传任务文档'''
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    if user.type == 2:
        form = AssignmentFileForm(request.POST, request.FILES)
    elif user.type == 1:
        form = AssignmentSubmitForm(request.POST, request.FILES)
    if form.is_valid():
        names = request.POST.getlist("file_name")
        files = request.FILES.getlist("file")
        assignment = models.Assignment.objects.filter(id=id).first()
        for i in range(len(files)):
            if user.type == 1:
                student = models.StudentInfo.objects.filter(user=user).first()
                models.AssignmentSubmit.objects.create(file_name=names[i], assignment=assignment, file=files[i], student=student)
            elif user.type == 2:
                models.AssignmentFile.objects.create(file_name=names[i], assignment=assignment, file=files[i])      
        return JsonResponse({"status": True})
    return JsonResponse({"status": False})

def file_update(request, id, fid):
    '''更新任务文档'''
    title = "更新任务文档"
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    if user.type == 2:
        old_obj = models.AssignmentFile.objects.filter(id=fid).first()
    elif user.type == 1:
        old_obj = models.AssignmentSubmit.objects.filter(id=fid).first()
    if request.method == 'GET':
        if user.type == 2:
            form = AssignmentFileForm(instance=old_obj)
        elif user.type == 1:
            form = AssignmentSubmitForm(instance=old_obj)
        context = {
            'form': form,
            'title': title,
        }
        return render(request, "change.html",context)
    if user.type == 2:
        form = AssignmentFileForm(request.POST, request.FILES, instance=old_obj)
    elif user.type == 1:
        form = AssignmentSubmitForm(request.POST, request.FILES, instance=old_obj)
    if form.is_valid():
        obj = form.save(commit=False)
        assignment = models.Assignment.objects.filter(id=id).first()
        obj.assignment = assignment
        if user.type == 1:
            student = models.StudentInfo.objects.filter(user=user).first()
            obj.student = student
        obj.save()
    return redirect('/assignment/{}/file/list'.format(id))   

@csrf_exempt
def file_delete(request, id, fid):
    '''删除任务文档'''
    info_dict = request.session.get('info')
    user = models.User.objects.filter(id=info_dict['id']).first()
    dir = 'media/'
    if user.type == 2:
        deletefile = models.AssignmentFile.objects.filter(id=fid)
        for i in deletefile:
            ##print(dir+'{}'.format(i.file.name))
            os.remove(dir+'{}'.format(i.file.name))
        models.AssignmentFile.objects.filter(id=fid).delete()
    elif user.type == 1:
        deletefile = models.AssignmentSubmit.objects.filter(id=fid)
        for i in deletefile:
            ##print(dir+'{}'.format(i.file.name))
            os.remove(dir+'{}'.format(i.file.name))
        models.AssignmentSubmit.objects.filter(id=fid).delete()
    return redirect('/assignment/{}/page'.format(id))


@csrf_exempt
def submit_info(request, id):
    assignment = models.Assignment.objects.filter(id=id).first()
    total_submit_list = models.AssignmentSubmit.objects.filter(assignment=assignment).all()
    studentscourse = models.StudentCourse.objects.filter(course=assignment.course).all()
    unsubmit_student_list = []
    count = 0
    for studentcourse in studentscourse:
        unsubmit_student_list.append(studentcourse.student)
        count += 1
    total_number = count
    students = []
    for submit in total_submit_list:
        if submit.student not in students:
            students.append(submit.student)
            if assignment.is_group:
                groupmember = models.GroupMember.objects.filter(student=submit.student).first()
                group = groupmember.group
                groupmembers = models.GroupMember.objects.filter(group=group).all()
                for member in groupmembers:
                    unsubmit_student_list.remove(member.student)
                    count -= 1
            else:
                unsubmit_student_list.remove(submit.student)
                count -= 1
    unsubmit_number = count
    series = [
                {
                    "name": '人数',
                    "type": 'pie',
                    "radius": '50%',
                    "data": [
                        { "value": total_number-unsubmit_number, "name": '已提交' },
                        { "value": unsubmit_number, "name": '未提交' },
                    ],
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
    return JsonResponse({"status":True, "series":series})
    

def unsubmit_list(request, id):
    '''计算所有未提交作业的人数并且给出名单'''
    assignment = models.Assignment.objects.filter(id=id).first()
    total_submit_list = models.AssignmentSubmit.objects.filter(assignment=assignment).all()
    studentscourse = models.StudentCourse.objects.filter(course=assignment.course).all()
    unsubmit_student_list = []
    count = 0
    for studentcourse in studentscourse:
        unsubmit_student_list.append(studentcourse.student)
        count += 1
    students = []
    for submit in total_submit_list:
        if submit.student not in students:
            students.append(submit.student)
            if assignment.is_group:
                groupmember = models.GroupMember.objects.filter(student=submit.student).first()
                group = groupmember.group
                groupmembers = models.GroupMember.objects.filter(group=group).all()
                for member in groupmembers:
                    unsubmit_student_list.remove(member.student)
                    count -= 1
            else:
                unsubmit_student_list.remove(submit.student)
                count -= 1
    context = {
        'count':count, 
        'unsubmit_student_list':unsubmit_student_list,
    }
    return render(request, 'unsubmit_list.html', context)

def submitfile_list(request, id, sid):
    assignment = models.Assignment.objects.filter(id=id).first()
    student = models.StudentInfo.objects.filter(user_id=sid).first()
    submit_list = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).all()
    return render(request, 'submitfile_list.html', {'submit_list':submit_list})
@csrf_exempt
def marks_enter(request, id, sid):
    '''打分'''
    if request.method == 'GET':
        form = AssignmentMarkForm
        content = {
            "title":"打分",
            "form": form, 

        }
        return render(request, 'change.html', content)
    assignment = models.Assignment.objects.filter(id=id).first()
    student = models.StudentInfo.objects.filter(user_id=sid).first()
    obj = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).first()
    form = AssignmentMarkForm(request.POST, instance=obj)
    if form.is_valid():
        assignmentsubmit = form.save(commit=False)
        assignmentsubmit.assignment = assignment
        assignmentsubmit.student = student
        assignmentsubmit.save()
    return redirect("/assignment/{}/page".format(id))

@csrf_exempt
def marks_get(request, id, uid):
    assignment = models.Assignment.objects.filter(id=id).first()
    student = models.StudentInfo.objects.filter(user_id=uid).first()
    exists = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).exists()
    if exists:
        file_with_marks = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).first()
        get_mark = file_with_marks.marks
        max_mark = file_with_marks.max_marks
        marks = "{}/{}".format(get_mark, max_mark)
        return JsonResponse({"status":True, "marks":marks})

    return JsonResponse({"status":False})

@csrf_exempt
def files_get(request, id, uid):
    assignment = models.Assignment.objects.filter(id=id).first()
    student = models.StudentInfo.objects.filter(user_id=uid).first()
    exists = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).exists()
    if exists:
        files = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).all()
        count = models.AssignmentSubmit.objects.filter(assignment=assignment, student=student).count()
        urls = []
        names = []
        for file in files:
            urls.append(file.file.url)
            names.append(file.file_name)
        return JsonResponse({"status":True, "urls":urls, "names":names,  "count":count})
    return JsonResponse({"status":False})

