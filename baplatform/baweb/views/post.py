from django.shortcuts import render, get_object_or_404
from baweb.models import Course, Post  # 导入模型
from django.db.models import Q

def post_list(request, course_id):
    # 获取当前课程
    course = get_object_or_404(Course, id=course_id)
    
    # 基础查询：获取该课程的所有帖子
    posts_query = Post.objects.filter(course=course).select_related('author', 'category')
    
    # 处理筛选条件
    # 1. 悬赏筛选（注意：Post模型中暂未直接存储悬赏金额，后续可扩展字段）
    has_bounty = request.GET.get('has_bounty')
    if has_bounty:
        # 假设后续添加了bounty字段，这里可以筛选有悬赏的帖子
        # posts_query = posts_query.filter(bounty__gt=0)
        pass  # 目前暂不实现，预留逻辑
    
    # 2. 排序逻辑
    sort_by = request.GET.get('sort_by', 'newest')
    if sort_by == 'heat':
        posts_query = posts_query.order_by('-heatScore')  # 按热度排序（模型已有字段）
    else:
        posts_query = posts_query.order_by('-createdAt')  # 按时间排序（默认）
    
    # 3. 搜索功能
    keyword = request.GET.get('keyword', '')
    if keyword:
        posts_query = posts_query.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword)
        )
    
    # 分页处理（保留原分页逻辑，替换数据源）
    from django.core.paginator import Paginator
    paginator = Paginator(posts_query, 10)  # 每页10条
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)
    
    # 传递真实数据到模板
    return render(request, 'forum/course_post.html', {
        'course': course,
        'posts': posts,  # 数据库查询的帖子列表
        'keyword': keyword,
        'sort_by': sort_by,
        'user': request.user,  # 当前登录用户
        # 个人信息相关（从用户表查询）
        'user_rank': 10,  # 后续可从积分系统查询真实排行
        # 'user_rank': get_user_rank(request.user)  # 示例：调用排行查询函数
    })