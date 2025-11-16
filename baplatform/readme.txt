1.班级同学账号已录入，账号密码均为学号
2.该项目为上一年级信息系统分析与设计课程的学生所完成，有一些bug；
3.环境为python3.7，所需额外的包库已在requirements.txt中;
4.运行后项目需在http协议下打开，请用http:头打开,可尝试让其支持https协议；（打不开可尝试更换浏览器打开）

sqlite3 db.sqlite3
-- 查看所有表
.tables

-- 查看表结构
.schema 表名


# 生成迁移（仅在修改 models 时需要）
python manage.py makemigrations

# 应用迁移
python manage.py migrate

创建管理员账号（用于访问 Django admin）：
python manage.py createsuperuser

# 在 baplatform 目录
python manage.py runserver 0.0.0.0:8000
http://127.0.0.1:8000/