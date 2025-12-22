"""
Activity 3: 帖子排名和评分服务
实现热度计算、个性化推荐、帖子重排序
"""

from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from datetime import timedelta
import math
import json

from ..models import Post, User, PostLike, PostCollect, PostComment
from .embedding_utils import EmbeddingUtils


class RankingService:
    """帖子排名服务类"""
    
    # 权重配置
    ENGAGEMENT_WEIGHT = 0.4  # 互动权重
    FRESHNESS_WEIGHT = 0.3   # 新鲜度权重
    POPULARITY_WEIGHT = 0.3  # 流行度权重
    
    # 互动分数权重
    LIKE_SCORE = 1.0
    COMMENT_SCORE = 2.0
    COLLECT_SCORE = 3.0
    
    @staticmethod
    def calculate_engagement_score(post: Post) -> float:
        """
        计算互动得分
        
        Args:
            post: 帖子对象
            
        Returns:
            互动得分
        """
        engagement = (
            post.likeCount * RankingService.LIKE_SCORE +
            post.commentCount * RankingService.COMMENT_SCORE +
            post.collectCount * RankingService.COLLECT_SCORE
        )
        return engagement
    
    @staticmethod
    def calculate_freshness_score(post: Post) -> float:
        """
        计算新鲜度得分（时间衰减）
        
        Args:
            post: 帖子对象
            
        Returns:
            新鲜度得分 (0-100)
        """
        return post.calculateFreshness()
    
    @staticmethod
    def calculate_view_popularity(post: Post) -> float:
        """
        计算浏览流行度（归一化浏览数）
        
        Args:
            post: 帖子对象
            
        Returns:
            流行度得分
        """
        # 使用对数归一化，避免极端值
        if post.viewCount == 0:
            return 0
        return math.log(post.viewCount + 1)
    
    @staticmethod
    def calculate_time_decay(post: Post) -> float:
        """
        计算时间衰减因子
        
        Args:
            post: 帖子对象
            
        Returns:
            衰减因子 (0-1)
        """
        time_diff = timezone.now() - post.createdAt
        days = time_diff.days + 1
        
        # 使用指数衰减：decay = exp(-lambda * days)
        # lambda = 0.1 表示大约10天后衰减到原来的37%
        decay = math.exp(-0.1 * days)
        return decay
    
    @staticmethod
    def calculate_heat_score(post: Post) -> float:
        """
        计算综合热度分数
        
        热度算法：
        - 互动得分 × 时间衰减 × 40%
        - 新鲜度得分 × 30%
        - 浏览流行度 × 30%
        
        Args:
            post: 帖子对象
            
        Returns:
            热度分数
        """
        engagement = RankingService.calculate_engagement_score(post)
        freshness = RankingService.calculate_freshness_score(post)
        popularity = RankingService.calculate_view_popularity(post)
        time_decay = RankingService.calculate_time_decay(post)
        
        # 综合计算
        heat_score = (
            engagement * time_decay * RankingService.ENGAGEMENT_WEIGHT +
            freshness * RankingService.FRESHNESS_WEIGHT +
            popularity * RankingService.POPULARITY_WEIGHT
        )
        
        return max(0, heat_score)
    
    @staticmethod
    def batch_update_heat_scores(posts: List[Post]) -> int:
        """
        批量更新帖子热度分数
        
        Args:
            posts: 帖子列表
            
        Returns:
            更新的帖子数量
        """
        updated_count = 0
        
        for post in posts:
            old_score = post.heatScore
            new_score = RankingService.calculate_heat_score(post)
            
            # 只有变化超过0.1才更新（避免频繁更新数据库）
            if abs(new_score - old_score) > 0.1:
                post.heatScore = new_score
                post.save(update_fields=['heatScore'])
                updated_count += 1
        
        return updated_count
    
    @staticmethod
    def get_user_profile(user: User) -> Dict:
        """
        获取用户画像
        
        Args:
            user: 用户对象
            
        Returns:
            用户画像字典
        """
        profile = {
            'user_vector': None,
            'interaction_history': {},
            'preferred_categories': {}
        }
        
        # 解析用户向量
        if hasattr(user, 'userVector') and user.userVector:
            profile['user_vector'] = EmbeddingUtils.decode_vector(user.userVector)
        
        # 解析交互历史
        if hasattr(user, 'interactionHistory') and user.interactionHistory:
            try:
                profile['interaction_history'] = json.loads(user.interactionHistory)
            except:
                pass
        
        # 解析分类偏好
        if hasattr(user, 'preferredCategories') and user.preferredCategories:
            try:
                profile['preferred_categories'] = json.loads(user.preferredCategories)
            except:
                pass
        
        return profile
    
    @staticmethod
    def calculate_personalized_score(post: Post, user_profile: Dict) -> float:
        """
        计算个性化相关度分数
        
        Args:
            post: 帖子对象
            user_profile: 用户画像字典
            
        Returns:
            个性化分数 (0-1)
        """
        score = 0.0
        
        # 1. 向量相似度 (50%)
        user_vector = user_profile.get('user_vector')
        if user_vector is not None and post.embedding:
            post_vector = EmbeddingUtils.decode_vector(post.embedding)
            if post_vector is not None:
                similarity = EmbeddingUtils.cosine_similarity(user_vector, post_vector)
                score += similarity * 0.5
        
        # 2. 交互历史 (30%)
        interaction_history = user_profile.get('interaction_history', {})
        post_id_str = str(post.id)
        if post_id_str in interaction_history:
            # 已交互过的帖子，根据交互分数给予权重
            interaction_score = interaction_history[post_id_str]
            # 归一化到0-1
            normalized_score = min(1.0, interaction_score / 10.0)
            score += normalized_score * 0.3
        
        # 3. 分类偏好 (20%)
        preferred_categories = user_profile.get('preferred_categories', {})
        if post.category_id:
            category_id_str = str(post.category_id)
            if category_id_str in preferred_categories:
                # 分类偏好分数
                preference_score = preferred_categories[category_id_str]
                # 归一化到0-1
                normalized_score = min(1.0, preference_score / 10.0)
                score += normalized_score * 0.2
        
        return min(1.0, score)
    
    @staticmethod
    def personalized_ranking(posts: List[Post], 
                           user: Optional[User] = None,
                           personalization_weight: float = 0.3,
                           respect_pinned: bool = True) -> List[Post]:
        """
        个性化排名
        
        综合考虑：
        - 基础热度分数 (70%)
        - 个性化相关度 (30%)
        
        Args:
            posts: 帖子列表
            user: 用户对象（None表示非个性化）
            personalization_weight: 个性化权重
            respect_pinned: 是否尊重置顶状态
            
        Returns:
            排序后的帖子列表
        """
        if not user:
            # 非个性化，直接按热度排序
            if respect_pinned:
                return sorted(posts, key=lambda p: (-p.isPinned, -p.heatScore))
            else:
                return sorted(posts, key=lambda p: -p.heatScore)
        
        # 获取用户画像
        user_profile = RankingService.get_user_profile(user)
        
        # 计算最终分数
        scored_posts = []
        for post in posts:
            heat_score = post.heatScore
            personalized_score = RankingService.calculate_personalized_score(post, user_profile)
            
            # 综合分数
            final_score = (
                heat_score * (1 - personalization_weight) +
                personalized_score * 100 * personalization_weight  # 乘100使其与heat_score量级一致
            )
            
            scored_posts.append((post, final_score))
        
        # 排序：是否置顶优先，然后按最终分数
        if respect_pinned:
            scored_posts.sort(key=lambda x: (-x[0].isPinned, -x[1]))
        else:
            scored_posts.sort(key=lambda x: -x[1])
        
        return [post for post, score in scored_posts]
    
    @staticmethod
    def rank_posts(posts: List[Post],
                  user: Optional[User] = None,
                  sort_by: str = 'heat',
                  enable_personalization: bool = True,
                  respect_pinned: bool = True) -> List[Post]:
        """
        对帖子列表进行排名
        
        Args:
            posts: 帖子列表
            user: 用户对象
            sort_by: 排序方式 ('heat', 'newest', 'bounty', 'personalized')
            enable_personalization: 是否启用个性化
            respect_pinned: 是否尊重置顶状态（False时忽略isPinned字段）
            
        Returns:
            排序后的帖子列表
        """
        if sort_by == 'newest':
            # 按时间排序
            if respect_pinned:
                return sorted(posts, key=lambda p: (-p.isPinned, -p.createdAt.timestamp()))
            else:
                return sorted(posts, key=lambda p: -p.createdAt.timestamp())
        
        elif sort_by == 'bounty':
            # 按悬赏积分排序
            if respect_pinned:
                return sorted(posts, key=lambda p: (-p.isPinned, -p.bountyPoints, -p.createdAt.timestamp()))
            else:
                return sorted(posts, key=lambda p: (-p.bountyPoints, -p.createdAt.timestamp()))
        
        elif sort_by == 'personalized':
            # 纯个性化排序（必须有用户）
            if user:
                return RankingService.personalized_ranking(posts, user, respect_pinned=respect_pinned)
            else:
                # 无用户时降级为热度排序
                if respect_pinned:
                    return sorted(posts, key=lambda p: (-p.isPinned, -p.heatScore))
                else:
                    return sorted(posts, key=lambda p: -p.heatScore)
        
        else:  # 'heat' or default
            # 按热度排序（支持个性化）
            if enable_personalization and user:
                return RankingService.personalized_ranking(posts, user, respect_pinned=respect_pinned)
            else:
                if respect_pinned:
                    return sorted(posts, key=lambda p: (-p.isPinned, -p.heatScore))
                else:
                    return sorted(posts, key=lambda p: -p.heatScore)
    
    @staticmethod
    def get_trending_posts(time_window_days: int = 7, limit: int = 10) -> List[Post]:
        """
        获取热门趋势帖子
        
        Args:
            time_window_days: 时间窗口（天）
            limit: 返回数量
            
        Returns:
            趋势帖子列表
        """
        # 计算时间窗口
        start_time = timezone.now() - timedelta(days=time_window_days)
        
        # 获取时间窗口内的帖子
        posts = Post.objects.filter(
            createdAt__gte=start_time,
            isDeletedByTeacher=False
        ).order_by('-heatScore')[:limit]
        
        return list(posts)
