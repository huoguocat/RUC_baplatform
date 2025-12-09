from django.shortcuts import render, get_object_or_404
from baweb.models import Course, Post, StudentCourse, User  # 导入模型
from django.db.models import Q
from django.core.paginator import Paginator

def post_list(request, course_id):
    # 获取当前课程
    course = get_object_or_404(Course, id=course_id)
    
    # 获取用户信息（使用正确的session格式）
    info = request.session.get('info', {})
    user_id = info.get('id')
    is_login = bool(user_id)
    
    # 获取当前用户对象
    current_user = None
    is_teacher = False
    if user_id:
        current_user = User.objects.filter(id=user_id).first()
        if current_user:
            is_teacher = (current_user.type == 2)
    
    # 基础查询：获取该课程的所有帖子
    posts_query = Post.objects.filter(course=course).select_related('author', 'category')
    
    # 处理筛选条件
    # 1. 悬赏积分筛选
    has_bounty = request.GET.get('has_bounty')
    if has_bounty == '1':
        posts_query = posts_query.filter(bountyPoints__gt=0)
    
    # 2. 排序逻辑
    sort_by = request.GET.get('sort_by', 'heat')
    if sort_by == 'heat':
        posts_query = posts_query.order_by('-heatScore', '-createdAt')  # 按热度排序
    elif sort_by == 'newest':
        posts_query = posts_query.order_by('-createdAt')  # 按时间排序
    elif sort_by == 'popular':
        posts_query = posts_query.order_by('-viewCount', '-createdAt')  # 按浏览数排序
    elif sort_by == 'bounty':  # 按悬赏积分排序
        posts_query = posts_query.order_by('-bountyPoints', '-createdAt')
    else:
        posts_query = posts_query.order_by('-heatScore', '-createdAt')
    
    # 3. 搜索功能
    keyword = request.GET.get('keyword', '')
    if keyword:
        posts_query = posts_query.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword)
        )
    
    # 分页处理
    paginator = Paginator(posts_query, 10)  # 每页10条
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)
    
    # 计算用户排名（如果有积分系统）
    user_rank = None
    if current_user:
        # 计算排名（积分大于当前用户的用户数 + 1）
        user_rank = User.objects.filter(points__gt=current_user.points).count() + 1
    
    # 传递真实数据到模板
    return render(request, 'forum/course_post.html', {
        'course': course,
        'posts': posts,  # 数据库查询的帖子列表
        'keyword': keyword,
        'sort_by': sort_by,
        'has_bounty': has_bounty,
        'is_login': is_login,
        'is_teacher': is_teacher,
        'user': current_user,  # 传递真实的用户对象，而不是字典
        'current_user': current_user,  # 也传递current_user以便模板使用
        'user_id': user_id,
        'user_rank': user_rank,
    })