# Post 论坛系统集成说明

## 📋 概述
已为 BAplatform 添加了完整的论坛系统，包括帖子发布、评论、点赞、收藏等功能。

## 🔧 已添加的文件

### 1. 数据模型 (`baweb/models.py`)
添加了以下模型类：

- **ContentCategory**: 内容分类（问答、知识分享、资源分享）
- **Post**: 主贴模型，包含热度计算、新鲜度计算等方法
- **PostLike**: 点赞记录表（防重复）
- **PostCollect**: 收藏记录表（防重复）
- **PostComment**: 评论表，支持嵌套回复

### 2. 表单 (`baweb/forms/postforms.py`)
- `PostCreateForm`: 创建帖子表单
- `PostUpdateForm`: 更新帖子表单
- `PostCommentForm`: 评论表单
- `PostSearchForm`: 搜索表单（支持按关键词、分类、排序）

### 3. 视图层 (`baweb/views/forum.py`)
完整的论坛功能视图：
- `post_list()`: 帖子列表（支持分页、搜索、排序）
- `post_detail()`: 帖子详情
- `post_create()`: 创建帖子
- `post_update()`: 更新帖子
- `post_delete()`: 删除帖子
- `post_like()`: 点赞帖子
- `post_collect()`: 收藏帖子
- `comment_add()`: 添加评论
- `comment_delete()`: 删除评论
- `comment_like()`: 点赞评论

### 4. 数据库迁移 (`baweb/migrations/0022_post_forum_system.py`)
完整的迁移文件，包含所有表创建和索引设置。

## 🚀 安装步骤

### 第一步：应用数据库迁移
```bash
# 使用 Python 3.7（项目要求版本）
python manage.py migrate baweb

# 或者仅迁移最新的迁移
python manage.py migrate baweb 0022_post_forum_system
```

### 第二步：初始化内容分类（可选）
```bash
python manage.py shell
```

在 Django shell 中执行：
```python
from baweb import models

# 创建内容分类
models.ContentCategory.objects.get_or_create(name=1, defaults={'description': '问答讨论'})
models.ContentCategory.objects.get_or_create(name=2, defaults={'description': '知识分享'})
models.ContentCategory.objects.get_or_create(name=3, defaults={'description': '资源分享'})
```

### 第三步：在 `baplatform/urls.py` 中添加路由

```python
from baweb.views import forum

urlpatterns = [
    # ... existing patterns ...
    
    # 论坛相关路由
    path('forum/course/<int:course_id>/posts/', forum.post_list, name='post_list'),
    path('forum/post/<str:post_id>/', forum.post_detail, name='post_detail'),
    path('forum/course/<int:course_id>/create/', forum.post_create, name='post_create'),
    path('forum/post/<str:post_id>/update/', forum.post_update, name='post_update'),
    path('forum/post/<str:post_id>/delete/', forum.post_delete, name='post_delete'),
    path('forum/post/<str:post_id>/like/', forum.post_like, name='post_like'),
    path('forum/post/<str:post_id>/collect/', forum.post_collect, name='post_collect'),
    path('forum/post/<str:post_id>/comment/', forum.comment_add, name='comment_add'),
    path('forum/comment/<str:comment_id>/delete/', forum.comment_delete, name='comment_delete'),
    path('forum/comment/<str:comment_id>/like/', forum.comment_like, name='comment_like'),
]
```

## 📊 数据库表结构

### Post 表
```
postId (UUID, pk): 帖子ID
title: 标题
content: 内容
author_id (FK): 作者ID
course_id (FK): 课程ID
category_id (FK): 分类ID
tags: 标签（逗号分隔）
isAnonymous: 是否匿名
createdAt: 创建时间
updatedAt: 更新时间
likeCount: 点赞数
collectCount: 收藏数
commentCount: 评论数
viewCount: 浏览数
heatScore: 热度分数（有索引）
embedding: 向量嵌入（可选，用于AI推荐）
```

### PostComment 表
```
commentId (UUID, pk): 评论ID
content: 评论内容
post_id (FK): 所属帖子
author_id (FK): 评论者
parentComment_id (FK, nullable): 父评论（支持嵌套）
isAnonymous: 是否匿名
createdAt: 创建时间
updatedAt: 更新时间
likeCount: 点赞数
```

## 🔑 关键特性

### 1. 热度算法 (Post.calculateHeat)
```
热度 = 交互权重 × 时间衰减 × 0.7 + 新鲜度 × 0.3

交互权重 = 点赞数 + 评论数×2 + 收藏数×3
时间衰减 = 1/log(天数+1)
新鲜度 = 100 × (1 - 已用时间/7天) （如果>7天则继续衰减）
```

### 2. 新鲜度计算 (Post.calculateFreshness)
- 7天内：100分满分
- 7天后：按30天周期继续衰减

### 3. 权限控制
- 学生和教师可以发帖
- 只有帖子作者或管理员可以删除
- 所有登录用户可以评论、点赞、收藏

### 4. 防重复机制
- `PostLike` 表使用 `unique_together`
- `PostCollect` 表使用 `unique_together`

### 5. 性能优化
- `postId`, `commentId` 有数据库索引
- `heatScore` 有索引（用于排序查询）
- `Post` 表有复合索引：(course_id, -heatScore)

## 📝 使用示例

### 发布帖子
```python
from baweb import models
from uuid import uuid4

post = models.Post.objects.create(
    postId=str(uuid4()),
    title="Python 异步编程探讨",
    content="讨论 async/await 的最佳实践...",
    author=user_obj,
    course=course_obj,
    category=category_obj,
    tags="Python,异步,并发",
)
```

### 计算热度
```python
heat_score = post.calculateHeat()
post.heatScore = heat_score
post.save()
```

### 查询热门帖子
```python
# 按热度排序
top_posts = models.Post.objects.filter(
    course=course_obj
).order_by('-heatScore')[:10]

# 按热度和时间综合排序
recent_hot = models.Post.objects.filter(
    course=course_obj,
    createdAt__gte=timezone.now() - timedelta(days=7)
).order_by('-heatScore')[:20]
```

## ⚠️ 注意事项

1. **Python 版本**：项目需要 Python 3.7 运行迁移
2. **UUID 字段**：postId 和 commentId 使用 UUID 格式存储
3. **时间戳**：所有时间字段使用 UTC 时区（请确保 Django 设置中 `USE_TZ=True`）
4. **向量嵌入**：embedding 字段为可选，后续可集成 AI 向量搜索

## 🔍 常见查询

```python
# 获取课程中的所有帖子
posts = models.Post.objects.filter(course_id=1)

# 获取用户的所有帖子
user_posts = models.Post.objects.filter(author_id=user.id)

# 获取用户收藏的帖子
collected = models.PostCollect.objects.filter(user_id=user.id).values_list('post_id', flat=True)
user_collected_posts = models.Post.objects.filter(postId__in=collected)

# 获取评论及其回复
comment = models.PostComment.objects.get(commentId='xxx')
replies = comment.replies.all()

# 搜索帖子
results = models.Post.objects.filter(
    Q(title__icontains='Python') | Q(content__icontains='Python')
)
```

## 🎯 下一步开发方向

1. **模板文件**：需要创建前端模板（forum/post_list.html 等）
2. **AI推荐**：集成向量搜索，基于 embedding 推荐相似帖子
3. **积分系统**：集成积分奖励机制（发帖+10分、被点赞+2分等）
4. **内容审核**：实现不当内容自动检测
5. **热度更新任务**：定期异步更新所有帖子热度（Celery）

