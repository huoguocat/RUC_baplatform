"""
Activity 4: 内容推荐服务
实现相似帖子发现、热门标签、协同过滤推荐
"""

from typing import List, Dict, Optional, Tuple
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from collections import Counter

from ..models import Post, User, PostLike, PostCollect, PostComment
from .embedding_utils import EmbeddingUtils
from .ranking_service import RankingService


class RecommendationService:
    """内容推荐服务类"""
    
    @staticmethod
    def find_similar_posts(current_post: Post, 
                          limit: int = 10,
                          exclude_viewed: Optional[List[int]] = None) -> List[Tuple[Post, float]]:
        """
        发现相似帖子（基于向量相似度）
        
        Args:
            current_post: 当前帖子
            limit: 返回数量
            exclude_viewed: 要排除的帖子ID列表（已浏览）
            
        Returns:
            (帖子, 相似度)列表
        """
        if not current_post.embedding:
            return []
        
        # 解码当前帖子向量
        current_vector = EmbeddingUtils.decode_vector(current_post.embedding)
        if current_vector is None:
            return []
        
        # 获取候选帖子（排除当前帖子和已浏览帖子）
        exclude_ids = [current_post.id]
        if exclude_viewed:
            exclude_ids.extend(exclude_viewed)
        
        candidates = Post.objects.filter(
            isDeletedByTeacher=False
        ).exclude(
            id__in=exclude_ids
        ).exclude(
            embedding__isnull=True
        ).select_related('author', 'category', 'course')
        
        # 计算相似度
        similarities = []
        for post in candidates:
            post_vector = EmbeddingUtils.decode_vector(post.embedding)
            if post_vector is not None:
                similarity = EmbeddingUtils.cosine_similarity(current_vector, post_vector)
                similarities.append((post, similarity))
        
        # 排序并返回top K
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    @staticmethod
    def get_trending_tags(time_window_days: int = 7, limit: int = 10) -> List[Dict]:
        """
        获取热门标签
        
        Args:
            time_window_days: 时间窗口（天）
            limit: 返回数量
            
        Returns:
            标签字典列表 [{'tag': '标签名', 'count': 出现次数, 'trend_score': 趋势分数}]
        """
        # 计算时间窗口
        start_time = timezone.now() - timedelta(days=time_window_days)
        
        # 获取时间窗口内的帖子
        recent_posts = Post.objects.filter(
            createdAt__gte=start_time,
            isDeletedByTeacher=False
        ).exclude(tags__isnull=True).exclude(tags='')
        
        # 统计标签出现次数
        tag_counter = Counter()
        tag_heat_scores = {}
        
        for post in recent_posts:
            tags = [tag.strip() for tag in post.tags.split(',') if tag.strip()]
            for tag in tags:
                tag_counter[tag] += 1
                # 累加帖子热度到标签
                if tag in tag_heat_scores:
                    tag_heat_scores[tag] += post.heatScore
                else:
                    tag_heat_scores[tag] = post.heatScore
        
        # 计算趋势分数：出现次数 × 平均热度
        trending_tags = []
        for tag, count in tag_counter.items():
            avg_heat = tag_heat_scores[tag] / count if count > 0 else 0
            trend_score = count * avg_heat
            trending_tags.append({
                'tag': tag,
                'count': count,
                'avg_heat': avg_heat,
                'trend_score': trend_score
            })
        
        # 按趋势分数排序
        trending_tags.sort(key=lambda x: x['trend_score'], reverse=True)
        return trending_tags[:limit]
    
    @staticmethod
    def get_posts_by_trending_tags(tag_names: List[str], limit: int = 20) -> List[Post]:
        """
        根据热门标签获取帖子
        
        Args:
            tag_names: 标签名列表
            limit: 返回数量
            
        Returns:
            帖子列表
        """
        if not tag_names:
            return []
        
        # 构建查询
        tag_query = Q()
        for tag in tag_names:
            tag_query |= Q(tags__icontains=tag)
        
        posts = Post.objects.filter(
            tag_query,
            isDeletedByTeacher=False
        ).select_related(
            'author', 'category', 'course'
        ).order_by('-heatScore')[:limit]
        
        return list(posts)
    
    @staticmethod
    def find_similar_users(user: User, limit: int = 10) -> List[Tuple[User, float]]:
        """
        找到相似用户（基于用户向量）
        
        Args:
            user: 当前用户
            limit: 返回数量
            
        Returns:
            (用户, 相似度)列表
        """
        if not hasattr(user, 'userVector') or not user.userVector:
            return []
        
        user_vector = EmbeddingUtils.decode_vector(user.userVector)
        if user_vector is None:
            return []
        
        # 获取其他有向量的用户
        other_users = User.objects.exclude(id=user.id)
        
        similarities = []
        for other_user in other_users:
            if not hasattr(other_user, 'userVector') or not other_user.userVector:
                continue
            
            other_vector = EmbeddingUtils.decode_vector(other_user.userVector)
            if other_vector is not None:
                similarity = EmbeddingUtils.cosine_similarity(user_vector, other_vector)
                similarities.append((other_user, similarity))
        
        # 排序并返回top K
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    @staticmethod
    def collaborative_filtering_recommendations(user: User, 
                                              limit: int = 10) -> List[Post]:
        """
        基于用户的协同过滤推荐
        
        策略：
        1. 找到相似用户
        2. 获取相似用户喜欢的帖子
        3. 排除当前用户已交互过的帖子
        4. 按热度排序
        
        Args:
            user: 当前用户
            limit: 返回数量
            
        Returns:
            推荐帖子列表
        """
        # 找到相似用户
        similar_users = RecommendationService.find_similar_users(user, limit=20)
        
        if not similar_users:
            # 如果没有相似用户，返回热门帖子
            return list(Post.objects.filter(
                isDeletedByTeacher=False
            ).order_by('-heatScore')[:limit])
        
        # 获取相似用户喜欢的帖子
        similar_user_ids = [u.id for u, _ in similar_users]
        
        # 从点赞、收藏中获取
        liked_posts = PostLike.objects.filter(
            user_id__in=similar_user_ids
        ).values_list('post_id', flat=True)
        
        collected_posts = PostCollect.objects.filter(
            user_id__in=similar_user_ids
        ).values_list('post_id', flat=True)
        
        # 合并并去重
        candidate_post_ids = set(liked_posts) | set(collected_posts)
        
        # 排除当前用户已交互过的帖子
        user_liked = PostLike.objects.filter(user=user).values_list('post_id', flat=True)
        user_collected = PostCollect.objects.filter(user=user).values_list('post_id', flat=True)
        user_interacted = set(user_liked) | set(user_collected)
        
        candidate_post_ids -= user_interacted
        
        if not candidate_post_ids:
            # 如果没有候选帖子，返回热门帖子
            return list(Post.objects.filter(
                isDeletedByTeacher=False
            ).order_by('-heatScore')[:limit])
        
        # 获取候选帖子并按热度排序
        posts = Post.objects.filter(
            id__in=candidate_post_ids,
            isDeletedByTeacher=False
        ).select_related(
            'author', 'category', 'course'
        ).order_by('-heatScore')[:limit]
        
        return list(posts)
    
    @staticmethod
    def generate_recommendations(current_post: Optional[Post] = None,
                                user: Optional[User] = None,
                                limit: int = 10) -> Dict[str, List]:
        """
        生成综合推荐
        
        Args:
            current_post: 当前浏览的帖子（可选）
            user: 当前用户（可选）
            limit: 每个推荐类别的数量
            
        Returns:
            推荐结果字典
        """
        recommendations = {
            'similar_posts': [],
            'trending_posts': [],
            'personalized_posts': [],
            'trending_tags': []
        }
        
        # 1. 相似帖子（如果有当前帖子）
        if current_post:
            similar_posts = RecommendationService.find_similar_posts(
                current_post, 
                limit=limit
            )
            recommendations['similar_posts'] = [post for post, _ in similar_posts]
        
        # 2. 热门标签
        trending_tags = RecommendationService.get_trending_tags(limit=10)
        recommendations['trending_tags'] = trending_tags
        
        # 3. 热门标签相关的帖子
        if trending_tags:
            tag_names = [tag['tag'] for tag in trending_tags[:5]]
            trending_posts = RecommendationService.get_posts_by_trending_tags(
                tag_names,
                limit=limit
            )
            recommendations['trending_posts'] = trending_posts
        
        # 4. 个性化推荐（如果有用户）
        if user:
            personalized_posts = RecommendationService.collaborative_filtering_recommendations(
                user,
                limit=limit
            )
            recommendations['personalized_posts'] = personalized_posts
        
        return recommendations
    
    @staticmethod
    def recommend_for_post_view(post: Post, 
                                user: Optional[User] = None,
                                limit: int = 10) -> List[Post]:
        """
        为帖子详情页生成推荐列表
        
        混合策略：
        - 50% 相似帖子
        - 30% 个性化推荐（如果有用户）
        - 20% 热门帖子
        
        Args:
            post: 当前查看的帖子
            user: 当前用户
            limit: 返回数量
            
        Returns:
            推荐帖子列表
        """
        recommendations = []
        seen_ids = {post.id}
        
        # 1. 相似帖子 (50%)
        similar_count = int(limit * 0.5)
        similar_posts = RecommendationService.find_similar_posts(post, limit=similar_count * 2)
        for similar_post, _ in similar_posts:
            if similar_post.id not in seen_ids:
                recommendations.append(similar_post)
                seen_ids.add(similar_post.id)
                if len(recommendations) >= similar_count:
                    break
        
        # 2. 个性化推荐 (30%)
        if user:
            personalized_count = int(limit * 0.3)
            personalized_posts = RecommendationService.collaborative_filtering_recommendations(
                user, 
                limit=personalized_count * 2
            )
            for p in personalized_posts:
                if p.id not in seen_ids:
                    recommendations.append(p)
                    seen_ids.add(p.id)
                    if len(recommendations) >= similar_count + personalized_count:
                        break
        
        # 3. 热门帖子填充至目标数量
        if len(recommendations) < limit:
            trending_posts = RankingService.get_trending_posts(limit=limit * 2)
            for p in trending_posts:
                if p.id not in seen_ids:
                    recommendations.append(p)
                    seen_ids.add(p.id)
                    if len(recommendations) >= limit:
                        break
        
        return recommendations[:limit]
