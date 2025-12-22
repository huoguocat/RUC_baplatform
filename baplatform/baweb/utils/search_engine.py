"""
Activity 1: 搜索查询处理服务
实现搜索查询的解析、向量化、过滤器应用
"""

from typing import Optional, List, Dict, Any
from django.db.models import Q, QuerySet
from ..models import Post, ContentCategory
from .embedding_utils import EmbeddingUtils
import re


class SearchQuery:
    """搜索查询对象"""
    
    def __init__(self, 
                 query_text: str,
                 selected_category: Optional[int] = None,
                 selected_tags: Optional[List[str]] = None,
                 sort_by: str = 'heat',
                 course_id: Optional[int] = None):
        """
        初始化搜索查询
        
        Args:
            query_text: 搜索文本
            selected_category: 选中的分类ID
            selected_tags: 选中的标签列表
            sort_by: 排序方式 ('heat', 'newest', 'bounty')
            course_id: 课程ID（可选）
        """
        self.query_text = query_text
        self.selected_category = selected_category
        self.selected_tags = selected_tags or []
        self.sort_by = sort_by
        self.course_id = course_id
        
        # 生成查询向量
        self.query_vector = None
        if query_text:
            self.query_vector = EmbeddingUtils.text_to_vector(query_text)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            'query_text': self.query_text,
            'selected_category': self.selected_category,
            'selected_tags': self.selected_tags,
            'sort_by': self.sort_by,
            'course_id': self.course_id,
            'has_vector': self.query_vector is not None
        }


class SearchEngine:
    """搜索引擎服务类"""
    
    @staticmethod
    def tokenize_and_normalize(text: str) -> List[str]:
        """
        对文本进行分词和标准化
        
        Args:
            text: 输入文本
            
        Returns:
            标准化后的词列表
        """
        # 简单的分词实现：去除标点，转小写，分割空格
        # 实际应用中应使用jieba等中文分词工具
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [token for token in tokens if token]
    
    @staticmethod
    def create_search_query(query_text: str,
                          category_id: Optional[int] = None,
                          tags: Optional[str] = None,
                          sort_by: str = 'heat',
                          course_id: Optional[int] = None) -> SearchQuery:
        """
        创建搜索查询对象
        
        Args:
            query_text: 查询文本
            category_id: 分类ID
            tags: 标签字符串（逗号分隔）
            sort_by: 排序方式
            course_id: 课程ID
            
        Returns:
            SearchQuery对象
        """
        # 处理标签
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # 创建查询对象
        search_query = SearchQuery(
            query_text=query_text.strip() if query_text else '',
            selected_category=category_id,
            selected_tags=tag_list,
            sort_by=sort_by,
            course_id=course_id
        )
        
        return search_query
    
    @staticmethod
    def apply_filters(queryset: QuerySet, search_query: SearchQuery) -> QuerySet:
        """
        应用搜索过滤器到查询集
        
        Args:
            queryset: Post查询集
            search_query: 搜索查询对象
            
        Returns:
            过滤后的查询集
        """
        # 1. 分类过滤
        if search_query.selected_category:
            queryset = queryset.filter(category_id=search_query.selected_category)
        
        # 2. 标签过滤
        if search_query.selected_tags:
            # 使用Q对象构建OR查询
            tag_query = Q()
            for tag in search_query.selected_tags:
                tag_query |= Q(tags__icontains=tag)
            queryset = queryset.filter(tag_query)
        
        # 3. 课程过滤
        if search_query.course_id:
            if search_query.course_id == -1:  # -1表示无课程帖子
                queryset = queryset.filter(course__isnull=True)
            else:
                queryset = queryset.filter(course_id=search_query.course_id)
        
        # 4. 关键词过滤（基础文本搜索）
        if search_query.query_text:
            queryset = queryset.filter(
                Q(title__icontains=search_query.query_text) |
                Q(content__icontains=search_query.query_text) |
                Q(tags__icontains=search_query.query_text)
            )
        
        return queryset
    
    @staticmethod
    def apply_sorting(queryset: QuerySet, sort_by: str) -> QuerySet:
        """
        应用排序到查询集
        
        Args:
            queryset: Post查询集
            sort_by: 排序方式
            
        Returns:
            排序后的查询集
        """
        # 置顶帖子始终在前
        if sort_by == 'newest':
            return queryset.order_by('-isPinned', '-createdAt')
        elif sort_by == 'bounty':
            return queryset.order_by('-isPinned', '-bountyPoints', '-createdAt')
        else:  # 默认按热度
            return queryset.order_by('-isPinned', '-heatScore', '-createdAt')
    
    @staticmethod
    def search(query_text: str = '',
               category_id: Optional[int] = None,
               tags: Optional[str] = None,
               sort_by: str = 'heat',
               course_id: Optional[int] = None,
               limit: Optional[int] = None) -> List[Post]:
        """
        执行搜索
        
        Args:
            query_text: 查询文本
            category_id: 分类ID
            tags: 标签（逗号分隔）
            sort_by: 排序方式
            course_id: 课程ID
            limit: 结果数量限制
            
        Returns:
            帖子列表
        """
        # 创建搜索查询对象
        search_query = SearchEngine.create_search_query(
            query_text=query_text,
            category_id=category_id,
            tags=tags,
            sort_by=sort_by,
            course_id=course_id
        )
        
        # 获取基础查询集
        queryset = Post.objects.filter(isDeletedByTeacher=False).select_related(
            'author', 'category', 'course'
        )
        
        # 应用过滤器
        queryset = SearchEngine.apply_filters(queryset, search_query)
        
        # 应用排序
        queryset = SearchEngine.apply_sorting(queryset, sort_by)
        
        # 应用限制
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def get_search_statistics(search_query: SearchQuery) -> Dict[str, Any]:
        """
        获取搜索统计信息
        
        Args:
            search_query: 搜索查询对象
            
        Returns:
            统计信息字典
        """
        # 获取过滤后的查询集
        queryset = Post.objects.filter(isDeletedByTeacher=False)
        queryset = SearchEngine.apply_filters(queryset, search_query)
        
        return {
            'total_results': queryset.count(),
            'has_query_text': bool(search_query.query_text),
            'has_category_filter': search_query.selected_category is not None,
            'has_tag_filter': bool(search_query.selected_tags),
            'has_course_filter': search_query.course_id is not None
        }
