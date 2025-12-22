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
from django.conf import settings
from uuid import uuid4

from baweb import models
from ..forms.postforms import PostCreateForm, PostUpdateForm, PostCommentForm, PostSearchForm

# 导入新的Activity服务
from ..utils.search_engine import SearchEngine
from ..utils.content_retrieval import ContentRetrieval
from ..utils.ranking_service import RankingService
from ..utils.recommendation_service import RecommendationService
from ..utils.interaction_tracker import InteractionTracker


def forum_index(request):
    """
    论坛首页 - 汇总所有课程的帖子,包括不属于课程的帖子
    
    Returns:
        renders forum/forum_index.html with all posts
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    # 获取当前用户对象（如果已登录）
    current_user = None
    if user_id:
        try:
            current_user = models.User.objects.get(id=user_id)
        except models.User.DoesNotExist:
            pass
    
    # 基础查询:获取所有帖子
    posts_query = models.Post.objects.all().select_related('author', 'category', 'course')
    
    # 处理筛选条件
    # 1. 课程筛选
    course_id = request.GET.get('course_id')
    if course_id:
        if course_id == 'none':  # 无课程帖子
            posts_query = posts_query.filter(course__isnull=True)
        else:
            try:
                posts_query = posts_query.filter(course_id=int(course_id))
            except (ValueError, TypeError):
                pass
    
    # 2. 分类筛选
    category_id = request.GET.get('category_id')
    if category_id:
        try:
            posts_query = posts_query.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass
    
    # 3. 悬赏积分筛选
    has_bounty = request.GET.get('has_bounty')
    if has_bounty == '1':
        posts_query = posts_query.filter(bountyPoints__gt=0)
    
    # 4. 搜索功能 - 使用Activity 1 & 2服务
    keyword = request.GET.get('keyword', '')
    sort_by = request.GET.get('sort_by', 'heat')
    
    if keyword:
        # 使用新的搜索引擎服务
        try:
            search_query = SearchEngine.create_search_query(
                query_text=keyword,
                category_id=int(category_id) if category_id else None,
                tags=None,
                sort_by=sort_by,
                course_id=int(course_id) if course_id and course_id != 'none' else (-1 if course_id == 'none' else None)
            )
            
            # 使用内容检索服务
            posts_list = ContentRetrieval.retrieve(search_query, top_k=100)
            
            # 应用悬赏积分过滤
            if has_bounty == '1':
                posts_list = [p for p in posts_list if p.bountyPoints > 0]
            
            # 使用排名服务进行个性化排名
            posts_list = RankingService.rank_posts(
                posts=posts_list,
                user=current_user,
                sort_by=sort_by,
                enable_personalization=True if current_user else False,
                respect_pinned=False  # 论坛首页不考虑置顶
            )
            
            # 手动分页
            paginator = Paginator(posts_list, 20)
            page_num = request.GET.get('page', 1)
            posts_page = paginator.get_page(page_num)
        except Exception as e:
            # 降级到传统搜索
            posts_query = posts_query.filter(
                Q(title__icontains=keyword) | Q(content__icontains=keyword)
            )
            # 论坛首页不按isPinned排序（课程置顶只在课程页面生效）
            if sort_by == 'newest':
                posts_query = posts_query.order_by('-createdAt')
            elif sort_by == 'bounty':
                posts_query = posts_query.order_by('-bountyPoints', '-createdAt')
            else:
                posts_query = posts_query.order_by('-heatScore', '-createdAt')
            
            paginator = Paginator(posts_query, 20)
            page_num = request.GET.get('page', 1)
            posts_page = paginator.get_page(page_num)
    else:
        # 5. 无搜索关键词时的排序逻辑 - 使用Activity 3服务
        posts_list = list(posts_query)
        
        # 使用排名服务进行个性化排名
        try:
            posts_list = RankingService.rank_posts(
                posts=posts_list,
                user=current_user,
                sort_by=sort_by,
                enable_personalization=True if current_user else False,
                respect_pinned=False  # 论坛首页不考虑置顶
            )
        except:
            # 降级到传统排序
            # 论坛首页不按isPinned排序（课程置顶只在课程页面生效）
            if sort_by == 'newest':
                posts_query = posts_query.order_by('-createdAt')
            elif sort_by == 'bounty':
                posts_query = posts_query.order_by('-bountyPoints', '-createdAt')
            else:
                posts_query = posts_query.order_by('-heatScore', '-createdAt')
            posts_list = list(posts_query)
        
        # 分页处理
        paginator = Paginator(posts_list, 20)
        page_num = request.GET.get('page', 1)
        posts_page = paginator.get_page(page_num)
    
    # 获取所有课程用于筛选
    courses = models.Course.objects.all().order_by('order')
    
    # 获取所有分类
    categories = models.ContentCategory.objects.all()
    
    # 获取统计数据
    total_posts = models.Post.objects.count()
    total_comments = models.PostComment.objects.count()
    
    # 获取当前用户信息（包括积分）
    current_user = None
    if user_id:
        current_user = models.User.objects.filter(id=user_id).first()
    
    # 处理标签
    for post in posts_page:
        if post.tags:
            post.tags_list = [tag.strip() for tag in post.tags.split(',') if tag.strip()]
        else:
            post.tags_list = []
    
    context = {
        'posts': posts_page,
        'courses': courses,
        'categories': categories,
        'keyword': keyword,
        'sort_by': sort_by,
        'selected_course_id': course_id,
        'selected_category_id': category_id,
        'has_bounty': has_bounty,
        'user_id': user_id,
        'current_user': current_user,
        'total_posts': total_posts,
        'total_comments': total_comments,
    }
    
    return render(request, 'forum/forum_index.html', context)


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
    
    # 悬赏积分筛选
    has_bounty = request.GET.get('has_bounty')
    if has_bounty == '1':
        posts_query = posts_query.filter(bountyPoints__gt=0)
    
    # 排序（置顶帖子始终在最前面）
    if sort_by == 'newest':
        posts_query = posts_query.order_by('-isPinned', '-createdAt')
    elif sort_by == 'popular':
        posts_query = posts_query.order_by('-isPinned', '-viewCount')
    elif sort_by == 'bounty':  # 按悬赏积分排序
        posts_query = posts_query.order_by('-isPinned', '-bountyPoints', '-createdAt')
    else:  # 默认按热度排序
        posts_query = posts_query.order_by('-isPinned', '-heatScore', '-createdAt')
    
    # 分页
    paginator = Paginator(posts_query, 10)
    page_num = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_num)
    
    # 获取当前用户信息（包括积分）
    current_user = None
    if user_id:
        current_user = models.User.objects.filter(id=user_id).first()
    
    context = {
        'course': course,
        'posts': posts_page,
        'search_form': search_form,
        'keyword': keyword,
        'category_id': category_id,
        'sort_by': sort_by,
        'has_bounty': has_bounty,
        'user_id': user_id,
        'current_user': current_user,
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
    
    # 获取当前用户信息（需要提前获取，用于浏览跟踪）
    current_user = None
    if user_id:
        current_user = models.User.objects.filter(id=user_id).first()
    
    # 获取帖子
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return redirect('/')
    
    # 使用Activity 5服务记录浏览行为
    if user_id and current_user:
        try:
            InteractionTracker.track_view(current_user, post)
        except:
            # 降级到传统方式
            post.viewCount += 1
            post.save(update_fields=['viewCount'])
    else:
        # 未登录用户仍然增加浏览数
        post.viewCount += 1
        post.save(update_fields=['viewCount'])
    
    # 获取评论（分页，只获取顶级评论）
    comments_query = models.PostComment.objects.filter(post=post, parentComment__isnull=True).prefetch_related('replies', 'replies__author')
    paginator = Paginator(comments_query, 10)
    page_num = request.GET.get('page', 1)
    comments_page = paginator.get_page(page_num)
    
    # 检查当前用户是否点赞或收藏
    has_liked = False
    has_collected = False
    if current_user:
        has_liked = models.PostLike.objects.filter(post=post, user=current_user).exists()
        has_collected = models.PostCollect.objects.filter(post=post, user=current_user).exists()
    
    # 评论表单
    comment_form = PostCommentForm()
    
    # 处理标签
    tags_list = []
    if post.tags:
        tags_list = [tag.strip() for tag in post.tags.split(',') if tag.strip()]
    
    # 检查是否可以设置最佳答案（只有帖子作者且帖子有悬赏积分且未选择最佳答案）
    can_select_best_answer = False
    if current_user and post.author == current_user and post.bountyPoints > 0 and not post.bestAnswer:
        can_select_best_answer = True
    
    # 检查当前用户是否是该课程的教师
    is_teacher = False
    if current_user and current_user.type == 2 and post.course:
        try:
            teacher_info = models.TeacherInfo.objects.get(user=current_user)
            if post.course.teacher == teacher_info:
                is_teacher = True
        except models.TeacherInfo.DoesNotExist:
            pass
    
    # 使用Activity 4服务生成推荐内容
    recommended_posts = []
    trending_tags = []
    try:
        recommended_posts = RecommendationService.recommend_for_post_view(
            post=post,
            user=current_user,
            limit=5
        )
        trending_tags = RecommendationService.get_trending_tags(time_window_days=7, limit=10)
    except:
        pass
    
    context = {
        'post': post,
        'comments': comments_page,
        'comment_form': comment_form,
        'user_id': user_id,
        'current_user': current_user,
        'has_liked': has_liked,
        'has_collected': has_collected,
        'tags_list': tags_list,
        'can_select_best_answer': can_select_best_answer,
        'is_teacher': is_teacher,
        'recommended_posts': recommended_posts,
        'trending_tags': trending_tags,
    }
    
    return render(request, 'forum/post_detail.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def post_create(request, course_id=None):
    """
    创建新帖子
    
    Args:
        course_id: 课程ID，None表示不对应任何课程
    
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
    
    # 获取课程（course_id=None表示不对应任何课程）
    course = None
    if course_id:
        course = models.Course.objects.filter(id=course_id).first()
        if not course:
            if request.method == 'POST':
                return JsonResponse({"status": False, "msg": "课程不存在"})
            else:
                return redirect('/forum/')
    
    if request.method == 'POST':
        form = PostCreateForm(data=request.POST)
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.postId = str(uuid4())
                post.author = user
                post.course = course  # 若course为None，则帖子不对应任何课程
                post.heatScore = 0.0  # 初始热度为0
                
                # 处理分类字段（如果提交了分类）
                category_value = form.cleaned_data.get('category')
                if category_value:
                    # 获取或创建对应的ContentCategory对象
                    category_obj, _ = models.ContentCategory.objects.get_or_create(
                        name=int(category_value)
                    )
                    post.category = category_obj
                
                # 处理悬赏积分
                bounty_points = form.cleaned_data.get('bountyPoints', 0) or 0
                if bounty_points > 0:
                    # 重新从数据库获取用户对象，确保积分是最新的
                    user.refresh_from_db()
                    
                    # 检查用户积分是否足够
                    if user.points < bounty_points:
                        return JsonResponse({"status": False, "msg": f"积分不足，您当前有 {user.points} 积分"})
                    
                    # 直接扣除用户积分（避免在setBounty中重复扣除）
                    user.points -= bounty_points
                    user.save(update_fields=['points'])
                    
                    # 设置帖子悬赏积分（不在这里扣除积分，因为已经扣除了）
                    post.bountyPoints = bounty_points
                
                post.save()
                
                # 重新获取用户对象，确保积分是最新的
                user.refresh_from_db()
                
                return JsonResponse({
                    "status": True, 
                    "postId": post.postId, 
                    "msg": "帖子发布成功",
                    "bounty_points": post.bountyPoints,
                    "user_points": user.points
                })
            except Exception as e:
                # 捕获所有异常，返回友好的错误信息
                import traceback
                error_detail = str(e)
                # 打印详细错误信息到控制台（用于调试）
                if settings.DEBUG:
                    import sys
                    traceback.print_exc(file=sys.stderr)
                return JsonResponse({"status": False, "msg": f"发布失败：{error_detail}"})
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
    
    # 使用Activity 5服务记录点赞行为
    try:
        result = InteractionTracker.track_like(user, post)
        return JsonResponse({
            "status": result['success'],
            "action": 'like' if result['is_liked'] else 'unlike',
            "like_count": post.likeCount,
            "heat_score": post.heatScore,
            "msg": result['message']
        })
    except Exception as e:
        # 降级到传统方式
        like = models.PostLike.objects.filter(post=post, user=user).first()
        
        if like:
            like.delete()
            post.likeCount = max(0, post.likeCount - 1)
            action = 'unlike'
        else:
            models.PostLike.objects.create(post=post, user=user)
            post.likeCount += 1
            action = 'like'
        
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
    
    # 使用Activity 5服务记录收藏行为
    try:
        result = InteractionTracker.track_collect(user, post)
        return JsonResponse({
            "status": result['success'],
            "action": 'collect' if result['is_collected'] else 'uncollect',
            "collect_count": post.collectCount,
            "heat_score": post.heatScore,
            "msg": result['message']
        })
    except Exception as e:
        # 降级到传统方式
        collect = models.PostCollect.objects.filter(post=post, user=user).first()
        
        if collect:
            collect.delete()
            post.collectCount = max(0, post.collectCount - 1)
            action = 'uncollect'
        else:
            models.PostCollect.objects.create(post=post, user=user)
            post.collectCount += 1
            action = 'collect'
        
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
    添加评论到帖子（支持回复评论）
    
    Args:
        post_id: 帖子ID (postId)
    
    POST参数:
        content: 评论内容
        isAnonymous: 是否匿名
        parent_comment_id: 父评论ID（可选，用于回复评论）
    
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
    
    # 检查是否是回复评论
    parent_comment_id = request.POST.get('parent_comment_id')
    parent_comment = None
    if parent_comment_id:
        parent_comment = models.PostComment.objects.filter(commentId=parent_comment_id).first()
        if not parent_comment or parent_comment.post != post:
            return JsonResponse({"status": False, "msg": "父评论不存在或不属于该帖子"})
    
    form = PostCommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.commentId = str(uuid4())
        comment.post = post
        comment.author = user
        comment.parentComment = parent_comment  # 设置父评论
        comment.save()
        
        # 使用Activity 5服务记录评论行为（只有顶级评论才记录）
        if not parent_comment:
            try:
                InteractionTracker.track_comment(user, post, comment)
            except:
                # 降级到传统方式
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
def comment_reply(request, comment_id):
    """
    回复评论
    
    Args:
        comment_id: 父评论ID (commentId)
    
    POST参数:
        content: 回复内容
        isAnonymous: 是否匿名
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    parent_comment = models.PostComment.objects.filter(commentId=comment_id).first()
    if not parent_comment:
        return JsonResponse({"status": False, "msg": "评论不存在"})
    
    user = models.User.objects.filter(id=user_id).first()
    post = parent_comment.post
    
    form = PostCommentForm(data=request.POST)
    if form.is_valid():
        # 使用模型的reply方法创建回复
        reply = parent_comment.reply(
            reply_content=form.cleaned_data['content'],
            reply_author=user,
            is_anonymous=form.cleaned_data.get('isAnonymous', False)
        )
        
        # 更新热度（回复不增加评论数，因为评论数只统计顶级评论）
        post.heatScore = post.calculateHeat()
        post.save()
        
        return JsonResponse({
            "status": True,
            "msg": "回复已发布",
            "heat_score": post.heatScore,
        })
    else:
        return JsonResponse({"status": False, "errors": form.errors})


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


def my_posts(request):
    """
    我的帖子页面
    显示当前用户发布的所有帖子
    
    Returns:
        renders forum/my_posts.html with user's posts
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return redirect('/login/')
    
    user = models.User.objects.filter(id=user_id).first()
    if not user:
        return redirect('/login/')
    
    # 获取用户发布的帖子
    posts_query = models.Post.objects.filter(author=user).select_related('course', 'category')
    
    # 排序
    sort_by = request.GET.get('sort_by', 'newest')
    if sort_by == 'hot':
        posts_query = posts_query.order_by('-heatScore', '-createdAt')
    else:
        posts_query = posts_query.order_by('-createdAt')
    
    # 搜索
    keyword = request.GET.get('keyword', '')
    if keyword:
        from django.db.models import Q
        posts_query = posts_query.filter(
            Q(title__icontains=keyword) | Q(content__icontains=keyword)
        )
    
    # 分页
    paginator = Paginator(posts_query, 15)
    page_num = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_num)
    
    # 处理标签
    for post in posts_page:
        if post.tags:
            post.tags_list = [tag.strip() for tag in post.tags.split(',') if tag.strip()]
        else:
            post.tags_list = []
    
    # 统计数据
    total_posts = models.Post.objects.filter(author=user).count()
    total_likes = sum(models.Post.objects.filter(author=user).values_list('likeCount', flat=True))
    total_comments = sum(models.Post.objects.filter(author=user).values_list('commentCount', flat=True))
    
    context = {
        'posts': posts_page,
        'user': user,
        'keyword': keyword,
        'sort_by': sort_by,
        'total_posts': total_posts,
        'total_likes': total_likes,
        'total_comments': total_comments,
    }
    
    return render(request, 'forum/my_posts.html', context)


def my_collected(request):
    """
    我的收藏页面
    显示当前用户收藏的所有帖子
    
    Returns:
        renders forum/my_collected.html with user's collected posts
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return redirect('/login/')
    
    user = models.User.objects.filter(id=user_id).first()
    if not user:
        return redirect('/login/')
    
    # 获取用户收藏的帖子
    collects_query = models.PostCollect.objects.filter(user=user).select_related('post', 'post__author', 'post__course', 'post__category').order_by('-createdAt')
    
    # 搜索
    keyword = request.GET.get('keyword', '')
    if keyword:
        from django.db.models import Q
        collects_query = collects_query.filter(
            Q(post__title__icontains=keyword) | Q(post__content__icontains=keyword)
        )
    
    # 分页
    paginator = Paginator(collects_query, 15)
    page_num = request.GET.get('page', 1)
    collects_page = paginator.get_page(page_num)
    
    # 处理标签
    for collect in collects_page:
        if collect.post.tags:
            collect.post.tags_list = [tag.strip() for tag in collect.post.tags.split(',') if tag.strip()]
        else:
            collect.post.tags_list = []
    
    # 统计数据
    total_collected = models.PostCollect.objects.filter(user=user).count()
    
    context = {
        'collects': collects_page,
        'user': user,
        'keyword': keyword,
        'total_collected': total_collected,
    }
    
    return render(request, 'forum/my_collected.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def post_select_best_answer(request, post_id, comment_id):
    """
    选择最佳答案并分配积分
    
    Args:
        post_id: 帖子ID (postId)
        comment_id: 评论ID (commentId)
    
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
    
    comment = models.PostComment.objects.filter(commentId=comment_id).first()
    if not comment:
        return JsonResponse({"status": False, "msg": "评论不存在"})
    
    user = models.User.objects.filter(id=user_id).first()
    
    # 选择最佳答案
    if post.selectBestAnswer(comment, user):
        return JsonResponse({
            "status": True,
            "msg": "已选择最佳答案，积分已分配给回答者",
            "bounty_points": post.bountyPoints,
        })
    else:
        return JsonResponse({"status": False, "msg": "选择最佳答案失败，请检查权限和积分"})


def points_ranking(request):
    """
    积分排行榜页面
    
    Returns:
        renders forum/points_ranking.html with user ranking
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    # 获取所有用户，按积分降序排列
    users = models.User.objects.all().order_by('-points')[:100]  # 前100名
    
    # 获取当前用户排名
    current_user_rank = None
    if user_id:
        current_user = models.User.objects.filter(id=user_id).first()
        if current_user:
            # 计算排名（积分大于当前用户的用户数 + 1）
            rank = models.User.objects.filter(points__gt=current_user.points).count() + 1
            current_user_rank = {
                'user': current_user,
                'rank': rank,
            }
    
    context = {
        'users': users,
        'current_user_rank': current_user_rank,
        'user_id': user_id,
    }
    
    return render(request, 'forum/points_ranking.html', context)


@require_http_methods(["POST"])
def post_pin_toggle(request, post_id):
    """
    教师置顶/取消置顶帖子
    只有帖子所属课程的教师才能置顶该帖子
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    # 获取帖子
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return JsonResponse({"status": False, "msg": "帖子不存在"})
    
    # 检查帖子是否属于某个课程
    if not post.course:
        return JsonResponse({"status": False, "msg": "只有课程内的帖子才能被置顶"})
    
    # 获取当前用户
    user = models.User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({"status": False, "msg": "用户不存在"})
    
    # 检查用户是否是教师
    if user.type != 2:
        return JsonResponse({"status": False, "msg": "只有教师才能置顶帖子"})
    
    # 检查教师是否是该课程的授课老师
    try:
        teacher_info = models.TeacherInfo.objects.get(user=user)
        if post.course.teacher != teacher_info:
            return JsonResponse({"status": False, "msg": "只有该课程的授课教师才能置顶帖子"})
    except models.TeacherInfo.DoesNotExist:
        return JsonResponse({"status": False, "msg": "教师信息不存在"})
    
    # 切换置顶状态
    if post.isPinned:
        post.isPinned = False
        post.pinnedAt = None
        post.save()
        return JsonResponse({"status": True, "msg": "已取消置顶", "isPinned": False})
    else:
        post.isPinned = True
        post.pinnedAt = timezone.now()
        post.save()
        return JsonResponse({"status": True, "msg": "已置顶", "isPinned": True})


@require_http_methods(["POST"])
def teacher_delete_post(request, post_id):
    """
    教师删除课程内的帖子
    只有帖子所属课程的教师才能删除该帖子
    
    Args:
        post_id: 帖子ID (postId)
    
    Returns:
        JsonResponse with status
    """
    info = request.session.get('info', {})
    user_id = info.get('id')
    
    if not user_id:
        return JsonResponse({"status": False, "msg": "未登录"})
    
    # 获取帖子
    post = models.Post.objects.filter(postId=post_id).first()
    if not post:
        return JsonResponse({"status": False, "msg": "帖子不存在"})
    
    # 检查帖子是否属于某个课程
    if not post.course:
        return JsonResponse({"status": False, "msg": "只有课程内的帖子才能被教师删除"})
    
    # 获取当前用户
    user = models.User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({"status": False, "msg": "用户不存在"})
    
    # 检查用户是否是教师
    if user.type != 2:
        return JsonResponse({"status": False, "msg": "只有教师才能删除课程内的帖子"})
    
    # 检查教师是否是该课程的授课老师
    try:
        teacher_info = models.TeacherInfo.objects.get(user=user)
        if post.course.teacher != teacher_info:
            return JsonResponse({"status": False, "msg": "只有该课程的授课教师才能删除帖子"})
    except models.TeacherInfo.DoesNotExist:
        return JsonResponse({"status": False, "msg": "教师信息不存在"})
    
    # 删除帖子
    post_title = post.title
    post.delete()
    
    return JsonResponse({"status": True, "msg": f"已删除帖子「{post_title}」"})
