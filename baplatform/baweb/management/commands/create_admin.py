"""
Django management command to create admin user
"""
from django.core.management.base import BaseCommand
from baweb.models import User
from baweb.utils.encrypt import md5


class Command(BaseCommand):
    help = '创建管理员账号'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='管理员用户名')
        parser.add_argument('--password', type=str, help='管理员密码')

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')
        
        # 如果没有提供参数，交互式输入
        if not username:
            username = input('请输入管理员用户名: ').strip()
        
        if not password:
            password = input('请输入管理员密码: ').strip()
        
        if not username or not password:
            self.stdout.write(self.style.ERROR('用户名和密码不能为空'))
            return
        
        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'用户名 "{username}" 已存在'))
            return
        
        # 创建管理员账号（使用系统的md5加密方式）
        encrypted_password = md5(password)
        
        admin = User.objects.create(
            username=username,
            password=encrypted_password,
            type=3,  # 管理员类型
            points=100
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ 管理员账号创建成功！'))
        self.stdout.write(f'  用户名: {username}')
        self.stdout.write(f'  ID: {admin.id}')
        self.stdout.write(f'  类型: {admin.get_type_display()}')
        self.stdout.write(f'  初始积分: {admin.points}')
        self.stdout.write(f'\n登录地址: http://127.0.0.1:8000/login/')
