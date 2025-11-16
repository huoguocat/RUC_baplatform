"""
论坛系统视图
处理帖子的创建、查看、编辑、删除等操作
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from uuid import uuid4

from baweb import models
from ..forms.postforms import PostCreateForm, PostUpdateForm, PostCommentForm, PostSearchForm


@require_http_methods(["GET"])
def post_list(request, course_id):
    """
    论坛帖子列表页面
    支持按分类、排序等条件筛选
    
    Args:
        course_id: 课程ID，0表示不对应任何课程
    
    Returns:
        renders post_list.html with paginated posts
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    # 获取课程（course_id=0表示不对应任何课程）
    course = None
    if course_id != 0:
        course = models.Course.objects.filter(id=course_id).first()
        if not course:
            return redirect('/')
    
    # 获取搜索和排序条件
    search_form = PostSearchForm(request.GET)
    keyword = request.GET.get('keyword', '')
    category_id = request.GET.get('category', '')
    sort_by = request.GET.get('sort_by', 'heat')
    
    # 构建查询（course_id=0时查询所有不对应课程的帖子）
    if course_id == 0:
        posts_query = models.Post.objects.filter(course__isnull=True)
    else:
        posts_query = models.Post.objects.filter(course=course)
    
    if keyword:
        posts_query = posts_query.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword)
        )
    
    if category_id:
        posts_query = posts_query.filter(category_id=category_id)
    
    # 排序
    if sort_by == 'newest':
        posts_query = posts_query.order_by('-createdAt')
    elif sort_by == 'popular':
        posts_query = posts_query.order_by('-viewCount')
    else:  # 默认按热度排序
        posts_query = posts_query.order_by('-heatScore', '-createdAt')
    
    # 分页
    paginator = Paginator(posts_query, 10)
    page_num = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_num)
    
    context = {
        'course': course,
        'posts': posts_page,
        'search_form': search_form,
        'keyword': keyword,
        'category_id': category_id,
        'sort_by': sort_by,
        'user_id': user_id,
    }
    
    return render(request, 'forum/post_list.html', context)


@require_http_methods(["GET"])
def post_detail(request, post_id):
    """
    帖子详情页面
    显示帖子内容和评论列表
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        renders post_detail.html with post and comments
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    # 获取帖子
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return redirect('/')
    
    # 增加浏览数
    post.viewCount += 1
    post.save(update_fields=['viewCount'])
    
    # 获取评论（分页）
    comments_query = models.PostComment.objects.filter(post=post, parentComment__isnull=True)
    paginator = Paginator(comments_query, 10)
    page_num = request.GET.get('page', 1)
    comments_page = paginator.get_page(page_num)
    
    # 检查当前用户是否点赞或收藏
    has_liked = False
    has_collected = False
    if user_id:
        user = models.User.objects.filter(id=user_id).first()
        has_liked = models.PostLike.objects.filter(post=post, user=user).exists()
        has_collected = models.PostCollect.objects.filter(post=post, user=user).exists()
    
    # 评论表单
    comment_form = PostCommentForm()
    
    context = {
        'post': post,
        'comments': comments_page,
        'comment_form': comment_form,
        'user_id': user_id,
        'has_liked': has_liked,
        'has_collected': has_collected,
    }
    
    return render(request, 'forum/post_detail.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def post_create(request, course_id):
    """
    创建新帖子
    
    Args:
        course_id: 课程ID，0表示不对应任何课程
    
    Returns:
        GET: renders post_create.html with form
        POST: JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return redirect('/login/')
    
    # 验证用户权限（学生或教师可以发帖）
    user = models.User.objects.filter(id=user_id).first()
    if not user or user.type == 3:  # 管理员不能发帖
        return JsonResponse({"status": False, "msg": "没有权限"})
    
    # 获取课程（course_id=0表示不对应任何课程）
    course = None
    if course_id != 0:
        course = models.Course.objects.filter(id=course_id).first()
        if not course:
            return JsonResponse({"status": False, "msg": "课程不存在"})
    
    if request.method == 'POST':
        form = PostCreateForm(data=request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.postId = str(uuid4())
            post.author = user
            post.course = course  # 若course为None，则帖子不对应任何课程
            post.heatScore = 0.0  # 初始热度为0
            post.save()
            
            return JsonResponse({"status": True, "postId": post.postId, "msg": "帖子发布成功"})
        else:
            return JsonResponse({"status": False, "errors": form.errors})
    
    # GET 请求
    form = PostCreateForm()
    context = {
        'form': form,
        'course': course,
    }
    
    return render(request, 'forum/post_create.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def post_update(request, post_id):
    """
    更新帖子
    只允许帖子作者修改
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return JsonResponse({"status": False, "msg": "帖子不存在"})
    
    # 验证权限（只能修改自己的帖子）
    if post.author.id != user_id:
        return JsonResponse({"status": False, "msg": "没有权限修改"})
    
    form = PostUpdateForm(data=request.POST, instance=post)
    if form.is_valid():
        form.save()
        return JsonResponse({"status": True, "msg": "帖子已更新"})
    else:
        return JsonResponse({"status": False, "errors": form.errors})


@csrf_exempt
@require_http_methods(["POST"])
def post_delete(request, post_id):
    """
    删除帖子
    只允许帖子作者或管理员删除
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return JsonResponse({"status": False, "msg": "帖子不存在"})
    
    # 验证权限
    user = models.User.objects.filter(id=user_id).first()
    if post.author.id != user_id and user.type != 3:  # 作者或管理员
        return JsonResponse({"status": False, "msg": "没有权限删除"})
    
    post.delete()
    return JsonResponse({"status": True, "msg": "帖子已删除"})


@csrf_exempt
@require_http_methods(["POST"])
def post_like(request, post_id):
    """
    点赞帖子（支持取消点赞）
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        JsonResponse with status and like_count
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return JsonResponse({"status": False, "msg": "帖子不存在"})
    
    user = models.User.objects.filter(id=user_id).first()
    
    # 检查是否已点赞
    like = models.PostLike.objects.filter(post=post, user=user).first()
    
    if like:
        # 取消点赞
        like.delete()
        post.likeCount = max(0, post.likeCount - 1)
        action = 'unlike'
    else:
        # 点赞
        models.PostLike.objects.create(post=post, user=user)
        post.likeCount += 1
        action = 'like'
    
    # 更新热度
    post.heatScore = post.calculateHeat()
    post.save()
    
    return JsonResponse({
        "status": True,
        "action": action,
        "like_count": post.likeCount,
        "heat_score": post.heatScore,
    })


@csrf_exempt
@require_http_methods(["POST"])
def post_collect(request, post_id):
    """
    收藏帖子（支持取消收藏）
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        JsonResponse with status and collect_count
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return JsonResponse({"status": False, "msg": "帖子不存在"})
    
    user = models.User.objects.filter(id=user_id).first()
    
    # 检查是否已收藏
    collect = models.PostCollect.objects.filter(post=post, user=user).first()
    
    if collect:
        # 取消收藏
        collect.delete()
        post.collectCount = max(0, post.collectCount - 1)
        action = 'uncollect'
    else:
        # 收藏
        models.PostCollect.objects.create(post=post, user=user)
        post.collectCount += 1
        action = 'collect'
    
    # 更新热度
    post.heatScore = post.calculateHeat()
    post.save()
    
    return JsonResponse({
        "status": True,
        "action": action,
        "collect_count": post.collectCount,
        "heat_score": post.heatScore,
    })


@csrf_exempt
@require_http_methods(["POST"])
def comment_add(request, post_id):
    """
    添加评论到帖子
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return JsonResponse({"status": False, "msg": "帖子不存在"})
    
    user = models.User.objects.filter(id=user_id).first()
    
    form = PostCommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.commentId = str(uuid4())
        comment.post = post
        comment.author = user
        comment.save()
        
        # 更新评论数和热度
        post.commentCount += 1
        post.heatScore = post.calculateHeat()
        post.save()
        
        return JsonResponse({
            "status": True,
            "msg": "评论已发布",
            "comment_count": post.commentCount,
            "heat_score": post.heatScore,
        })
    else:
        return JsonResponse({"status": False, "errors": form.errors})


@csrf_exempt
@require_http_methods(["POST"])
def comment_delete(request, comment_id):
    """
    删除评论
    只允许评论作者或管理员删除
    
    Args:
        comment_id: 评论ID (commentId)
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    comment = models.PostComment.objects.filter(commentId=comment_id).first()
    if not comment:
        return JsonResponse({"status": False, "msg": "评论不存在"})
    
    # 验证权限
    user = models.User.objects.filter(id=user_id).first()
    if comment.author.id != user_id and user.type != 3:
        return JsonResponse({"status": False, "msg": "没有权限删除"})
    
    post = comment.post
    post.commentCount = max(0, post.commentCount - 1)
    
    comment.delete()
    
    # 更新热度
    post.heatScore = post.calculateHeat()
    post.save()
    
    return JsonResponse({
        "status": True,
        "msg": "评论已删除",
        "comment_count": post.commentCount,
    })


@csrf_exempt
@require_http_methods(["POST"])
def comment_like(request, comment_id):
    """
    点赞评论
    
    Args:
        comment_id: 评论ID (commentId)
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    comment = models.PostComment.objects.filter(commentId=comment_id).first()
    if not comment:
        return JsonResponse({"status": False, "msg": "评论不存在"})
    
    comment.like()
    
    return JsonResponse({
        "status": True,
        "msg": "评论已点赞",
        "like_count": comment.likeCount,
    })
