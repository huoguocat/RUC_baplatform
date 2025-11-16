from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from baweb import models
from baweb.forms.assignmentforms import AssignmentFileForm, AssignmentSubmitForm, AssignmentMarkForm
from ..forms.courseforms import CourseAssignmentForm
from ..forms.userforms import UserChangePasswordForm


def assignment_list(request, id):
    '''任务列表'''
    course = models.Course.objects.filter(id=id).first()
    assignment_list = models.Assignment.objects.filter(course=course).all()
    info = request.session.get("info", "")
    username = info['name']
    user_id = info['id']
    changepwd_form = UserChangePasswordForm
    course = models.Course.objects.filter(id=id).first()
    user = models.User.objects.filter(id=user_id).first()
    assignment_add_form = CourseAssignmentForm
    if user.type == 2:
        is_teacher = 1
        if course.teacher.user != user:
            return redirect('/')
    else:
        is_teacher = 0
        student = models.StudentInfo.objects.filter(user=user).first()
        exists = models.StudentCourse.objects.filter(student=student,course=course)
        if not exists:
            return redirect('/')
    content = {
        "username": username,
        "id": user_id,
        "changepwd_form": changepwd_form,
        "course": course,
        "is_teacher": is_teacher,
        "assignment_list": assignment_list,
        "assignment_add_form": assignment_add_form
    }
    return render(request, 'assignment.html', content)


@csrf_exempt
def assignment_add(request, id):
    form = CourseAssignmentForm(request.POST)
    # print(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        course = models.Course.objects.filter(id=id).first()
        obj.course = course
        obj.save()
        return JsonResponse({"status": True})
    return JsonResponse({"status": False})


@csrf_exempt
def assignment_des_update(request, id):
    des_richtext = request.POST.get('description_richtext')
    models.Assignment.objects.filter(id=id).update(
        description_richtext=des_richtext)
    return JsonResponse({"status": True})


def assignment_update(request, id, aid):
    '''更新任务'''
    title = "更新任务"
    old_obj = models.Assignment.objects.filter(id=aid).first()
    if request.method == 'GET':
        form = CourseAssignmentForm(instance=old_obj)
        context = {
            'form': form,
            'title': title,
        }
        return render(request, "change.html", context)
    form = CourseAssignmentForm(request.POST, instance=old_obj)
    if form.is_valid():
        obj = form.save(commit=False)
        course = models.Course.objects.filter(id=id).first()
        obj.course = course
        obj.save()
    return redirect('/course/{}/assignment/list'.format(id))


def assignment_delete(request, id, aid):
    '''删除任务'''
    models.Assignment.objects.filter(id=aid).delete()
    return redirect('/course/{}/assignment/list'.format(id))


def assignment_page(request, id):
    info = request.session.get("info", "")
    username = info['name']
    user_id = info['id']
    user = models.User.objects.filter(id=info['id']).first()
    assignment = models.Assignment.objects.filter(id=id).first()
    changepwd_form = UserChangePasswordForm
    if user.type == 2:
        is_teacher = 1
        total_submit_list = models.AssignmentSubmit.objects.filter(
            assignment=assignment).all()
        students = []
        submit_list = []
        for submit in total_submit_list:
            if submit.student not in students:
                submit_list.append(submit)
                students.append(submit.student)
    elif user.type == 1:
        students = []
        student = models.StudentInfo.objects.filter(user=user).first()
        submit_list = models.AssignmentSubmit.objects.filter(
            assignment=assignment, student=student).all()
        is_teacher = 0
    file_list = models.AssignmentFile.objects.filter(
        assignment=assignment).all()
    assignmentfileform = AssignmentFileForm
    assignmentsubmitform = AssignmentSubmitForm
    marksform = AssignmentMarkForm
    content = {
        "assignment": assignment,
        "is_teacher": is_teacher,
        "username": username,
        "id": user_id,
        "changepwd_form": changepwd_form,
        "course": assignment.course,
        "file_list": file_list,
        "assignmentfileform": assignmentfileform,
        "assignmentsubmitform": assignmentsubmitform,
        "marksform": marksform,
        "submit_list": submit_list,
        "students": students,
    }
    return render(request, 'assignment_page.html', content)


@csrf_exempt
def remind(request):
    info = request.session.get("info", "")
    user_id = info['id']
    user = models.User.objects.filter(id=user_id).first()
    if user.type == 1:
        course_list = []
        student = models.StudentInfo.objects.filter(user=user).first()
        studentcourse = models.StudentCourse.objects.filter(
            student=student).all()
        for obj in studentcourse:
            course_list.append(obj.course)
    elif user.type == 2:
        teacher = models.TeacherInfo.objects.filter(user=user).first()
        course_list = models.Course.objects.filter(teacher=teacher).all()
    ddl_list = []
    assignment_name_list = []
    assingment_url_list = []
    count = 0
    for course in course_list:
        assignment_list = models.Assignment.objects.filter(course=course).all()
        for assignment in assignment_list:
            year, month, date = str(assignment.ddl).split('-')
            ddl = "{}-{}-{}".format(int(year), int(month), int(date))
            ddl_list.append(ddl)
            assignment_name_list.append(assignment.name)
            assingment_url_list.append("/assignment/{}/page".format(assignment.id))
            count += 1
    if count == 0:
        res = {
            "status": False
        }
    else:
        res = {
            "status": True,
            "count": count, 
            "ddls": ddl_list,
            "names": assignment_name_list,
            "urls": assingment_url_list, 
        }
    print(count)
    return JsonResponse(res)
