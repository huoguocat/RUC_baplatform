from django.db import models
from ckeditor.fields import RichTextField

# Create your models here.
class User(models.Model):
    '''用户表'''
    username = models.CharField(verbose_name='用户', max_length=16, unique=True)
    password = models.CharField(verbose_name='密码', max_length=64)
    type_choices = (
        (1, "学生"),
        (2, "老师"),
        (3, "管理员"),
    )
    type = models.SmallIntegerField(verbose_name='用户类型', choices=type_choices)

class StudentInfo(models.Model):
    '''学生信息表'''
    user = models.OneToOneField(User, verbose_name='学生', on_delete=models.CASCADE, primary_key=True, related_name='Student')
    name = models.CharField(verbose_name='名字', max_length=64, default="未知")
    gender_choices = (
        (1, "男"),
        (2, "女"),  
        (3, "保密")
    )
    gender = models.SmallIntegerField(verbose_name='性别',choices=gender_choices, default=3, blank=True)
    email = models.EmailField(verbose_name='邮箱', max_length=64, blank=True)
    phone = models.CharField(verbose_name='手机号', max_length=16, blank=True)
    student_profile_pic = models.ImageField(verbose_name='头像', upload_to="userimg/student_profile_pic", blank=True)

    def __str__(self):
        return self.name

class TeacherInfo(models.Model):
    '''老师信息表'''
    user = models.OneToOneField(User, verbose_name='老师', on_delete=models.CASCADE, primary_key=True, related_name='Teacher')
    name = models.CharField(verbose_name='名字', max_length=64, default="未知")
    gender_choices = (
        (1, "男"),
        (2, "女"),  
        (3, "保密")
    )
    gender = models.SmallIntegerField(verbose_name='性别',choices=gender_choices, default=3, blank=True)
    email = models.EmailField(verbose_name='邮箱', max_length=64, blank=True)
    phone = models.CharField(verbose_name='手机号', max_length=16, blank=True)
    description = models.TextField(verbose_name='教师简介', max_length=1000, blank=True)
    teacher_profile_pic = models.ImageField(verbose_name='头像', upload_to="userimg/teacher_profile_pic", blank=True)
    description_richtext = RichTextField(verbose_name='教师简介', blank=True)
    order = models.IntegerField(verbose_name='顺序',default=0 ,blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['order']

class Course(models.Model):
    '''课程表'''
    name = models.CharField(verbose_name='课程名', max_length=64)
    teacher = models.ForeignKey(TeacherInfo, verbose_name='教课老师', on_delete=models.CASCADE, related_name='course_teacher')
    course_profile_pic = models.ImageField(verbose_name='课程图', upload_to="userimg/course_profile_pic/", blank=True)
    description = models.TextField(verbose_name='课程简介', max_length=1000, blank=True)
    description_richtext = RichTextField(verbose_name='课程简介', blank=True)
    order = models.IntegerField(verbose_name="课程顺序", default=0, blank=True)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']

class CourseFiles(models.Model):
    '''课件表'''
    course = models.ForeignKey(Course, verbose_name='所属课程', on_delete=models.CASCADE, related_name='file_course')
    file = models.FileField(verbose_name='课件', upload_to="files/")
    file_name = models.CharField(verbose_name='课件名', max_length=64, default=file.name, blank=True)

    def __str__(self):
        return self.file_name

class Assignment(models.Model):
    '''任务表'''
    name = models.CharField(verbose_name='任务名', max_length=64)
    course = models.ForeignKey(Course, verbose_name='所属课程', on_delete=models.CASCADE, related_name='assignment_course')
    description = models.TextField(verbose_name='任务简介', max_length=1000, blank=True)
    description_richtext = RichTextField(verbose_name='任务简介', blank=True)
    is_group = models.BooleanField(verbose_name='是否是小组任务', default=False)
    ddl = models.DateField(verbose_name='任务截止时间')

    def __str__(self):
        return self.name

class AssignmentFile(models.Model):
    '''任务文档'''
    file = models.FileField(verbose_name='任务文档', upload_to="assignments/")
    file_name = models.CharField(verbose_name='文档名', max_length=64 ,default=file.name, blank=True)
    assignment = models.ForeignKey(Assignment, verbose_name='所属任务', on_delete=models.CASCADE, related_name='file_assignment')

    def __str__(self):
        return self.file_name

class AssignmentComment(models.Model):
    '''任务评价'''
    comment =  models.TextField(verbose_name='任务评价')
    assignment = models.ForeignKey(Assignment, verbose_name='所属任务', on_delete=models.CASCADE, related_name="comment_assignment")
    user = models.ForeignKey(User, verbose_name='评价人', on_delete=models.CASCADE, related_name='comment_user')
    created_at = models.DateField(verbose_name='评价时间', auto_now=True)

    class Meta:
        ordering = ['-created_at']

class CourseComment(models.Model):
    '''课程讨论'''
    comment = models.TextField(verbose_name="评论")
    course = models.ForeignKey(Course, verbose_name="所属课程", on_delete=models.CASCADE, related_name="comment_course")
    user = models.ForeignKey(User, verbose_name='评价人', on_delete=models.CASCADE, related_name='coursecomment_user')
    created_at = models.DateField(verbose_name='评价时间', auto_now=True)

    class Meta:
        ordering = ['-created_at']

class StudentCourse(models.Model):
    '''学生课程表'''
    student = models.ForeignKey(StudentInfo, verbose_name='选课学生', on_delete=models.CASCADE, related_name='course_student')
    course = models.ForeignKey(Course, verbose_name='被选课程', on_delete=models.CASCADE, related_name='student_course')
    
class AssignmentSubmit(models.Model):
    '''学生提交任务'''
    student = models.ForeignKey(StudentInfo, verbose_name='学生', on_delete=models.CASCADE, related_name='assignmentsubmit_student')
    assignment = models.ForeignKey(Assignment, verbose_name='所提交的任务', on_delete=models.CASCADE, related_name='submit_assignment')
    file = models.FileField(verbose_name='任务文档', upload_to="submission/")
    file_name = models.CharField(verbose_name='文档名', max_length=64 ,default=file.name, blank=True)
    marks = models.SmallIntegerField(verbose_name='获得分数', default=0)
    max_marks = models.SmallIntegerField(verbose_name='最大分数', default=100)
    submit_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name

class Group(models.Model):
    '''小组表'''
    course = models.ForeignKey(Course, verbose_name='所属课程', on_delete=models.CASCADE, related_name='group_course')
    name = models.CharField(verbose_name="组名", max_length=64, unique=True)

    def __str__(self):
        return self.name

class GroupMember(models.Model):
    '''小组成员'''
    group = models.ForeignKey(Group, verbose_name='所属小组', on_delete=models.CASCADE, related_name='groupmember_group')
    student = models.ForeignKey(StudentInfo, verbose_name="小组成员", on_delete=models.CASCADE, related_name='groupmember_student')
    is_head = models.BooleanField()

    def __str__(self):
        return self.student.name
    submit_time = models.DateTimeField(auto_now=True)

class Announce(models.Model):
    '''老师通知'''
    announcement = models.TextField(verbose_name="通知")
    teacher = models.ForeignKey(TeacherInfo, verbose_name="所属老师", on_delete=models.CASCADE, related_name='announce_teacher')
    course = models.ForeignKey(Course, verbose_name='所属课程', on_delete=models.CASCADE, related_name="announce_course")

    created_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']

class TeacherDisabled(models.Model):
    '''禁用教师'''
    teacher = models.ForeignKey(User, verbose_name="禁用教师", on_delete=models.CASCADE, related_name="teacher_disabled")


# ==================== 论坛系统模型 ====================

class ContentCategory(models.Model):
    '''内容分类表'''
    category_choices = (
        (1, "问答"),
        (2, "知识分享"),
        (3, "资源分享"),
    )
    name = models.SmallIntegerField(verbose_name='内容分类', choices=category_choices, default=1)
    description = models.CharField(verbose_name='分类描述', max_length=256, blank=True)

    class Meta:
        verbose_name_plural = '内容分类'

    def __str__(self):
        return self.get_name_display()


class Post(models.Model):
    '''帖子/讨论表'''
    # 基本属性
    postId = models.CharField(verbose_name='帖子ID', max_length=64, unique=True, db_index=True)
    author = models.ForeignKey(User, verbose_name='作者', on_delete=models.CASCADE, related_name='user_posts')
    course = models.ForeignKey(Course, verbose_name='所属课程', on_delete=models.CASCADE, related_name='course_posts')
    
    # 内容属性
    title = models.CharField(verbose_name='标题', max_length=256)
    content = models.TextField(verbose_name='内容')
    category = models.ForeignKey(ContentCategory, verbose_name='内容分类', on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(verbose_name='标签', max_length=512, blank=True, help_text='多个标签用逗号分隔')
    
    # 匿名模式
    isAnonymous = models.BooleanField(verbose_name='是否匿名', default=False)
    
    # 时间戳
    createdAt = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updatedAt = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    # 交互统计
    likeCount = models.IntegerField(verbose_name='点赞数', default=0)
    collectCount = models.IntegerField(verbose_name='收藏数', default=0)
    commentCount = models.IntegerField(verbose_name='评论数', default=0)
    viewCount = models.IntegerField(verbose_name='浏览数', default=0)
    
    # 热度计算
    heatScore = models.FloatField(verbose_name='热度分数', default=0.0, db_index=True)
    
    # AI向量嵌入（可选，用于向量搜索和推荐）
    embedding = models.BinaryField(verbose_name='内容嵌入向量', null=True, blank=True, 
                                   help_text='768维向量，用于智能推荐和语义搜索')

    class Meta:
        ordering = ['-heatScore', '-createdAt']
        indexes = [
            models.Index(fields=['course', '-heatScore']),
            models.Index(fields=['-createdAt']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return self.title

    def calculateFreshness(self):
        '''计算新鲜度得分（时间衰减）
        
        Returns:
            float: 0-100 之间的新鲜度分数，越接近100表示越新
        '''
        from django.utils import timezone
        from datetime import timedelta
        
        time_diff = (timezone.now() - self.createdAt).total_seconds()
        # 7天内为最新，7天后开始衰减
        max_age_seconds = 7 * 24 * 3600
        
        if time_diff <= max_age_seconds:
            freshness = 100 * (1 - time_diff / max_age_seconds)
        else:
            freshness = max(0, 100 * (1 - time_diff / (30 * 24 * 3600)))
        
        return max(0, min(100, freshness))

    def calculateHeat(self):
        '''计算帖子热度
        
        热度算法：
        - 互动权重 70%：(点赞 + 评论*2 + 收藏*3) / (时间衰减)
        - 时间权重 30%：新鲜度分数
        
        Returns:
            float: 热度分数
        '''
        import math
        
        # 交互量权重：70%
        interaction_score = self.likeCount + self.commentCount * 2 + self.collectCount * 3
        freshness = self.calculateFreshness()
        
        # 时间衰减因子
        from django.utils import timezone
        time_diff_days = (timezone.now() - self.createdAt).days + 1
        time_decay = 1.0 / math.log(time_diff_days + 1) if time_diff_days > 0 else 1.0
        
        # 综合热度计算
        heat = (interaction_score * time_decay * 0.7) + (freshness * 0.3)
        return max(0, heat)

    def updateContent(self, new_title=None, new_content=None, new_category=None, new_tags=None):
        '''更新帖子内容
        
        Args:
            new_title (str): 新标题
            new_content (str): 新内容
            new_category (ContentCategory): 新分类
            new_tags (str): 新标签（逗号分隔）
        
        Returns:
            bool: 更新是否成功
        '''
        if new_title:
            self.title = new_title
        if new_content:
            self.content = new_content
        if new_category:
            self.category = new_category
        if new_tags:
            self.tags = new_tags
        
        self.save()
        return True

    def setBounty(self, bounty_points):
        '''设置悬赏分数（积分系统集成）
        
        Args:
            bounty_points (int): 悬赏积分
        
        Returns:
            bool: 设置是否成功
        '''
        # 预留接口用于积分系统集成
        # TODO: 与 IntegralService 集成
        pass


class PostLike(models.Model):
    '''帖子点赞记录表'''
    post = models.ForeignKey(Post, verbose_name='帖子', on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, verbose_name='点赞用户', on_delete=models.CASCADE)
    createdAt = models.DateTimeField(verbose_name='点赞时间', auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 防止重复点赞
        verbose_name_plural = '帖子点赞'

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"


class PostCollect(models.Model):
    '''帖子收藏记录表'''
    post = models.ForeignKey(Post, verbose_name='帖子', on_delete=models.CASCADE, related_name='collects')
    user = models.ForeignKey(User, verbose_name='收藏用户', on_delete=models.CASCADE, related_name='collected_posts')
    createdAt = models.DateTimeField(verbose_name='收藏时间', auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 防止重复收藏
        verbose_name_plural = '帖子收藏'

    def __str__(self):
        return f"{self.user.username} collected {self.post.title}"


class PostComment(models.Model):
    '''帖子评论表'''
    commentId = models.CharField(verbose_name='评论ID', max_length=64, unique=True, db_index=True)
    post = models.ForeignKey(Post, verbose_name='所属帖子', on_delete=models.CASCADE, related_name='post_comments')
    author = models.ForeignKey(User, verbose_name='评论者', on_delete=models.CASCADE, related_name='user_comments')
    
    content = models.TextField(verbose_name='评论内容')
    isAnonymous = models.BooleanField(verbose_name='是否匿名', default=False)
    
    # 支持评论回复
    parentComment = models.ForeignKey('self', verbose_name='父评论', on_delete=models.CASCADE, 
                                      null=True, blank=True, related_name='replies')
    
    createdAt = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updatedAt = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    
    likeCount = models.IntegerField(verbose_name='点赞数', default=0)

    class Meta:
        ordering = ['-createdAt']
        indexes = [
            models.Index(fields=['post', '-createdAt']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

    def like(self):
        '''点赞评论'''
        self.likeCount += 1
        self.save()

    def reply(self, reply_content, reply_author, is_anonymous=False):
        '''回复评论
        
        Args:
            reply_content (str): 回复内容
            reply_author (User): 回复用户
            is_anonymous (bool): 是否匿名
        
        Returns:
            PostComment: 新创建的回复评论对象
        '''
        from uuid import uuid4
        reply = PostComment.objects.create(
            commentId=str(uuid4()),
            post=self.post,
            author=reply_author,
            content=reply_content,
            isAnonymous=is_anonymous,
            parentComment=self
        )
        return reply

