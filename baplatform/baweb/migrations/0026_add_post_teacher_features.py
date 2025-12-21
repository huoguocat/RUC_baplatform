# Generated migration for adding teacher features to posts

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baweb', '0025_make_post_course_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='isPinned',
            field=models.BooleanField(default=False, verbose_name='是否置顶', help_text='教师可以置顶课程内的帖子'),
        ),
        migrations.AddField(
            model_name='post',
            name='pinnedAt',
            field=models.DateTimeField(verbose_name='置顶时间', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='post',
            name='isDeletedByTeacher',
            field=models.BooleanField(default=False, verbose_name='是否被教师删除', help_text='教师可以删除课程内的帖子'),
        ),
    ]
