"""
Activity 5: 用户交互跟踪服务
实现浏览/点赞/评论/收藏跟踪，用户画像更新，帖子指标更新
"""

from typing import Optional, Dict, List
from django.utils import timezone
from django.db import transaction
import json

from ..models import User, Post, PostLike, PostCollect, PostComment, PostView
from .embedding_utils import EmbeddingUtils, update_user_vector
from .ranking_service import RankingService


class InteractionType:
    """交互类型枚举"""
    VIEW = 'view'
    LIKE = 'like'
    COMMENT = 'comment'
    COLLECT = 'collect'
    
    # 交互分数
    SCORES = {
        VIEW: 1,
        LIKE: 2,
        COMMENT: 3,
        COLLECT: 4
    }


class InteractionTracker:
    """用户交互跟踪服务类"""
    
    @staticmethod
    @transaction.atomic
    def track_view(user: User, post: Post) -> bool:
        """
        记录浏览行为
        
        Args:
            user: 用户对象
            post: 帖子对象
            
        Returns:
            是否成功
        """
        # 增加浏览数
        post.viewCount += 1
        post.save(update_fields=['viewCount'])
        
        # 记录浏览历史（如果有PostView模型）
        try:
            from ..models import PostView
            PostView.objects.get_or_create(
                user=user,
                post=post,
                defaults={'viewedAt': timezone.now()}
            )
        except:
            pass
        
        # 更新用户交互历史
        InteractionTracker.update_user_interaction_history(
            user, 
            post, 
            InteractionType.VIEW
        )
        
        # 异步更新热度分数
        InteractionTracker.update_post_heat_score(post)
        
        return True
    
    @staticmethod
    @transaction.atomic
    def track_like(user: User, post: Post) -> Dict[str, any]:
        """
        记录点赞行为
        
        Args:
            user: 用户对象
            post: 帖子对象
            
        Returns:
            结果字典 {'success': bool, 'message': str, 'is_liked': bool}
        """
        # 检查是否已点赞
        like_obj, created = PostLike.objects.get_or_create(
            user=user,
            post=post
        )
        
        if not created:
            # 已点赞，执行取消点赞
            like_obj.delete()
            post.likeCount = max(0, post.likeCount - 1)
            post.save(update_fields=['likeCount'])
            
            # 从用户交互历史中移除
            InteractionTracker.remove_from_interaction_history(user, post)
            
            return {
                'success': True,
                'message': '取消点赞成功',
                'is_liked': False
            }
        else:
            # 新点赞
            post.likeCount += 1
            post.save(update_fields=['likeCount'])
            
            # 更新用户交互历史
            InteractionTracker.update_user_interaction_history(
                user,
                post,
                InteractionType.LIKE
            )
            
            # 给帖子作者加积分
            if post.author.id != user.id:  # 不能给自己加分
                post.author.points += 1
                post.author.save(update_fields=['points'])
            
            # 更新热度分数
            InteractionTracker.update_post_heat_score(post)
            
            return {
                'success': True,
                'message': '点赞成功',
                'is_liked': True
            }
    
    @staticmethod
    @transaction.atomic
    def track_comment(user: User, post: Post, comment: PostComment) -> bool:
        """
        记录评论行为
        
        Args:
            user: 用户对象
            post: 帖子对象
            comment: 评论对象
            
        Returns:
            是否成功
        """
        # 增加评论数
        post.commentCount += 1
        post.save(update_fields=['commentCount'])
        
        # 更新用户交互历史
        InteractionTracker.update_user_interaction_history(
            user,
            post,
            InteractionType.COMMENT
        )
        
        # 给帖子作者加积分
        if post.author.id != user.id:
            post.author.points += 2
            post.author.save(update_fields=['points'])
        
        # 更新热度分数
        InteractionTracker.update_post_heat_score(post)
        
        # TODO: 通知帖子作者（可选）
        
        return True
    
    @staticmethod
    @transaction.atomic
    def track_collect(user: User, post: Post) -> Dict[str, any]:
        """
        记录收藏行为
        
        Args:
            user: 用户对象
            post: 帖子对象
            
        Returns:
            结果字典 {'success': bool, 'message': str, 'is_collected': bool}
        """
        # 检查是否已收藏
        collect_obj, created = PostCollect.objects.get_or_create(
            user=user,
            post=post
        )
        
        if not created:
            # 已收藏，执行取消收藏
            collect_obj.delete()
            post.collectCount = max(0, post.collectCount - 1)
            post.save(update_fields=['collectCount'])
            
            # 从用户交互历史中移除
            InteractionTracker.remove_from_interaction_history(user, post)
            
            return {
                'success': True,
                'message': '取消收藏成功',
                'is_collected': False
            }
        else:
            # 新收藏
            post.collectCount += 1
            post.save(update_fields=['collectCount'])
            
            # 更新用户交互历史
            InteractionTracker.update_user_interaction_history(
                user,
                post,
                InteractionType.COLLECT
            )
            
            # 给帖子作者加积分
            if post.author.id != user.id:
                post.author.points += 3
                post.author.save(update_fields=['points'])
            
            # 更新热度分数
            InteractionTracker.update_post_heat_score(post)
            
            return {
                'success': True,
                'message': '收藏成功',
                'is_collected': True
            }
    
    @staticmethod
    def update_user_interaction_history(user: User, 
                                       post: Post, 
                                       interaction_type: str) -> bool:
        """
        更新用户交互历史
        
        Args:
            user: 用户对象
            post: 帖子对象
            interaction_type: 交互类型
            
        Returns:
            是否成功
        """
        # 解析现有交互历史
        interaction_history = {}
        if hasattr(user, 'interactionHistory') and user.interactionHistory:
            try:
                interaction_history = json.loads(user.interactionHistory)
            except:
                pass
        
        # 更新交互分数
        post_id_str = str(post.id)
        current_score = interaction_history.get(post_id_str, 0)
        interaction_score = InteractionType.SCORES.get(interaction_type, 0)
        
        # 累加分数（但设置上限）
        new_score = min(current_score + interaction_score, 10)
        interaction_history[post_id_str] = new_score
        
        # 保存交互历史
        if hasattr(user, 'interactionHistory'):
            user.interactionHistory = json.dumps(interaction_history)
        
        # 更新分类偏好
        if post.category_id:
            InteractionTracker.update_category_preference(user, post.category_id, interaction_score)
        
        # 重新计算用户向量
        InteractionTracker.recalculate_user_vector(user)
        
        # 保存用户
        save_fields = []
        if hasattr(user, 'interactionHistory'):
            save_fields.append('interactionHistory')
        if hasattr(user, 'preferredCategories'):
            save_fields.append('preferredCategories')
        if hasattr(user, 'userVector'):
            save_fields.append('userVector')
        
        if save_fields:
            user.save(update_fields=save_fields)
        
        return True
    
    @staticmethod
    def remove_from_interaction_history(user: User, post: Post) -> bool:
        """
        从用户交互历史中移除帖子
        
        Args:
            user: 用户对象
            post: 帖子对象
            
        Returns:
            是否成功
        """
        if not hasattr(user, 'interactionHistory') or not user.interactionHistory:
            return False
        
        try:
            interaction_history = json.loads(user.interactionHistory)
            post_id_str = str(post.id)
            
            if post_id_str in interaction_history:
                del interaction_history[post_id_str]
                user.interactionHistory = json.dumps(interaction_history)
                
                # 重新计算用户向量
                InteractionTracker.recalculate_user_vector(user)
                
                user.save(update_fields=['interactionHistory', 'userVector'])
                return True
        except:
            pass
        
        return False
    
    @staticmethod
    def update_category_preference(user: User, category_id: int, score_delta: int) -> bool:
        """
        更新用户分类偏好
        
        Args:
            user: 用户对象
            category_id: 分类ID
            score_delta: 分数变化
            
        Returns:
            是否成功
        """
        if not hasattr(user, 'preferredCategories'):
            return False
        
        # 解析现有偏好
        preferences = {}
        if user.preferredCategories:
            try:
                preferences = json.loads(user.preferredCategories)
            except:
                pass
        
        # 更新偏好分数
        category_id_str = str(category_id)
        current_score = preferences.get(category_id_str, 0)
        new_score = min(current_score + score_delta, 10)
        preferences[category_id_str] = new_score
        
        # 保存
        user.preferredCategories = json.dumps(preferences)
        
        return True
    
    @staticmethod
    def recalculate_user_vector(user: User) -> bool:
        """
        重新计算用户向量
        
        基于用户交互过的帖子的embedding计算加权平均
        
        Args:
            user: 用户对象
            
        Returns:
            是否成功
        """
        if not hasattr(user, 'interactionHistory') or not user.interactionHistory:
            return False
        
        try:
            interaction_history = json.loads(user.interactionHistory)
        except:
            return False
        
        # 获取交互过的帖子
        post_ids = [int(pid) for pid in interaction_history.keys()]
        posts = Post.objects.filter(id__in=post_ids).exclude(embedding__isnull=True)
        
        # 收集向量和权重
        interaction_posts = []
        interaction_scores = []
        
        for post in posts:
            post_id_str = str(post.id)
            score = interaction_history.get(post_id_str, 0)
            if score > 0:
                interaction_posts.append(post)
                interaction_scores.append(score)
        
        if not interaction_posts:
            return False
        
        # 计算用户向量
        if hasattr(user, 'userVector'):
            user_vector_bytes = update_user_vector(user, interaction_posts, interaction_scores)
            user.userVector = user_vector_bytes
            return True
        
        return False
    
    @staticmethod
    def update_post_heat_score(post: Post) -> bool:
        """
        更新帖子热度分数
        
        Args:
            post: 帖子对象
            
        Returns:
            是否成功
        """
        old_score = post.heatScore
        new_score = RankingService.calculate_heat_score(post)
        
        # 只有变化显著才更新
        if abs(new_score - old_score) > 0.1:
            post.heatScore = new_score
            post.save(update_fields=['heatScore'])
            return True
        
        return False
    
    @staticmethod
    def get_user_statistics(user: User) -> Dict:
        """
        获取用户交互统计
        
        Args:
            user: 用户对象
            
        Returns:
            统计字典
        """
        stats = {
            'total_posts': Post.objects.filter(author=user).count(),
            'total_likes': PostLike.objects.filter(user=user).count(),
            'total_collects': PostCollect.objects.filter(user=user).count(),
            'total_comments': PostComment.objects.filter(author=user).count(),
            'received_likes': PostLike.objects.filter(post__author=user).count(),
            'received_comments': PostComment.objects.filter(post__author=user).count(),
            'points': user.points
        }
        
        # 交互历史统计
        if hasattr(user, 'interactionHistory') and user.interactionHistory:
            try:
                interaction_history = json.loads(user.interactionHistory)
                stats['interaction_count'] = len(interaction_history)
                stats['total_interaction_score'] = sum(interaction_history.values())
            except:
                stats['interaction_count'] = 0
                stats['total_interaction_score'] = 0
        else:
            stats['interaction_count'] = 0
            stats['total_interaction_score'] = 0
        
        # 分类偏好统计
        if hasattr(user, 'preferredCategories') and user.preferredCategories:
            try:
                preferences = json.loads(user.preferredCategories)
                stats['preferred_category_count'] = len(preferences)
            except:
                stats['preferred_category_count'] = 0
        else:
            stats['preferred_category_count'] = 0
        
        return stats
