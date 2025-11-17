from django.shortcuts import render
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from baweb import models
# 在 post.py 顶部添加
from ..models import Course  # 相对导入：从当前目录的上一级（baweb）的 models 中导入 Course
def course_forum(request, course_id):
    # 这里模拟数据，实际项目中需要从数据库查询
    course = Course.objects.get(id=course_id)  # 获取课程信息
    posts = [  # 模拟帖子列表数据
        {
            'postId': 1,
            'title': '测试帖子1',
            'bounty': 10,
            'createdAt': '2025-11-17 10:00',
            'commentCount': 5,
            'likeCount': 3
        },
        {
            'postId': 2,
            'title': '测试帖子2',
            'bounty': 0,
            'createdAt': '2025-11-17 11:00',
            'commentCount': 2,
            'likeCount': 1
        }
    ]
    user = request.user  # 获取当前登录用户（Django内置）
    user_rank = 10  # 模拟排行数据
    # 传递变量给模板
    return render(request, 'forum/course_post.html', {
        'course': course,
        'posts': posts,
        'user': user,
        'user_rank': user_rank,
        'keyword': ''  # 搜索关键词，初始为空
    })