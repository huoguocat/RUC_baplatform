"""baplatform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path,include
from baweb.views import home,admin, user, student, course, teacher, file, assignment, assignmentfile, comment, group, announce
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #path('superadmin/', superadmin.site.urls),
    ##用户通用功能
    
    path('', user.user_home),
    path('signup/', user.user_signup),
    path('login/', user.user_login), 
    path('logout/', user.user_logout),
    ##管理员功能
    path('admin/', user.user_admin), 
    path('teacher/import', admin.teacher_import),
    path('teacher/add', admin.teacher_add),
    path('teacher/<int:id>/is_disabled', admin.is_disabled),
    path('teacher/<int:id>/disabled', admin.teacher_disabled),
    path('teacher/<int:id>/abled', admin.teacher_abled),
    path('teacher/<int:id>/order/<int:order>/update', admin.update_torder),
    path('course/<int:id>/order/<int:order>/update', admin.update_corder),
    ##首页导航的功能
    path('home/', user.user_home),
    ####辅助home页面加载
    path('home/load/', home.home_load),
    path('account/', user.user_account),
    path('announce/', user.user_announce),
    path('course/', user.user_course),
    path('calendar/', user.user_calendar),
    path('help/', user.user_help),
    #####calendar 根据任务ddl添加到日历上
    path('remind/', assignment.remind),
    ##修改密码
    path('password/change', user.user_change_password),  
    ##个人账号的功能：个人信息的修改+头像的上传
    path('profile/update', user.user_pofile_update),
    path("profile_pic/update", user.user_pic_update),
    path("description_richtext/update", user.user_des_update),
    path('user/<int:pk>/info', user.user_info),
    ##图片验证码
    path('image/code/', user.image_code),
    #学生功能
    path('student/<int:pk>/student_page/', student.student_page),
    path('student/<int:pk>/info/', student.student_info),
    path('student/<int:pk>/edit/', student.student_edit),
    #老师功能
    path('teacher/<int:pk>/teacher_page/', teacher.teacher_page),
    path('teacher/<int:pk>/info/', teacher.teacher_info),
    path('teacher/<int:pk>/edit', teacher.teacher_edit),
    ##课程内容
    path('course/list', course.course_list),
    path('course/add', course.course_add),
    path('course/<int:id>/course_page', course.course_page),
    path('course/<int:id>/delete', course.course_delete),
    path('course/<int:id>/description_richtext/update', course.des_update),
    path('course/<int:id>/student/import', course.student_import),
    path('course/<int:id>/student/add', course.student_add),
    path('course/<int:id>/student/list', course.student_list), 
    path('course/<int:id>/student/<int:sid>/delete', course.student_delete),
    ##课件的增删改
    path('course/<int:id>/file/list', file.file_list),
    path('course/<int:id>/file/add', file.file_add),
    path('course/<int:id>/file/add_batch', file.file_add_batch),
    path('course/<int:id>/file/<int:fid>/update', file.file_update),
    path('course/<int:id>/file/<int:fid>/delete', file.file_delete), 
    ##任务的增删改
    path('course/<int:id>/assignment/list', assignment.assignment_list),
    path('course/<int:id>/assignment/add', assignment.assignment_add),
    path('course/<int:id>/assignment/<int:aid>/update', assignment.assignment_update),
    path('course/<int:id>/assignment/<int:aid>/delete', assignment.assignment_delete), 
    path('course/<int:id>/comment/list', course.comment), 
    path('assignment/<int:id>/page', assignment.assignment_page), 
    path('assignment/<int:id>/description_richtext/update', assignment.assignment_des_update), 
    ##任务文档的增删改
    path('assignment/<int:id>/file/list', assignmentfile.file_list),
    path('assignment/<int:id>/file/add', assignmentfile.file_add),
    path('assignment/<int:id>/file/<int:fid>/update', assignmentfile.file_update),
    path('assignment/<int:id>/file/<int:fid>/delete', assignmentfile.file_delete), 
    ##任务评价 
    path('assignment/<int:id>/mycomment/list',comment.mycomment_list), 
    path('course/<int:id>/comment/add',comment.comment_add), 
    path('course/<int:id>/comment/<int:cid>/delete',comment.comment_delete),
    path('course/<int:id>/comment/<int:cid>/edit',comment.comment_edit), 
    ##查看作业提交情况
    path('assignment/<int:id>/submit/info', assignmentfile.submit_info), 
    #path('assignment/<int:id>/submit/list',assignmentfile.s), 
    path('assignment/<int:id>/unsubmit/list',assignmentfile.unsubmit_list), 
    path('assignment/<int:id>/student/<int:sid>/file/list',assignmentfile.submitfile_list),
    ## 老师打分 
    path('assignment/<int:id>/student/<int:sid>/entermarks',assignmentfile.marks_enter), 
    path('assignment/<int:id>/student/<int:uid>/marks/get', assignmentfile.marks_get),
    path('assignment/<int:id>/student/<int:uid>/files/get', assignmentfile.files_get),
    ##查看成绩
    #path('course/<int:id>/marks/list',course.marks_list), 
    ##小组
    path('course/<int:id>/group/list',group.group_list), 
    path('course/<int:id>/group/add',group.group_add), 
    path('course/<int:id>/group/<int:gid>/delete', group.group_delete),
    path('group/<int:id>/member/list', group.member_list), 
    path('group/<int:id>/member/add', group.member_add),
    path('group/<int:id>/member/<int:sid>/delete', group.member_delete),
    ##通知
    path('announce/add', announce.announce_add),
    path('announce/<int:id>/edit', announce.announce_edit),
    path('announce/<int:id>/delete', announce.announce_delete),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    ##老师课程展示
    path("teacher/<int:id>/course/list", course.teacher_courses),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
