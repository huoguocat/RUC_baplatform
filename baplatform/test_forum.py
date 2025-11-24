"""
论坛功能快速测试脚本
使用方法：python manage.py shell < test_forum.py
"""

from baweb.models import Course, Post, User, ContentCategory, PostComment
from django.utils import timezone
import uuid

print("=" * 60)
print("论坛功能测试脚本")
print("=" * 60)

# 1. 检查用户
print("\n1. 检查用户...")
user = User.objects.first()
if user:
    print(f"   ✓ 找到用户: {user.username} (ID: {user.id}, 类型: {user.get_type_display()})")
else:
    print("   ✗ 没有找到用户，正在创建测试用户...")
    user = User.objects.create(
        username='forum_test_user',
        password='pbkdf2_sha256$150000$test$test',  # 简单的测试密码
        type=1  # 学生
    )
    print(f"   ✓ 已创建测试用户: {user.username}")

# 2. 检查课程
print("\n2. 检查课程...")
course = Course.objects.first()
if course:
    print(f"   ✓ 找到课程: {course.name} (ID: {course.id})")
else:
    print("   ✗ 没有找到课程，无法继续测试")
    print("   请先在管理后台创建课程")
    exit()

# 3. 检查或创建分类
print("\n3. 检查内容分类...")
category = ContentCategory.objects.first()
if not category:
    print("   正在创建默认分类...")
    categories = [
        {'name': '讨论', 'description': '课程相关讨论'},
        {'name': '问答', 'description': '问题解答'},
        {'name': '分享', 'description': '学习资源分享'},
        {'name': '公告', 'description': '课程公告'},
    ]
    for cat_data in categories:
        ContentCategory.objects.create(
            categoryId=str(uuid.uuid4()),
            name=cat_data['name'],
            description=cat_data['description']
        )
    category = ContentCategory.objects.first()
    print(f"   ✓ 已创建 {len(categories)} 个分类")
else:
    print(f"   ✓ 找到分类: {category.name}")

# 4. 创建测试帖子
print("\n4. 创建测试帖子...")
existing_posts = Post.objects.filter(course=course).count()
print(f"   当前课程已有 {existing_posts} 个帖子")

if existing_posts < 10:
    posts_to_create = 10 - existing_posts
    print(f"   正在创建 {posts_to_create} 个测试帖子...")
    
    for i in range(posts_to_create):
        post_num = existing_posts + i + 1
        post = Post.objects.create(
            postId=str(uuid.uuid4()),
            author=user,
            course=course,
            title=f'测试帖子 #{post_num} - {["Python基础", "Django开发", "数据库设计", "Web前端", "项目实战"][i % 5]}',
            content=f'''这是第 {post_num} 个测试帖子的内容。

## 帖子简介
本帖子用于测试论坛的各项功能。

## 主要内容
1. 帖子发布功能测试
2. 帖子展示功能测试
3. 评论互动功能测试
4. 点赞收藏功能测试

## 讨论话题
欢迎大家在评论区讨论相关问题！

---
*这是一个自动生成的测试帖子*
''',
            category=category,
            tags=['测试', 'Django', '论坛'][:(i % 3 + 1)],  # 1-3个标签
            isAnonymous=(i % 3 == 0),  # 每3个帖子有1个匿名
            likeCount=(post_num * 2) % 50,
            commentCount=(post_num) % 20,
            viewCount=(post_num * 10) % 200,
            heatScore=100 - (i * 5)
        )
    
    print(f"   ✓ 已创建 {posts_to_create} 个测试帖子")
else:
    print("   ✓ 帖子数量充足，无需创建")

# 5. 为部分帖子添加测试评论
print("\n5. 为帖子添加测试评论...")
posts_with_no_comments = Post.objects.filter(course=course, commentCount=0)[:3]

for post in posts_with_no_comments:
    # 创建2-3条评论
    num_comments = (hash(post.postId) % 2) + 2
    for j in range(num_comments):
        comment = PostComment.objects.create(
            commentId=str(uuid.uuid4()),
            post=post,
            author=user,
            content=f'这是对帖子《{post.title}》的第 {j+1} 条测试评论。\n\n评论内容可以很详细，支持换行和格式。',
            isAnonymous=(j % 2 == 0),
            likeCount=j * 3
        )
    
    # 更新评论计数
    post.commentCount = num_comments
    post.save()
    
    print(f"   ✓ 为帖子 '{post.title}' 添加了 {num_comments} 条评论")

# 6. 显示测试结果
print("\n" + "=" * 60)
print("测试数据统计")
print("=" * 60)

total_posts = Post.objects.filter(course=course).count()
total_comments = PostComment.objects.filter(post__course=course).count()
anonymous_posts = Post.objects.filter(course=course, isAnonymous=True).count()

print(f"课程: {course.name}")
print(f"总帖子数: {total_posts}")
print(f"总评论数: {total_comments}")
print(f"匿名帖子数: {anonymous_posts}")
print(f"分类数: {ContentCategory.objects.count()}")

# 7. 显示访问链接
print("\n" + "=" * 60)
print("测试链接")
print("=" * 60)
print(f"\n论坛列表页:")
print(f"http://localhost:8000/forum/course/{course.id}/posts/")

print(f"\n发布帖子页:")
print(f"http://localhost:8000/forum/course/{course.id}/create/")

if total_posts > 0:
    latest_post = Post.objects.filter(course=course).order_by('-createdAt').first()
    print(f"\n最新帖子详情页:")
    print(f"http://localhost:8000/forum/post/{latest_post.postId}/")

print("\n" + "=" * 60)
print("✓ 测试数据准备完成！")
print("=" * 60)
print("\n提示: 请确保服务器正在运行")
print("启动命令: python manage.py runserver 0.0.0.0:8000")
print("=" * 60)
