"""
使用Django shell初始化分类
"""
from baweb.models import ContentCategory

categories = [
    (1, "问答", "提问和解答各类学习问题"),
    (2, "知识分享", "分享学习经验和知识点"),
    (3, "资源分享", "分享学习资源、工具和资料"),
    (4, "作业讨论", "讨论作业相关的问题"),
    (5, "课程反馈", "对课程内容和教学的反馈"),
    (6, "学习心得", "分享学习心得体会"),
    (7, "求助", "寻求帮助和支持"),
    (8, "闲聊", "轻松话题和日常交流"),
    (9, "通知公告", "重要通知和公告信息"),
    (10, "项目协作", "项目合作和团队协作"),
]

created_count = 0
updated_count = 0

for cat_id, cat_name, description in categories:
    category, created = ContentCategory.objects.get_or_create(
        name=cat_id,
        defaults={'description': description}
    )
    
    if created:
        created_count += 1
        print(f"✓ 创建分类: {cat_id} - {cat_name}")
    else:
        if category.description != description:
            category.description = description
            category.save()
            updated_count += 1
            print(f"✓ 更新分类: {cat_id} - {cat_name}")
        else:
            print(f"- 分类已存在: {cat_id} - {cat_name}")

print(f"\n总结:")
print(f"- 新创建: {created_count} 个分类")
print(f"- 更新: {updated_count} 个分类")
print(f"- 总数: {ContentCategory.objects.count()} 个分类")

print(f"\n当前所有分类:")
for cat in ContentCategory.objects.all().order_by('name'):
    cat_display = dict(cat.category_choices).get(cat.name, '未知')
    print(f"  {cat.name}. {cat_display} - {cat.description}")
