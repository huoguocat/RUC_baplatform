"""
Activity 2: 内容检索服务
实现语义搜索、关键词搜索、结果合并和过滤
"""

from typing import List, Dict, Tuple, Optional
from django.db.models import Q, QuerySet
from ..models import Post
from .embedding_utils import EmbeddingUtils
from .search_engine import SearchQuery


class ContentRetrieval:
    """内容检索服务类"""
    
    @staticmethod
    def semantic_search(query_vector, posts: List[Post], top_k: int = 50) -> List[Tuple[Post, float]]:
        """
        执行语义搜索（基于向量相似度）
        
        Args:
            query_vector: 查询向量(numpy array)
            posts: 候选帖子列表
            top_k: 返回前K个最相似的结果
            
        Returns:
            (帖子, 相似度分数)列表，按相似度降序排序
        """
        if query_vector is None:
            return []
        
        results = []
        
        for post in posts:
            if not post.embedding:
                continue
            
            # 解码帖子向量
            post_vector = EmbeddingUtils.decode_vector(post.embedding)
            if post_vector is None:
                continue
            
            # 计算相似度
            similarity = EmbeddingUtils.cosine_similarity(query_vector, post_vector)
            results.append((post, similarity))
        
        # 按相似度降序排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top K
        return results[:top_k]
    
    @staticmethod
    def keyword_search(query_text: str, queryset: QuerySet) -> List[Post]:
        """
        执行关键词搜索（基于文本匹配）
        
        Args:
            query_text: 查询文本
            queryset: Post查询集
            
        Returns:
            匹配的帖子列表
        """
        if not query_text:
            return []
        
        # 在标题、内容、标签中搜索
        results = queryset.filter(
            Q(title__icontains=query_text) |
            Q(content__icontains=query_text) |
            Q(tags__icontains=query_text)
        )
        
        return list(results)
    
    @staticmethod
    def merge_and_deduplicate(semantic_results: List[Tuple[Post, float]],
                             keyword_results: List[Post]) -> List[Post]:
        """
        合并语义搜索和关键词搜索结果并去重
        
        策略：
        1. 语义搜索结果优先（因为包含相似度分数）
        2. 添加关键词搜索中的额外结果
        3. 去除重复
        
        Args:
            semantic_results: 语义搜索结果 (帖子, 分数)列表
            keyword_results: 关键词搜索结果列表
            
        Returns:
            去重后的帖子列表
        """
        # 使用字典去重，保持顺序
        merged = {}
        
        # 添加语义搜索结果
        for post, score in semantic_results:
            merged[post.id] = post
        
        # 添加关键词搜索结果
        for post in keyword_results:
            if post.id not in merged:
                merged[post.id] = post
        
        return list(merged.values())
    
    @staticmethod
    def apply_category_filter(posts: List[Post], category_id: Optional[int]) -> List[Post]:
        """
        应用分类过滤
        
        Args:
            posts: 帖子列表
            category_id: 分类ID
            
        Returns:
            过滤后的帖子列表
        """
        if category_id is None:
            return posts
        
        return [post for post in posts if post.category_id == category_id]
    
    @staticmethod
    def apply_tag_filter(posts: List[Post], tags: List[str]) -> List[Post]:
        """
        应用标签过滤
        
        Args:
            posts: 帖子列表
            tags: 标签列表
            
        Returns:
            过滤后的帖子列表（包含任意一个标签的帖子）
        """
        if not tags:
            return posts
        
        filtered = []
        for post in posts:
            if not post.tags:
                continue
            
            post_tags = [t.strip().lower() for t in post.tags.split(',')]
            # 检查是否包含任意一个搜索标签
            if any(tag.lower() in post_tags for tag in tags):
                filtered.append(post)
        
        return filtered
    
    @staticmethod
    def retrieve(search_query: SearchQuery, 
                use_semantic: bool = True,
                use_keyword: bool = True,
                top_k: int = 50) -> List[Post]:
        """
        执行完整的内容检索流程
        
        Args:
            search_query: 搜索查询对象
            use_semantic: 是否使用语义搜索
            use_keyword: 是否使用关键词搜索
            top_k: 语义搜索返回的最大结果数
            
        Returns:
            检索到的帖子列表
        """
        # 基础查询集：未被删除的帖子
        base_queryset = Post.objects.filter(isDeletedByTeacher=False).select_related(
            'author', 'category', 'course'
        )
        
        # 应用课程过滤
        if search_query.course_id:
            if search_query.course_id == -1:
                base_queryset = base_queryset.filter(course__isnull=True)
            else:
                base_queryset = base_queryset.filter(course_id=search_query.course_id)
        
        # 应用分类过滤
        if search_query.selected_category:
            base_queryset = base_queryset.filter(category_id=search_query.selected_category)
        
        # 如果没有查询文本，直接返回过滤后的结果
        if not search_query.query_text:
            queryset = base_queryset
            
            # 应用标签过滤
            if search_query.selected_tags:
                tag_query = Q()
                for tag in search_query.selected_tags:
                    tag_query |= Q(tags__icontains=tag)
                queryset = queryset.filter(tag_query)
            
            return list(queryset)
        
        # 语义搜索
        semantic_results = []
        if use_semantic and search_query.query_vector is not None:
            # 获取所有候选帖子（有embedding的）
            candidates = list(base_queryset.exclude(embedding__isnull=True))
            semantic_results = ContentRetrieval.semantic_search(
                search_query.query_vector, 
                candidates, 
                top_k
            )
        
        # 关键词搜索
        keyword_results = []
        if use_keyword:
            keyword_results = ContentRetrieval.keyword_search(
                search_query.query_text,
                base_queryset
            )
        
        # 合并和去重
        merged_posts = ContentRetrieval.merge_and_deduplicate(
            semantic_results,
            keyword_results
        )
        
        # 应用标签过滤
        if search_query.selected_tags:
            merged_posts = ContentRetrieval.apply_tag_filter(
                merged_posts,
                search_query.selected_tags
            )
        
        return merged_posts
    
    @staticmethod
    def retrieve_with_scores(search_query: SearchQuery,
                           top_k: int = 50) -> List[Tuple[Post, Dict[str, float]]]:
        """
        执行检索并返回详细分数信息
        
        Args:
            search_query: 搜索查询对象
            top_k: 返回的最大结果数
            
        Returns:
            (帖子, 分数字典)列表
            分数字典包含: semantic_score, keyword_match, total_score
        """
        base_queryset = Post.objects.filter(isDeletedByTeacher=False).select_related(
            'author', 'category', 'course'
        )
        
        # 应用课程和分类过滤
        if search_query.course_id:
            if search_query.course_id == -1:
                base_queryset = base_queryset.filter(course__isnull=True)
            else:
                base_queryset = base_queryset.filter(course_id=search_query.course_id)
        
        if search_query.selected_category:
            base_queryset = base_queryset.filter(category_id=search_query.selected_category)
        
        # 没有查询文本
        if not search_query.query_text:
            posts = list(base_queryset)
            return [(post, {'semantic_score': 0, 'keyword_match': 0, 'total_score': 0}) 
                    for post in posts]
        
        # 创建分数字典
        scores_dict = {}
        
        # 语义搜索
        if search_query.query_vector is not None:
            candidates = list(base_queryset.exclude(embedding__isnull=True))
            semantic_results = ContentRetrieval.semantic_search(
                search_query.query_vector,
                candidates,
                top_k * 2  # 获取更多候选
            )
            
            for post, score in semantic_results:
                scores_dict[post.id] = {
                    'post': post,
                    'semantic_score': score,
                    'keyword_match': 0
                }
        
        # 关键词搜索
        keyword_results = ContentRetrieval.keyword_search(
            search_query.query_text,
            base_queryset
        )
        
        for post in keyword_results:
            if post.id in scores_dict:
                scores_dict[post.id]['keyword_match'] = 1
            else:
                scores_dict[post.id] = {
                    'post': post,
                    'semantic_score': 0,
                    'keyword_match': 1
                }
        
        # 计算总分：语义分数 70% + 关键词匹配 30%
        results = []
        for post_id, info in scores_dict.items():
            total_score = info['semantic_score'] * 0.7 + info['keyword_match'] * 0.3
            info['total_score'] = total_score
            results.append((info['post'], info))
        
        # 按总分排序
        results.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # 应用标签过滤
        if search_query.selected_tags:
            filtered_results = []
            for post, scores in results:
                if post.tags:
                    post_tags = [t.strip().lower() for t in post.tags.split(',')]
                    if any(tag.lower() in post_tags for tag in search_query.selected_tags):
                        filtered_results.append((post, scores))
            results = filtered_results
        
        return results[:top_k]
