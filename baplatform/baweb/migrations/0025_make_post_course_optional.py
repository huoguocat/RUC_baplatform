# Generated manually to make Post.course field optional

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('baweb', '0024_auto_20251204_0928'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='course',
            field=models.ForeignKey(blank=True, help_text='可以为空，表示不属于任何课程的帖子', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_posts', to='baweb.Course', verbose_name='所属课程'),
        ),
    ]

