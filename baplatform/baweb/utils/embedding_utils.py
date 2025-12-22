"""
向量嵌入工具模块
处理文本向量化、向量编码/解码、相似度计算等操作

注意：
这是一个简化的模拟实现。在生产环境中，应该：
1. 使用真实的嵌入模型（如OpenAI API、本地BERT模型等）
2. 使用向量数据库（如Milvus、Pinecone等）进行高效检索
3. 实现批量处理以提高性能
"""

import numpy as np
import pickle
import hashlib
from typing import List, Tuple, Optional


class EmbeddingUtils:
    """向量嵌入工具类"""
    
    EMBEDDING_DIM = 768  # 标准BERT embedding维度
    
    @staticmethod
    def text_to_vector(text: str) -> np.ndarray:
        """
        将文本转换为向量
        
        注意：这是一个简化的模拟实现
        真实环境应该使用预训练模型（如BERT、OpenAI embeddings等）
        
        Args:
            text: 输入文本
            
        Returns:
            768维numpy向量
        """
        # 使用文本hash值作为种子生成确定性的随机向量
        # 这样相同的文本总是生成相同的向量
        hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_value % (2**32))
        
        # 生成随机向量并归一化
        vector = np.random.randn(EmbeddingUtils.EMBEDDING_DIM)
        vector = vector / np.linalg.norm(vector)  # L2归一化
        
        return vector
    
    @staticmethod
    def encode_vector(vector: np.ndarray) -> bytes:
        """
        将numpy向量编码为字节串，用于存储到数据库
        
        Args:
            vector: numpy向量
            
        Returns:
            序列化的字节串
        """
        return pickle.dumps(vector)
    
    @staticmethod
    def decode_vector(vector_bytes: bytes) -> Optional[np.ndarray]:
        """
        从字节串解码为numpy向量
        
        Args:
            vector_bytes: 序列化的字节串
            
        Returns:
            numpy向量，如果解码失败返回None
        """
        try:
            return pickle.loads(vector_bytes)
        except:
            return None
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度分数 (0-1之间，1表示完全相同)
        """
        # 向量已经归一化，所以点积就是余弦相似度
        similarity = np.dot(vec1, vec2)
        # 确保在[0, 1]范围内
        return max(0.0, min(1.0, (similarity + 1) / 2))
    
    @staticmethod
    def batch_similarity(query_vector: np.ndarray, 
                        candidate_vectors: List[np.ndarray]) -> List[float]:
        """
        批量计算查询向量与候选向量的相似度
        
        Args:
            query_vector: 查询向量
            candidate_vectors: 候选向量列表
            
        Returns:
            相似度分数列表
        """
        similarities = []
        for vec in candidate_vectors:
            sim = EmbeddingUtils.cosine_similarity(query_vector, vec)
            similarities.append(sim)
        return similarities
    
    @staticmethod
    def average_vectors(vectors: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        计算多个向量的平均值，用于生成用户画像向量
        
        Args:
            vectors: 向量列表
            
        Returns:
            平均向量，如果输入为空返回None
        """
        if not vectors:
            return None
        
        avg_vector = np.mean(vectors, axis=0)
        # 归一化
        avg_vector = avg_vector / np.linalg.norm(avg_vector)
        return avg_vector
    
    @staticmethod
    def weighted_average_vectors(vectors: List[np.ndarray], 
                                 weights: List[float]) -> Optional[np.ndarray]:
        """
        计算向量的加权平均
        
        Args:
            vectors: 向量列表
            weights: 权重列表（应与vectors长度相同）
            
        Returns:
            加权平均向量，如果输入为空返回None
        """
        if not vectors or not weights or len(vectors) != len(weights):
            return None
        
        # 归一化权重
        total_weight = sum(weights)
        if total_weight == 0:
            return EmbeddingUtils.average_vectors(vectors)
        
        normalized_weights = [w / total_weight for w in weights]
        
        # 计算加权平均
        weighted_sum = np.zeros(EmbeddingUtils.EMBEDDING_DIM)
        for vec, weight in zip(vectors, normalized_weights):
            weighted_sum += vec * weight
        
        # 归一化结果
        weighted_sum = weighted_sum / np.linalg.norm(weighted_sum)
        return weighted_sum


# 便捷函数
def generate_post_embedding(title: str, content: str) -> bytes:
    """
    为帖子生成嵌入向量并编码
    
    Args:
        title: 帖子标题
        content: 帖子内容
        
    Returns:
        编码后的向量字节串
    """
    # 合并标题和内容，标题权重更高
    combined_text = f"{title} {title} {content}"
    vector = EmbeddingUtils.text_to_vector(combined_text)
    return EmbeddingUtils.encode_vector(vector)


def update_user_vector(user, interaction_posts: List, interaction_scores: List[float]) -> bytes:
    """
    根据用户交互历史更新用户向量
    
    Args:
        user: 用户对象
        interaction_posts: 用户交互过的帖子列表
        interaction_scores: 对应的交互分数（如：view=1, like=2, comment=3, collect=4）
        
    Returns:
        编码后的用户向量字节串
    """
    vectors = []
    weights = []
    
    for post, score in zip(interaction_posts, interaction_scores):
        if post.embedding:
            vec = EmbeddingUtils.decode_vector(post.embedding)
            if vec is not None:
                vectors.append(vec)
                weights.append(score)
    
    if not vectors:
        # 如果没有交互历史，返回零向量
        zero_vector = np.zeros(EmbeddingUtils.EMBEDDING_DIM)
        return EmbeddingUtils.encode_vector(zero_vector)
    
    # 计算加权平均
    user_vector = EmbeddingUtils.weighted_average_vectors(vectors, weights)
    return EmbeddingUtils.encode_vector(user_vector)
