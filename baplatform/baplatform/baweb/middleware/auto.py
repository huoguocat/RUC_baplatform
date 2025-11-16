from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
import re

class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        urls = ["/", "/signup/", "/login/", "/image/code/", "/home/load/", "/logout/"]
        if re.match(r'/teacher/[0-9]*/course/list' ,request.path_info):
            return
        if re.match(r'/media/userimg/*', request.path_info):
            return
        if re.match(r'/course/[0-9]*/course_page', request.path_info):
            return
        for url in urls:
            if request.path_info == url:
                return 
        #1. 读取当前访问的用户的session信息， 如果能够读取，说明已登录， 继续往后走
        info_dict = request.session.get('info')
        if info_dict:
            return
        return redirect('/login/')


