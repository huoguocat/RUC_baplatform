from baweb import models
from django.shortcuts import render, redirect
from django.shortcuts import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from baweb.forms.announceform import AnnounceForm
from baweb.forms.courseforms import CourseForm
from ..forms.userforms import UserChangePasswordForm, UserModelForm, UserLoginForm
from ..forms.studentforms import  StudentPicForm, StudentUpdateForm
from ..forms.teacherforms import  TeacherPicForm, TeacherUpdateForm
from ..utils.check_code import check_code
from io import BytesIO

# For user to sign up

@csrf_exempt
def user_signup(request):
    '''用户注册'''
    form = UserModelForm(data=request.POST)

    if form.is_valid():
        user = form.save()
        if user.type == 1:
            models.StudentInfo.objects.create(user=user)
        elif user.type == 2:
            models.TeacherInfo.objects.create(user=user)
        elif user.type == 3:
            return HttpResponse("还没有类")
            # models.StudentInfo.objects.create(user=user)
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "error": form.errors})

def user_admin(request):
    info = request.session.get("info", "")
    username = info['name']

    user = models.User.objects.filter(id=info['id']).first()
    if user.type != 3:
        return redirect("/")

    changepwd_form = UserChangePasswordForm
    teacher_list = models.TeacherInfo.objects.filter().all()
    course_list = models.Course.objects.filter().all()
    content = { 
        "username": username, 
        "id": info['id'],
        "changepwd_form":changepwd_form,
        "teacher_list": teacher_list, 
        "course_list": course_list,
    }
    return render(request, "admin.html", content)

def user_login(request):
    '''用户登录'''
    signupform =  UserModelForm()
    if request.method == 'GET':
        form = UserLoginForm()
        return render(request, "login.html", {'form': form, "signupform": signupform})

    form = UserLoginForm(data=request.POST)
    if form.is_valid():
        user_input_code = form.cleaned_data.pop("code")
        code = request.session.get("image_code", "")
        # 验证码校验
        if code.upper() != user_input_code.upper():
            form.add_error("code", "验证码错误")
            return render(request, "login.html", {'form': form, "signupform": signupform})

        user_object = models.User.objects.filter(**form.cleaned_data).first()
        # print(user_object)
        # 密码校验
        if not user_object:
            form.add_error("password", "用户名或密码错误")
            return render(request, "login.html", {'form': form, "signupform": signupform})

        exists = models.TeacherDisabled.objects.filter(teacher=user_object).exists()
        if exists:
            form.add_error("username", "账号被封，请联系管理员解封")
            return render(request, "login.html", {'form': form})
        request.session['info'] = {
            'id': user_object.id, 'name': user_object.username}
        request.session.set_expiry(60 * 60 * 24 * 7)
        if user_object.type == 3:
            return redirect('/admin/')
        return redirect('/home/')

    return render(request, "login.html", {'form': form, "signupform": signupform})


def user_logout(request):
    '''用户退出（注销）'''
    request.session.clear()
    return redirect('/')


def image_code(request):
    '''生成图片验证码'''
    # print("开始生成图片")
    img, code_str = check_code()

    # 写入到自己的session中，以便后续获取验证码再进行校验
    request.session['image_code'] = code_str
    # Session 设置60s 超时
    request.session.set_expiry(300)
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())


def user_home(request):
    info = request.session.get("info", "")
    if info == '':
        username = "来访者"
        id = -1
        is_login = False 
    else:
        username = info['name']
        id = info['id']
        is_login = True
    changepwd_form = UserChangePasswordForm
    content = { 
        "username": username, 
        "id": id,
        "changepwd_form":changepwd_form,
        "is_login": is_login
    }
    return render(request, "home.html", content)


def user_info(request, pk):
    user = models.User.objects.filter(id=pk).first()
    if user.type == 1:
        studentinfo = models.StudentInfo.objects.filter(user_id=pk).first()
        return render(request, "student_info.html", {"studentinfo": studentinfo})
    elif user.type == 2:
        teacherinfo = models.TeacherInfo.objects.filter(user_id=pk).first()
        return render(request, "teacher_info.html", {"teacherinfo": teacherinfo})


@csrf_exempt
def user_account(request):
    info = request.session.get("info", "")
    username = info['name']
    id = info['id']
    #print(request.POST)
    user = models.User.objects.filter(id=id).first()
    if user.type == 1:
        is_teacher = 0
        userinfo = models.StudentInfo.objects.filter(user_id=id).first()
        profileupdate_form = StudentUpdateForm(instance=userinfo)
    elif user.type == 2:
        is_teacher = 1
        userinfo = models.TeacherInfo.objects.filter(user_id=id).first()
        profileupdate_form = TeacherUpdateForm(instance=userinfo)
    if userinfo.gender == 1:
        gender = "男"
    elif userinfo.gender == 2:
        gender = "女"
    else:
        gender = "保密"
    changepwd_form = UserChangePasswordForm
    content = {
        "username": username,
        "id": id,
        "userinfo": userinfo,
        "gender": gender,
        "changepwd_form": changepwd_form,
        "profileupdate_form": profileupdate_form,
        "is_teacher": is_teacher, 
    }
    ##print(userinfo.teacher_profile_pic.url)
    return render(request, "account.html", content)


@csrf_exempt
def user_change_password(request):
    '''修改密码(Ajax请求)'''
    info = request.session.get("info", "")
    id = info['id']
    form = UserChangePasswordForm(request.POST)
    if form.is_valid():
        pwd = form.cleaned_data.get("password")
        models.User.objects.filter(id=id).update(password=pwd)
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "error": form.errors})


@csrf_exempt
def user_pofile_update(request):
    '''更新个人信息(Ajax请求)'''
    info = request.session.get("info", "")
    id = info['id']
    user = models.User.objects.filter(id=id).first()
    if user.type == 1:
        userinfo = models.StudentInfo.objects.filter(user_id=id).first()
        form = StudentUpdateForm(request.POST, instance=userinfo)
    elif user.type == 2:
        userinfo = models.TeacherInfo.objects.filter(user_id=id).first()
        form = TeacherUpdateForm(request.POST, instance=userinfo)
    if form.is_valid():
        profile = form.save(commit=False)
        profile.user = user
        profile.save()
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "error": form.errors})


@csrf_exempt
def user_pic_update(request):
    '''上传头像'''
    info = request.session.get("info", "")
    id = info['id']
    user = models.User.objects.filter(id=id).first()
    pic_obj = request.FILES.get('profile_pic')
    if user.type == 1:
        userinfo = models.StudentInfo.objects.filter(user_id=id).first()
        form = StudentPicForm(request.POST, instance=userinfo)
    elif user.type == 2:
        userinfo = models.TeacherInfo.objects.filter(user_id=id).first()
        form = TeacherPicForm(request.POST, instance=userinfo)
    if form.is_valid():
        profile = form.save(commit=False)
        if user.type == 1:
            # print("加载图片")
            profile.student_profile_pic = pic_obj
        elif user.type == 2:
            profile.teacher_profile_pic = pic_obj
        profile.save()
        return JsonResponse({"status": True})
    return JsonResponse({"status": False})

@csrf_exempt
def user_des_update(request):
    info = request.session.get("info", "")
    id = info['id']
    des_richtext = request.POST.get('description_richtext')
    models.TeacherInfo.objects.filter(user_id=id).update(description_richtext=des_richtext)
    return JsonResponse({"status": True})
    
def user_announce(request):
    info = request.session.get("info", "")
    username = info['name']
    id = info['id']
    changepwd_form = UserChangePasswordForm
    announceform = AnnounceForm
    user = models.User.objects.filter(id=id).first()
    if user.type == 2:
        is_teacher = 1
        teacher = models.TeacherInfo.objects.filter(user=user).first()
        announce_list = models.Announce.objects.filter(teacher=teacher).all()
    elif user.type == 1:
        student = models.StudentInfo.objects.filter(user=user).first()
        studentcourse_list = models.StudentCourse.objects.filter(student=student).all()
        announce_list = []
        for studentcourse in studentcourse_list:
            announces = models.Announce.objects.filter(course=studentcourse.course).all()
            for announce in announces:
                announce_list.append(announce)
        is_teacher = 0 
    content = { 
        "username": username, 
        "id": id,
        "changepwd_form":changepwd_form,
        "announceform": announceform,
        "is_teacher": is_teacher,
        "announce_list": announce_list,
    }
    return render(request, "announce.html", content)

def user_course(request):
    info = request.session.get("info", "")
    username = info['name']
    id = info['id']
    user = models.User.objects.filter(id=id).first()
    changepwd_form = UserChangePasswordForm
    if user.type == 2:
        is_teacher = 1
        teacher = models.TeacherInfo.objects.filter(user=user).first()
        course_list = models.Course.objects.filter(teacher=teacher).all() 
    else: 
        is_teacher = 0
        course_list = []
        student = models.StudentInfo.objects.filter(user=user).first()
        studentcourse = models.StudentCourse.objects.filter(student=student).all()
        for obj in studentcourse:
            course_list.append(obj.course)
    course_form = CourseForm
    content = { 
        "username": username, 
        "id": id,
        "changepwd_form":changepwd_form,
        "is_teacher": is_teacher,
        "course_list": course_list,
        "course_form": course_form,
        "is_login":True,
    }
    return render(request, "course.html", content)

def user_calendar(request):
    info = request.session.get("info", "")
    username = info['name']
    id = info['id']
    changepwd_form = UserChangePasswordForm
    content = { 
        "username": username, 
        "id": id,
        "changepwd_form":changepwd_form
    }
    return render(request, "calendar.html", content)

def user_help(request):
    info = request.session.get("info", "")
    username = info['name']
    id = info['id']
    changepwd_form = UserChangePasswordForm
    content = { 
        "username": username, 
        "id": id,
        "changepwd_form":changepwd_form
    }
    return render(request, "help.html", content)