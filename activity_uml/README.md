# 论坛系统Activity设计与实现文档

## 概述

本目录包含论坛系统的5个核心Activity的UML设计图，以及对应的Python实现。这些Activity共同构成了一个智能化的论坛搜索、推荐和交互系统。

## Activity设计文件

- `Activity1_SearchQuery.puml` - 搜索查询处理
- `Activity2_ContentRetrieval.puml` - 内容检索
- `Activity3_Ranking.puml` - 帖子排名和评分
- `Activity4_Recommendation.puml` - 内容推荐
- `Activity5_UserInteraction.puml` - 用户交互跟踪

## 实现位置

所有Activity的实现代码位于 `baplatform/baweb/utils/` 目录下：

```
baplatform/baweb/utils/
├── embedding_utils.py          # 向量嵌入工具
├── search_engine.py            # Activity 1: 搜索查询处理
├── content_retrieval.py        # Activity 2: 内容检索
├── ranking_service.py          # Activity 3: 帖子排名和评分
├── recommendation_service.py   # Activity 4: 内容推荐
└── interaction_tracker.py      # Activity 5: 用户交互跟踪
```

---

## Activity 1: 搜索查询处理

**设计文件**: `Activity1_SearchQuery.puml`  
**实现文件**: `search_engine.py`

### 功能
- 接收用户搜索查询
- 提取和标准化查询文本（分词、去标点）
- 生成768维查询向量
- 应用分类和标签过滤器
- 创建结构化的SearchQuery对象

### 核心类
- `SearchQuery`: 封装查询参数和向量
- `SearchEngine`: 提供搜索服务方法

### 关键方法
- `create_search_query()`: 创建搜索查询对象
- `tokenize_and_normalize()`: 文本标准化
- `apply_filters()`: 应用过滤条件
- `apply_sorting()`: 应用排序规则

---

## Activity 2: 内容检索

**设计文件**: `Activity2_ContentRetrieval.puml`  
**实现文件**: `content_retrieval.py`

### 功能
- **语义搜索**: 基于向量余弦相似度检索相关帖子
- **关键词搜索**: 基于文本匹配检索帖子
- 合并和去重搜索结果
- 应用分类和标签过滤

### 核心类
- `ContentRetrieval`: 内容检索服务

### 关键方法
- `semantic_search()`: 向量相似度搜索
- `keyword_search()`: 关键词文本搜索
- `merge_and_deduplicate()`: 结果合并去重
- `retrieve()`: 执行完整检索流程
- `retrieve_with_scores()`: 返回带详细分数的结果

---

## Activity 3: 帖子排名和评分

**设计文件**: `Activity3_Ranking.puml`  
**实现文件**: `ranking_service.py`

### 功能
- 计算帖子热度分数
  - **互动得分** (40%): 点赞×1 + 评论×2 + 收藏×3
  - **新鲜度** (30%): 基于发布时间的衰减函数
  - **浏览流行度** (30%): 对数归一化浏览数
- 个性化排名
  - 用户向量与帖子向量相似度匹配
  - 基于用户交互历史调整分数
  - 基于用户分类偏好提升分数

### 核心类
- `RankingService`: 排名服务

### 关键方法
- `calculate_heat_score()`: 计算综合热度
- `calculate_engagement_score()`: 计算互动得分
- `calculate_freshness_score()`: 计算新鲜度
- `calculate_personalized_score()`: 计算个性化分数
- `personalized_ranking()`: 个性化排名
- `batch_update_heat_scores()`: 批量更新热度

---

## Activity 4: 内容推荐

**设计文件**: `Activity4_Recommendation.puml`  
**实现文件**: `recommendation_service.py`

### 功能
- **相似帖子发现**: 基于向量相似度找到相关帖子
- **热门标签**: 分析时间窗口内的标签趋势
- **协同过滤**: 基于相似用户的喜好推荐
- **混合推荐策略**: 
  - 50% 相似帖子
  - 30% 个性化推荐
  - 20% 热门帖子

### 核心类
- `RecommendationService`: 推荐服务

### 关键方法
- `find_similar_posts()`: 发现相似帖子
- `get_trending_tags()`: 获取热门标签
- `find_similar_users()`: 找到相似用户
- `collaborative_filtering_recommendations()`: 协同过滤
- `recommend_for_post_view()`: 为帖子详情页生成推荐

---

## Activity 5: 用户交互跟踪

**设计文件**: `Activity5_UserInteraction.puml`  
**实现文件**: `interaction_tracker.py`

### 功能
- 记录用户交互行为
  - **浏览**: 增加浏览数，记录浏览历史
  - **点赞**: 增加点赞数，更新用户偏好，作者+1积分
  - **评论**: 增加评论数，更新用户偏好，作者+2积分
  - **收藏**: 增加收藏数，更新用户偏好，作者+3积分
- 更新用户画像
  - 维护交互历史 (JSON格式)
  - 更新分类偏好 (JSON格式)
  - 重新计算用户向量 (768维)
- 更新帖子指标
  - 实时更新热度分数
  - 触发排名重新计算

### 核心类
- `InteractionTracker`: 交互跟踪服务
- `InteractionType`: 交互类型枚举

### 关键方法
- `track_view()`: 记录浏览
- `track_like()`: 记录点赞
- `track_comment()`: 记录评论
- `track_collect()`: 记录收藏
- `update_user_interaction_history()`: 更新交互历史
- `recalculate_user_vector()`: 重新计算用户向量

---

## 向量嵌入工具

**实现文件**: `embedding_utils.py`

### 功能
- 文本向量化 (768维BERT风格)
- 向量编码/解码 (pickle序列化)
- 余弦相似度计算
- 批量相似度计算
- 向量平均和加权平均

### 核心类
- `EmbeddingUtils`: 向量工具类

### 便捷函数
- `generate_post_embedding()`: 为帖子生成嵌入向量
- `update_user_vector()`: 更新用户向量

### ⚠️ 重要说明
当前实现使用**模拟的向量生成**（基于哈希的确定性随机向量）。在生产环境中需要：
- 使用真实的嵌入模型（OpenAI API、本地BERT等）
- 集成向量数据库（Milvus、Pinecone）
- 实现批量处理和缓存机制

---

## 数据模型扩展

为支持这些Activity，对数据库模型进行了以下扩展：

### User模型新增字段
```python
userVector = BinaryField()           # 768维用户偏好向量
interactionHistory = TextField()     # JSON格式: {postId: score}
preferredCategories = TextField()    # JSON格式: {categoryId: score}
```

### 新增PostView模型
记录用户浏览历史，支持浏览行为跟踪。

**迁移文件**: `baweb/migrations/0028_user_interactionhistory_user_preferredcategories_and_more.py`

---

## 系统架构

```
┌─────────────────┐
│   用户请求      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Activity 1: 搜索查询处理        │
│  - 解析查询                      │
│  - 生成向量                      │
│  - 应用过滤器                    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Activity 2: 内容检索            │
│  - 语义搜索 (向量相似度)         │
│  - 关键词搜索 (文本匹配)         │
│  - 结果合并去重                  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Activity 3: 帖子排名            │
│  - 计算热度分数                  │
│  - 个性化调整                    │
│  - 排序输出                      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Activity 4: 内容推荐            │
│  - 相似帖子                      │
│  - 热门标签                      │
│  - 协同过滤                      │
└─────────────────────────────────┘

         ▲
         │
┌─────────────────────────────────┐
│  Activity 5: 用户交互跟踪        │
│  - 记录行为                      │
│  - 更新用户画像                  │
│  - 更新帖子指标                  │
└─────────────────────────────────┘
```

---

## 使用示例

### 1. 执行搜索
```python
from baweb.utils.search_engine import SearchEngine
from baweb.utils.content_retrieval import ContentRetrieval

# 创建搜索查询
query = SearchEngine.create_search_query(
    query_text="Django教程",
    category_id=1,
    tags="python,web",
    sort_by='heat'
)

# 执行检索
posts = ContentRetrieval.retrieve(query, top_k=20)
```

### 2. 个性化排名
```python
from baweb.utils.ranking_service import RankingService

# 对帖子列表进行个性化排名
ranked_posts = RankingService.rank_posts(
    posts=posts,
    user=current_user,
    sort_by='heat',
    enable_personalization=True
)
```

### 3. 生成推荐
```python
from baweb.utils.recommendation_service import RecommendationService

# 为帖子详情页生成推荐
recommendations = RecommendationService.recommend_for_post_view(
    post=current_post,
    user=current_user,
    limit=10
)
```

### 4. 跟踪用户交互
```python
from baweb.utils.interaction_tracker import InteractionTracker

# 记录点赞
result = InteractionTracker.track_like(user, post)

# 记录评论
InteractionTracker.track_comment(user, post, comment)

# 记录收藏
result = InteractionTracker.track_collect(user, post)
```

---

## 性能优化建议

1. **向量检索优化**
   - 使用向量数据库（Milvus、Pinecone）
   - 实现ANN（近似最近邻）算法
   - 建立向量索引

2. **缓存策略**
   - 缓存热门帖子的向量
   - 缓存用户向量
   - 缓存搜索结果

3. **异步处理**
   - 异步更新用户向量
   - 异步更新热度分数
   - 使用消息队列处理交互事件

4. **数据库优化**
   - 为热度字段建立索引
   - 使用Redis缓存热门数据
   - 实现读写分离

---

## 后续扩展方向

1. **深度学习集成**
   - 集成BERT/RoBERTa模型生成真实向量
   - 使用GPT进行内容理解和摘要
   - 实现图神经网络进行关系建模

2. **实时推荐**
   - 实现实时流处理
   - 动态调整推荐策略
   - A/B测试框架

3. **多模态搜索**
   - 支持图片搜索
   - 支持视频内容检索
   - 支持语音搜索

4. **高级分析**
   - 用户行为分析
   - 内容质量评估
   - 社区网络分析

---

## 参考资料

- Django官方文档: https://docs.djangoproject.com/
- 推荐系统实践: https://recsys.org/
- BERT模型: https://github.com/google-research/bert
- 向量数据库: https://milvus.io/

---

**最后更新**: 2025年12月22日  
**版本**: 1.0  
**状态**: ✅ 已实现并测试
