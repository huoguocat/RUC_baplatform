"""
更新用户个性化推荐分数的定时任务命令

使用方法：
python manage.py update_heat_scores

建议每小时运行一次：
- Windows: 使用任务计划程序设置
- Linux: 使用crontab: 0 * * * * cd /path/to/project && python manage.py update_heat_scores

功能：
1. 更新所有帖子的基础热度分数
2. 为每个活跃用户计算个性化推荐分数并缓存
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from baweb.models import Post, User, PersonalizedPostScore
from baweb.utils.ranking_service import RankingService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '更新帖子热度分数和用户个性化推荐分数（建议每小时运行一次）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all-posts',
            action='store_true',
            help='更新所有帖子（包括很旧的），默认只更新30天内的帖子',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='更新多少天内的帖子（默认30天）',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='批处理大小（默认100）',
        )
        parser.add_argument(
            '--active-days',
            type=int,
            default=30,
            help='只为最近N天内活跃的用户计算个性化分数（默认30天）',
        )
        parser.add_argument(
            '--personalization-weight',
            type=float,
            default=0.3,
            help='个性化权重（0-1，默认0.3）',
        )
        parser.add_argument(
            '--skip-personalized',
            action='store_true',
            help='跳过个性化分数计算，只更新基础热度',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('开始更新推荐系统分数'))
        self.stdout.write(f'时间: {start_time}')
        self.stdout.write('=' * 70)
        
        # ===== 第一步：更新帖子基础热度分数 =====
        self.stdout.write('\n[步骤 1/2] 更新帖子基础热度分数...')
        heat_updated = self._update_heat_scores(options)
        
        # ===== 第二步：计算用户个性化分数 =====
        if not options['skip_personalized']:
            self.stdout.write('\n[步骤 2/2] 计算用户个性化推荐分数...')
            personalized_updated = self._update_personalized_scores(options)
        else:
            self.stdout.write('\n[步骤 2/2] 跳过个性化分数计算')
            personalized_updated = 0
        
        # ===== 完成总结 =====
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('✓ 全部更新完成！'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'基础热度更新: {heat_updated} 篇帖子')
        self.stdout.write(f'个性化分数缓存: {personalized_updated} 条记录')
        self.stdout.write(f'总用时: {duration:.2f} 秒')
        self.stdout.write(f'完成时间: {end_time}')
        self.stdout.write('=' * 70)
        
        # 记录日志
        logger.info(
            f'Recommendation score update completed: '
            f'heat_updated={heat_updated}, personalized_updated={personalized_updated}, '
            f'duration={duration:.2f}s'
        )
    
    def _update_heat_scores(self, options):
        """更新帖子基础热度分数"""
        # 获取需要更新的帖子
        posts_query = Post.objects.filter(isDeletedByTeacher=False)
        
        if not options['all_posts']:
            # 默认只更新最近N天的帖子
            days = options['days']
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            posts_query = posts_query.filter(createdAt__gte=cutoff_date)
        
        total_posts = posts_query.count()
        self.stdout.write(f'  找到 {total_posts} 篇帖子需要更新热度')
        
        if total_posts == 0:
            return 0
        
        # 分批处理
        batch_size = options['batch_size']
        updated_count = 0
        processed_count = 0
        
        posts = list(posts_query.select_related('author', 'course', 'category'))
        
        for i in range(0, len(posts), batch_size):
            batch = posts[i:i + batch_size]
            batch_updated = RankingService.batch_update_heat_scores(batch)
            updated_count += batch_updated
            processed_count += len(batch)
            
            progress = (processed_count / total_posts) * 100
            self.stdout.write(
                f'  进度: {processed_count}/{total_posts} ({progress:.1f}%) - '
                f'本批次更新: {batch_updated}/{len(batch)}'
            )
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ 热度分数更新完成: {updated_count}/{processed_count}'))
        return updated_count
    
    def _update_personalized_scores(self, options):
        """为活跃用户计算并缓存个性化推荐分数"""
        from datetime import timedelta
        
        # 获取活跃用户（最近N天内有交互的用户）
        active_days = options['active_days']
        cutoff_date = timezone.now() - timedelta(days=active_days)
        
        # 获取最近有互动的用户（点赞、评论、收藏、浏览）
        from baweb.models import PostLike, PostComment, PostCollect, PostView
        
        active_user_ids = set()
        active_user_ids.update(
            PostLike.objects.filter(createdAt__gte=cutoff_date)
            .values_list('user_id', flat=True).distinct()
        )
        active_user_ids.update(
            PostComment.objects.filter(createdAt__gte=cutoff_date)
            .values_list('author_id', flat=True).distinct()
        )
        active_user_ids.update(
            PostCollect.objects.filter(createdAt__gte=cutoff_date)
            .values_list('user_id', flat=True).distinct()
        )
        active_user_ids.update(
            PostView.objects.filter(viewedAt__gte=cutoff_date)
            .values_list('user_id', flat=True).distinct()
        )
        
        active_users = User.objects.filter(id__in=active_user_ids)
        user_count = active_users.count()
        
        self.stdout.write(f'  找到 {user_count} 个活跃用户需要计算个性化分数')
        
        if user_count == 0:
            return 0
        
        # 获取需要推荐的帖子（最近的帖子）
        post_days = options['days']
        post_cutoff = timezone.now() - timedelta(days=post_days)
        posts = Post.objects.filter(
            createdAt__gte=post_cutoff,
            isDeletedByTeacher=False
        ).select_related('author', 'course', 'category')
        
        post_count = posts.count()
        self.stdout.write(f'  针对 {post_count} 篇最近帖子计算个性化分数')
        
        if post_count == 0:
            return 0
        
        personalization_weight = options['personalization_weight']
        total_updated = 0
        processed_users = 0
        
        # 为每个用户计算个性化分数
        for user in active_users:
            user_profile = RankingService.get_user_profile(user)
            user_updated = 0
            
            # 批量处理该用户的所有帖子
            score_records = []
            for post in posts:
                # 计算个性化分数
                personalized_score = RankingService.calculate_personalized_score(
                    post, user_profile
                )
                heat_score = post.heatScore
                final_score = (
                    heat_score * (1 - personalization_weight) +
                    personalized_score * 100 * personalization_weight
                )
                
                # 准备批量创建/更新
                score_records.append({
                    'user': user,
                    'post': post,
                    'personalizedScore': personalized_score,
                    'heatScore': heat_score,
                    'finalScore': final_score,
                })
            
            # 批量更新数据库
            with transaction.atomic():
                for record in score_records:
                    obj, created = PersonalizedPostScore.objects.update_or_create(
                        user=record['user'],
                        post=record['post'],
                        defaults={
                            'personalizedScore': record['personalizedScore'],
                            'heatScore': record['heatScore'],
                            'finalScore': record['finalScore'],
                        }
                    )
                    user_updated += 1
            
            total_updated += user_updated
            processed_users += 1
            
            # 显示进度
            progress = (processed_users / user_count) * 100
            self.stdout.write(
                f'  进度: {processed_users}/{user_count} ({progress:.1f}%) - '
                f'{user.username}: {user_updated} 条记录'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  ✓ 个性化分数计算完成: {total_updated} 条记录 '
                f'({user_count} 个用户 × {post_count} 篇帖子)'
            )
        )
        return total_updated
