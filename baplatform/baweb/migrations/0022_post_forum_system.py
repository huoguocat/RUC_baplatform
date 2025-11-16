# Generated migration for Post forum system models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("baweb", "0021_alter_course_options_course_order"),
    ]

    operations = [
        # Create ContentCategory model
        migrations.CreateModel(
            name='ContentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.SmallIntegerField(choices=[(1, '问答'), (2, '知识分享'), (3, '资源分享')], default=1, verbose_name='内容分类')),
                ('description', models.CharField(blank=True, max_length=256, verbose_name='分类描述')),
            ],
            options={
                'verbose_name_plural': '内容分类',
            },
        ),
        
        # Create Post model
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('postId', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='帖子ID')),
                ('title', models.CharField(max_length=256, verbose_name='标题')),
                ('content', models.TextField(verbose_name='内容')),
                ('tags', models.CharField(blank=True, help_text='多个标签用逗号分隔', max_length=512, verbose_name='标签')),
                ('isAnonymous', models.BooleanField(default=False, verbose_name='是否匿名')),
                ('createdAt', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updatedAt', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('likeCount', models.IntegerField(default=0, verbose_name='点赞数')),
                ('collectCount', models.IntegerField(default=0, verbose_name='收藏数')),
                ('commentCount', models.IntegerField(default=0, verbose_name='评论数')),
                ('viewCount', models.IntegerField(default=0, verbose_name='浏览数')),
                ('heatScore', models.FloatField(db_index=True, default=0.0, verbose_name='热度分数')),
                ('embedding', models.BinaryField(blank=True, help_text='768维向量，用于智能推荐和语义搜索', null=True, verbose_name='内容嵌入向量')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_posts', to='baweb.User', verbose_name='作者')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='baweb.ContentCategory', verbose_name='内容分类')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_posts', to='baweb.Course', verbose_name='所属课程')),
            ],
            options={
                'ordering': ['-heatScore', '-createdAt'],
            },
        ),
        
        # Create indexes for Post model
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['course', '-heatScore'], name='baweb_post_course_heat_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['-createdAt'], name='baweb_post_created_idx'),
        ),
        migrations.AddIndex(
            model_name='post',
            index=models.Index(fields=['author'], name='baweb_post_author_idx'),
        ),
        
        # Create PostLike model
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdAt', models.DateTimeField(auto_now_add=True, verbose_name='点赞时间')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='baweb.Post', verbose_name='帖子')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='baweb.User', verbose_name='点赞用户')),
            ],
            options={
                'verbose_name_plural': '帖子点赞',
                'unique_together': {('post', 'user')},
            },
        ),
        
        # Create PostCollect model
        migrations.CreateModel(
            name='PostCollect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('createdAt', models.DateTimeField(auto_now_add=True, verbose_name='收藏时间')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collects', to='baweb.Post', verbose_name='帖子')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collected_posts', to='baweb.User', verbose_name='收藏用户')),
            ],
            options={
                'verbose_name_plural': '帖子收藏',
                'unique_together': {('post', 'user')},
            },
        ),
        
        # Create PostComment model
        migrations.CreateModel(
            name='PostComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('commentId', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='评论ID')),
                ('content', models.TextField(verbose_name='评论内容')),
                ('isAnonymous', models.BooleanField(default=False, verbose_name='是否匿名')),
                ('createdAt', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updatedAt', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('likeCount', models.IntegerField(default=0, verbose_name='点赞数')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_comments', to='baweb.User', verbose_name='评论者')),
                ('parentComment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='baweb.PostComment', verbose_name='父评论')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_comments', to='baweb.Post', verbose_name='所属帖子')),
            ],
            options={
                'ordering': ['-createdAt'],
            },
        ),
        
        # Create indexes for PostComment model
        migrations.AddIndex(
            model_name='postcomment',
            index=models.Index(fields=['post', '-createdAt'], name='baweb_postcomment_post_idx'),
        ),
        migrations.AddIndex(
            model_name='postcomment',
            index=models.Index(fields=['author'], name='baweb_postcomment_author_idx'),
        ),
    ]
