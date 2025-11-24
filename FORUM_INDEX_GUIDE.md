# 论坛首页使用指南

## 功能概述

论坛首页是一个汇总所有课程帖子的中心页面,包括:
- ✅ 显示所有课程的帖子
- ✅ 显示不属于任何课程的公共讨论帖子
- ✅ 按课程筛选
- ✅ 按分类筛选
- ✅ 搜索功能
- ✅ 排序(热度/最新)
- ✅ 发布新帖(无需指定课程)

## 访问地址

```
http://127.0.0.1:8000/forum/
```

## 主要功能

### 1. 查看所有帖子
- 访问 `/forum/` 查看所有帖子汇总
- 默认按热度排序
- 显示每个帖子所属的课程(或"公共讨论"标签)

### 2. 课程筛选
侧边栏提供课程筛选:
- **全部课程**: 显示所有帖子
- **无归属课程**: 只显示公共讨论帖子(不属于任何课程)
- **具体课程**: 显示该课程的帖子

### 3. 分类筛选
按内容分类筛选帖子:
- 问答
- 讨论
- 分享
- 公告
- 其他

### 4. 搜索功能
- 在搜索框输入关键词
- 搜索范围包括帖子标题和内容

### 5. 排序方式
- **热度排序**: 根据点赞、评论、收藏综合计算
- **最新排序**: 按发布时间倒序

### 6. 发布新帖
- 点击侧边栏"发布新帖子"按钮
- 跳转到发帖页面(无需指定课程)
- 可选择是否关联到某个课程

## URL路由说明

### 新增路由

```python
# 论坛首页
path('forum/', forum.forum_index, name='forum_index')

# 无课程发帖
path('forum/create/', forum.post_create, name='post_create_no_course')

# 课程内发帖(保留原有功能)
path('forum/course/<int:course_id>/create/', forum.post_create, name='post_create')
```

## 视图函数说明

### forum_index视图

**位置**: `baweb/views/forum.py`

**功能**:
- 查询所有帖子
- 支持课程筛选(`?course_id=1` 或 `?course_id=none`)
- 支持分类筛选(`?category_id=1`)
- 支持搜索(`?keyword=关键词`)
- 支持排序(`?sort_by=heat` 或 `?sort_by=newest`)
- 分页显示(每页20条)

**模板**: `forum/forum_index.html`

## 数据模型说明

### Post模型的course字段

```python
course = models.ForeignKey(Course, verbose_name='所属课程', 
                          on_delete=models.CASCADE, 
                          related_name='course_posts')
```

- `course`字段可以为`None`(通过修改视图实现)
- 当`course=None`时,帖子不属于任何课程,显示为"公共讨论"
- 当`course`有值时,显示课程名称徽章

## 页面布局

### 头部区域
- 论坛标题
- 统计数据(总帖子数、总评论数)

### 侧边栏
- 发帖按钮
- 课程筛选列表
- 分类筛选列表

### 主内容区
- 搜索框和排序按钮
- 帖子卡片列表
- 分页导航

### 帖子卡片信息
- 标题 + 课程徽章
- 作者、发布时间、分类
- 内容预览(30字)
- 标签
- 统计数据(浏览、点赞、评论、收藏)

## 使用示例

### 1. 查看所有帖子
```
GET /forum/
```

### 2. 筛选某个课程的帖子
```
GET /forum/?course_id=1
```

### 3. 查看公共讨论(无课程)
```
GET /forum/?course_id=none
```

### 4. 搜索帖子
```
GET /forum/?keyword=作业
```

### 5. 组合筛选
```
GET /forum/?course_id=1&category_id=2&sort_by=newest&keyword=问题
```

## 测试步骤

### 1. 启动服务器
```powershell
cd baplatform
.\baplatform_env\Scripts\Activate.ps1
python manage.py runserver 0.0.0.0:8000
```

### 2. 访问论坛首页
```
http://127.0.0.1:8000/forum/
```

### 3. 测试功能
- ✅ 查看是否显示所有帖子
- ✅ 点击课程筛选,测试筛选功能
- ✅ 点击"无归属课程",测试公共讨论筛选
- ✅ 输入关键词搜索
- ✅ 切换排序方式
- ✅ 点击帖子卡片跳转到详情页
- ✅ 点击"发布新帖子"按钮

### 4. 测试发帖功能
- 访问 `/forum/create/`
- 填写标题、内容
- 提交后应创建一个无课程归属的帖子
- 返回论坛首页,在"无归属课程"筛选中应能看到

## 设计特点

### 视觉设计
- 紫色渐变主题(#667eea → #764ba2)
- 卡片式布局
- 响应式设计
- 悬停动效

### 用户体验
- 清晰的视觉层次
- 直观的筛选导航
- 丰富的统计信息
- 便捷的发帖入口

### 性能优化
- 使用`select_related`减少数据库查询
- 分页显示(每页20条)
- 标签预处理避免模板中复杂逻辑

## 注意事项

1. **课程筛选**: `course_id=none`表示无课程帖子,空值表示所有帖子
2. **权限控制**: 发帖功能需要登录,管理员不能发帖
3. **标签显示**: 标签使用逗号分隔,在视图中预处理为列表
4. **热度计算**: 使用Post模型的`heatScore`字段
5. **匿名显示**: 如果`isAnonymous=True`,显示"匿名用户"

## 后续优化建议

1. **热门标签**: 在侧边栏添加热门标签云
2. **推荐帖子**: 基于用户兴趣推荐相关帖子
3. **实时更新**: 使用WebSocket实现帖子实时更新
4. **高级搜索**: 支持按作者、时间范围等高级搜索
5. **个人中心**: 我的帖子、我的收藏快捷入口
6. **通知系统**: 帖子回复、点赞通知

## 相关文件

- 视图: `baweb/views/forum.py` → `forum_index()`
- 模板: `baweb/templates/forum/forum_index.html`
- URL配置: `baplatform/urls.py`
- 数据模型: `baweb/models.py` → `Post`, `Course`, `ContentCategory`
