# Post 论坛系统 - 快速参考手册

## 🔍 模型快速查询

### Post 模型方法

```python
from baweb import models
from uuid import uuid4

# 创建帖子
post = models.Post.objects.create(
    postId=str(uuid4()),
    title="Python 最佳实践",
    content="讨论 Python 编程规范...",
    author=user_obj,
    course=course_obj,
    category=category_obj,
    tags="Python,最佳实践",
)

# 计算热度
heat = post.calculateHeat()  # 返回 float

# 计算新鲜度（0-100）
freshness = post.calculateFreshness()  # 返回 float

# 更新内容
post.updateContent(
    new_title="新标题",
    new_content="新内容",
)

# 按热度排序查询
top_posts = models.Post.objects.filter(
    course=course_obj
).order_by('-heatScore')[:10]
```

### PostComment 模型方法

```python
# 创建评论
comment = models.PostComment.objects.create(
    commentId=str(uuid4()),
    post=post_obj,
    author=user_obj,
    content="这个想法很有趣...",
    isAnonymous=False,
)

# 点赞评论
comment.like()

# 回复评论
reply = comment.reply(
    reply_content="我同意你的观点",
    reply_author=user_obj,
    is_anonymous=False,
)

# 获取评论的所有回复
replies = comment.replies.all()
```

## 🛣️ URL 路由映射
以下列出了论坛模块中主要的 URL 路由。每条路由旁标注了支持的 HTTP 方法与对应的视图函数。参数说明：`<course_id>` 为课程表 `Course.id`（整型），`<post_id>` 和 `<comment_id>` 为模型中使用的 UUID 字符串（对应 `postId` / `commentId` 字段）。

- GET 请求通常渲染页面；POST 请求用于表单提交或 AJAX 操作，返回 JSON 响应。

```
GET  /forum/course/<course_id>/posts/
     → post_list() 列表页

GET  /forum/post/<post_id>/
     → post_detail() 详情页

GET/POST /forum/course/<course_id>/create/
     → post_create() 创建帖子

POST /forum/post/<post_id>/update/
     → post_update() 更新帖子

POST /forum/post/<post_id>/delete/
     → post_delete() 删除帖子

POST /forum/post/<post_id>/like/
     → post_like() 点赞

POST /forum/post/<post_id>/collect/
     → post_collect() 收藏

POST /forum/post/<post_id>/comment/
     → comment_add() 添加评论

POST /forum/comment/<comment_id>/delete/
     → comment_delete() 删除评论

POST /forum/comment/<comment_id>/like/
     → comment_like() 点赞评论
```

## 📋 API 响应格式

### 成功响应
```json
{
  "status": true,
  "msg": "操作成功描述",
  "postId": "xxx-xxx-xxx",
  "like_count": 10,
  "heat_score": 45.3
}
```

### 错误响应
```json
{
  "status": false,
  "msg": "错误信息",
  "errors": {"field": ["错误详情"]}
}
```

## 🔐 权限检查模式

```python
# 视图中的标准权限检查
info = request.session.get('info', {})
user_id = info.get('id')

if not user_id:
    return JsonResponse({"status": False, "msg": "未登录"})

user = models.User.objects.filter(id=user_id).first()

# 检查是否为特定类型用户
if user.type != 2:  # 1=学生, 2=教师, 3=管理员
    return JsonResponse({"status": False, "msg": "无权限"})

# 检查资源所有权
if resource.author.id != user_id and user.type != 3:
    return JsonResponse({"status": False, "msg": "无权限修改"})
```

## 🔄 AJAX 调用示例

### 点赞帖子
```javascript
fetch('/forum/post/{{ post.postId }}/like/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  }
})
.then(r => r.json())
.then(data => {
  if (data.status) {
    // 更新点赞数
    document.getElementById('like_count').textContent = data.like_count;
    // 更新热度
    document.getElementById('heat_score').textContent = data.heat_score.toFixed(2);
  }
})
```

### 发表评论
```javascript
const formData = new FormData(document.getElementById('comment_form'));
fetch('/forum/post/{{ post.postId }}/comment/', {
  method: 'POST',
  body: formData,
})
.then(r => r.json())
.then(data => {
  if (data.status) {
    // 刷新评论列表
    location.reload();
  }
})
```

## 📊 数据库查询示例

### 获取课程内的热门帖子
```python
from django.utils import timezone
from datetime import timedelta

# 最近7天的热门帖子
recent_hot = models.Post.objects.filter(
    course_id=1,
    createdAt__gte=timezone.now() - timedelta(days=7)
).order_by('-heatScore')[:20]
```

### 获取用户的所有交互
```python
# 用户发表的帖子
my_posts = models.Post.objects.filter(author_id=user.id)

# 用户发表的评论
my_comments = models.PostComment.objects.filter(author_id=user.id)

# 用户点赞过的帖子
my_likes = models.PostLike.objects.filter(user_id=user.id).select_related('post')
liked_posts = [like.post for like in my_likes]

# 用户收藏的帖子
my_collects = models.PostCollect.objects.filter(user_id=user.id).select_related('post')
collected_posts = [collect.post for collect in my_collects]
```

### 搜索帖子
```python
from django.db.models import Q

# 按标题或内容搜索
results = models.Post.objects.filter(
    Q(title__icontains='Django') | Q(content__icontains='Django'),
    course_id=1
)

# 按分类搜索
qa_posts = models.Post.objects.filter(
    course_id=1,
    category__name=1  # 问答类
)

# 组合搜索
combined = models.Post.objects.filter(
    Q(title__icontains='API'),
    category__name=1,
    createdAt__gte=timezone.now() - timedelta(days=7)
).order_by('-heatScore')
```

### 评论树形查询
```python
# 获取帖子的顶层评论
top_comments = models.PostComment.objects.filter(
    post_id=post.id,
    parentComment__isnull=True
).order_by('-createdAt')

# 获取某评论的所有回复
replies = models.PostComment.objects.filter(
    parentComment_id=comment.id
).order_by('createdAt')

# 深度优先递归获取所有回复
def get_comment_tree(comment):
    tree = {
        'comment': comment,
        'replies': []
    }
    for reply in comment.replies.all():
        tree['replies'].append(get_comment_tree(reply))
    return tree
```

## 🧪 测试命令

```bash
# 进入 Django shell
python manage.py shell

# 创建测试帖子
from baweb import models
from uuid import uuid4
import random

user = models.User.objects.first()
course = models.Course.objects.first()
category = models.ContentCategory.objects.first()

for i in range(5):
    post = models.Post.objects.create(
        postId=str(uuid4()),
        title=f"测试帖子 {i}",
        content=f"这是测试内容 {i}" * 10,
        author=user,
        course=course,
        category=category,
        tags="测试,示例",
    )
    # 模拟交互
    post.likeCount = random.randint(0, 50)
    post.commentCount = random.randint(0, 20)
    post.viewCount = random.randint(10, 1000)
    post.heatScore = post.calculateHeat()
    post.save()

# 查询热门帖子
hot = models.Post.objects.order_by('-heatScore')[:5]
for p in hot:
    print(f"{p.title}: 热度={p.heatScore:.2f}")
```

## 📝 表单验证示例

```python
from baweb.forms.postforms import PostCreateForm

# 验证创建帖子的表单
form_data = {
    'title': '我的问题',
    'content': '详细描述...',
    'category': 1,
    'tags': 'Python,Django',
    'isAnonymous': False,
}

form = PostCreateForm(data=form_data)
if form.is_valid():
    print("表单有效")
    print(f"标题: {form.cleaned_data['title']}")
else:
    print("表单错误:", form.errors)
```

## 🔧 性能优化建议

1. **查询优化**
   ```python
   # 使用 select_related 减少查询
   posts = models.Post.objects.select_related(
       'author', 'course', 'category'
   ).filter(course_id=1)
   ```

2. **缓存热度计算**
   ```python
   # 定时更新热度，而不是每次查询时计算
   from django.core.cache import cache
   
   heat = cache.get(f'post_heat_{post.id}')
   if not heat:
       heat = post.calculateHeat()
       cache.set(f'post_heat_{post.id}', heat, 3600)  # 缓存1小时
   ```

3. **批量操作**
   ```python
   # 批量创建分类
   categories = models.ContentCategory.objects.bulk_create([
       models.ContentCategory(name=1, description='Q&A'),
       models.ContentCategory(name=2, description='Share'),
   ])
   ```

---

📖 **完整文档请参考：**
- `FORUM_INTEGRATION_GUIDE.md` - 集成步骤
- `FORUM_IMPLEMENTATION_SUMMARY.md` - 实现详情
