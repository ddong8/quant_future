<template>
  <div class="market-news-view">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><ChatDotRound /></el-icon>
          市场资讯
        </h1>
        <p class="page-description">实时市场新闻和分析资讯</p>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button 
            :type="activeCategory === 'all' ? 'primary' : 'default'"
            @click="setCategory('all')"
          >
            全部
          </el-button>
          <el-button 
            :type="activeCategory === 'market' ? 'primary' : 'default'"
            @click="setCategory('market')"
          >
            市场动态
          </el-button>
          <el-button 
            :type="activeCategory === 'policy' ? 'primary' : 'default'"
            @click="setCategory('policy')"
          >
            政策解读
          </el-button>
          <el-button 
            :type="activeCategory === 'analysis' ? 'primary' : 'default'"
            @click="setCategory('analysis')"
          >
            技术分析
          </el-button>
        </el-button-group>
        <el-button @click="refreshNews" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="news-content">
      <!-- 重要新闻轮播 -->
      <div class="important-news" v-if="importantNews.length > 0">
        <h3 class="section-title">
          <el-icon><Star /></el-icon>
          重要资讯
        </h3>
        <el-carousel height="200px" :interval="5000" indicator-position="outside">
          <el-carousel-item v-for="news in importantNews" :key="news.id">
            <div class="carousel-item" @click="openNewsDetail(news)">
              <div class="news-image" v-if="news.image">
                <img :src="news.image" :alt="news.title" />
              </div>
              <div class="news-content-overlay">
                <h4 class="news-title">{{ news.title }}</h4>
                <p class="news-summary">{{ news.summary }}</p>
                <div class="news-meta">
                  <span class="news-time">{{ formatTime(news.publishTime) }}</span>
                  <el-tag :type="getCategoryType(news.category)" size="small">
                    {{ getCategoryName(news.category) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-carousel-item>
        </el-carousel>
      </div>

      <!-- 新闻列表 -->
      <div class="news-list">
        <h3 class="section-title">
          <el-icon><Document /></el-icon>
          最新资讯
        </h3>
        
        <el-skeleton :loading="loading" animated>
          <template #template>
            <div v-for="i in 5" :key="i" class="news-skeleton">
              <el-skeleton-item variant="image" style="width: 120px; height: 80px;" />
              <div class="skeleton-content">
                <el-skeleton-item variant="h3" style="width: 60%" />
                <el-skeleton-item variant="text" style="width: 100%" />
                <el-skeleton-item variant="text" style="width: 80%" />
                <el-skeleton-item variant="text" style="width: 40%" />
              </div>
            </div>
          </template>
          
          <template #default>
            <div class="news-items">
              <div 
                v-for="news in filteredNews" 
                :key="news.id" 
                class="news-item"
                @click="openNewsDetail(news)"
              >
                <div class="news-image" v-if="news.image">
                  <img :src="news.image" :alt="news.title" />
                </div>
                <div class="news-info">
                  <h4 class="news-title">{{ news.title }}</h4>
                  <p class="news-summary">{{ news.summary }}</p>
                  <div class="news-meta">
                    <span class="news-source">{{ news.source }}</span>
                    <span class="news-time">{{ formatTime(news.publishTime) }}</span>
                    <el-tag :type="getCategoryType(news.category)" size="small">
                      {{ getCategoryName(news.category) }}
                    </el-tag>
                    <span class="news-views">
                      <el-icon><View /></el-icon>
                      {{ news.views }}
                    </span>
                  </div>
                </div>
                <div class="news-actions">
                  <el-button text @click.stop="toggleFavorite(news)">
                    <el-icon :class="{ 'favorited': news.isFavorited }">
                      <Star />
                    </el-icon>
                  </el-button>
                  <el-button text @click.stop="shareNews(news)">
                    <el-icon><Share /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </template>
        </el-skeleton>

        <!-- 加载更多 -->
        <div class="load-more" v-if="hasMore && !loading">
          <el-button @click="loadMore" :loading="loadingMore">
            加载更多
          </el-button>
        </div>
      </div>
    </div>

    <!-- 新闻详情对话框 -->
    <el-dialog
      v-model="showNewsDetail"
      :title="selectedNews?.title"
      width="80%"
      :before-close="closeNewsDetail"
    >
      <div class="news-detail" v-if="selectedNews">
        <div class="detail-meta">
          <span class="detail-source">{{ selectedNews.source }}</span>
          <span class="detail-time">{{ formatTime(selectedNews.publishTime) }}</span>
          <el-tag :type="getCategoryType(selectedNews.category)">
            {{ getCategoryName(selectedNews.category) }}
          </el-tag>
        </div>
        <div class="detail-image" v-if="selectedNews.image">
          <img :src="selectedNews.image" :alt="selectedNews.title" />
        </div>
        <div class="detail-content" v-html="selectedNews.content"></div>
        <div class="detail-actions">
          <el-button @click="toggleFavorite(selectedNews)">
            <el-icon><Star /></el-icon>
            {{ selectedNews.isFavorited ? '取消收藏' : '收藏' }}
          </el-button>
          <el-button @click="shareNews(selectedNews)">
            <el-icon><Share /></el-icon>
            分享
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ChatDotRound, 
  Refresh, 
  Star, 
  Document, 
  View, 
  Share 
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

interface NewsItem {
  id: string
  title: string
  summary: string
  content: string
  source: string
  publishTime: string
  category: string
  image?: string
  views: number
  isFavorited: boolean
  isImportant: boolean
}

const loading = ref(false)
const loadingMore = ref(false)
const activeCategory = ref('all')
const newsList = ref<NewsItem[]>([])
const selectedNews = ref<NewsItem | null>(null)
const showNewsDetail = ref(false)
const hasMore = ref(true)
const page = ref(1)

// 重要新闻
const importantNews = computed(() => 
  newsList.value.filter(news => news.isImportant).slice(0, 5)
)

// 过滤后的新闻
const filteredNews = computed(() => {
  if (activeCategory.value === 'all') {
    return newsList.value
  }
  return newsList.value.filter(news => news.category === activeCategory.value)
})

// 设置分类
const setCategory = (category: string) => {
  activeCategory.value = category
}

// 获取分类类型
const getCategoryType = (category: string) => {
  const types: Record<string, string> = {
    market: 'primary',
    policy: 'warning',
    analysis: 'success',
    breaking: 'danger'
  }
  return types[category] || 'info'
}

// 获取分类名称
const getCategoryName = (category: string) => {
  const names: Record<string, string> = {
    market: '市场动态',
    policy: '政策解读',
    analysis: '技术分析',
    breaking: '突发新闻'
  }
  return names[category] || '其他'
}

// 格式化时间
const formatTime = (time: string) => {
  return dayjs(time).fromNow()
}

// 生成模拟新闻数据
const generateMockNews = (): NewsItem[] => {
  const categories = ['market', 'policy', 'analysis', 'breaking']
  const sources = ['财经网', '新浪财经', '东方财富', '金融界', '证券时报', '第一财经']
  const titles = [
    '央行降准释放流动性，A股市场迎来利好',
    '美联储加息预期升温，全球股市震荡',
    '新能源汽车板块强势上涨，龙头股涨停',
    '房地产政策再度放松，地产股集体走强',
    '科技股回调，投资者关注业绩表现',
    '大宗商品价格上涨，相关概念股受益',
    '金融监管新规出台，银行股分化明显',
    '外资持续流入A股，看好中国经济前景',
    '创业板指数创新高，成长股表现亮眼',
    '沪深300指数震荡整理，市场观望情绪浓厚'
  ]

  return Array.from({ length: 20 }, (_, index) => ({
    id: `news_${index + 1}`,
    title: titles[index % titles.length] + `（${index + 1}）`,
    summary: '这是一条重要的市场资讯，详细内容请点击查看。市场波动较大，投资者需要密切关注相关政策和数据变化。',
    content: `
      <p>这是新闻的详细内容。市场分析师认为，当前市场环境下，投资者应该保持谨慎乐观的态度。</p>
      <p>从技术面来看，主要指数仍在关键支撑位之上，短期内有望继续震荡上行。</p>
      <p>建议投资者关注以下几个方面：</p>
      <ul>
        <li>宏观经济政策变化</li>
        <li>行业龙头企业业绩表现</li>
        <li>国际市场动态影响</li>
        <li>资金流向和市场情绪</li>
      </ul>
      <p>总体而言，市场机会与风险并存，建议做好风险控制。</p>
    `,
    source: sources[index % sources.length],
    publishTime: dayjs().subtract(index * 30, 'minute').toISOString(),
    category: categories[index % categories.length],
    image: index % 3 === 0 ? `https://picsum.photos/400/200?random=${index}` : undefined,
    views: Math.floor(Math.random() * 10000) + 100,
    isFavorited: Math.random() > 0.8,
    isImportant: index < 5
  }))
}

// 刷新新闻
const refreshNews = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    newsList.value = generateMockNews()
    page.value = 1
    hasMore.value = true
    ElMessage.success('新闻刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败，请重试')
  } finally {
    loading.value = false
  }
}

// 加载更多
const loadMore = async () => {
  loadingMore.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 800))
    const moreNews = generateMockNews().map(news => ({
      ...news,
      id: `${news.id}_page_${page.value + 1}`
    }))
    newsList.value.push(...moreNews)
    page.value++
    if (page.value >= 3) {
      hasMore.value = false
    }
  } catch (error) {
    ElMessage.error('加载失败，请重试')
  } finally {
    loadingMore.value = false
  }
}

// 打开新闻详情
const openNewsDetail = (news: NewsItem) => {
  selectedNews.value = news
  showNewsDetail.value = true
  // 增加浏览量
  news.views++
}

// 关闭新闻详情
const closeNewsDetail = () => {
  showNewsDetail.value = false
  selectedNews.value = null
}

// 切换收藏状态
const toggleFavorite = (news: NewsItem) => {
  news.isFavorited = !news.isFavorited
  ElMessage.success(news.isFavorited ? '收藏成功' : '取消收藏')
}

// 分享新闻
const shareNews = (news: NewsItem) => {
  if (navigator.share) {
    navigator.share({
      title: news.title,
      text: news.summary,
      url: window.location.href
    })
  } else {
    // 复制到剪贴板
    navigator.clipboard.writeText(`${news.title}\n${news.summary}\n${window.location.href}`)
    ElMessage.success('链接已复制到剪贴板')
  }
}

onMounted(() => {
  refreshNews()
})
</script>

<style lang="scss" scoped>
.market-news-view {
  padding: 24px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 20px;

  .header-content {
    .page-title {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0 0 8px 0;
      font-size: 28px;
      font-weight: 700;
      color: var(--el-text-color-primary);

      .el-icon {
        font-size: 32px;
        color: var(--el-color-primary);
      }
    }

    .page-description {
      margin: 0;
      font-size: 16px;
      color: var(--el-text-color-regular);
    }
  }

  .header-actions {
    display: flex;
    gap: 16px;
    align-items: center;
  }
}

.news-content {
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 16px 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);

    .el-icon {
      color: var(--el-color-primary);
    }
  }
}

.important-news {
  margin-bottom: 32px;

  .carousel-item {
    position: relative;
    height: 200px;
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.3s ease;

    &:hover {
      transform: scale(1.02);
    }

    .news-image {
      width: 100%;
      height: 100%;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    .news-content-overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
      color: white;
      padding: 20px;

      .news-title {
        margin: 0 0 8px 0;
        font-size: 18px;
        font-weight: 600;
        line-height: 1.4;
      }

      .news-summary {
        margin: 0 0 12px 0;
        font-size: 14px;
        opacity: 0.9;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .news-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 12px;

        .news-time {
          opacity: 0.8;
        }
      }
    }
  }
}

.news-list {
  .news-skeleton {
    display: flex;
    gap: 16px;
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);

    .skeleton-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
  }

  .news-items {
    .news-item {
      display: flex;
      gap: 16px;
      padding: 20px;
      background: var(--el-bg-color);
      border-radius: 12px;
      margin-bottom: 16px;
      cursor: pointer;
      transition: all 0.3s ease;
      border: 1px solid var(--el-border-color-lighter);

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        border-color: var(--el-color-primary-light-7);
      }

      .news-image {
        width: 120px;
        height: 80px;
        border-radius: 8px;
        overflow: hidden;
        flex-shrink: 0;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      .news-info {
        flex: 1;
        display: flex;
        flex-direction: column;

        .news-title {
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          line-height: 1.4;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .news-summary {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: var(--el-text-color-regular);
          line-height: 1.5;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
          flex: 1;
        }

        .news-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          font-size: 12px;
          color: var(--el-text-color-secondary);

          .news-views {
            display: flex;
            align-items: center;
            gap: 4px;
          }
        }
      }

      .news-actions {
        display: flex;
        flex-direction: column;
        gap: 8px;
        align-items: center;

        .el-button {
          padding: 8px;

          .favorited {
            color: var(--el-color-warning);
          }
        }
      }
    }
  }

  .load-more {
    text-align: center;
    padding: 20px;
  }
}

.news-detail {
  .detail-meta {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }

  .detail-image {
    margin-bottom: 20px;
    text-align: center;

    img {
      max-width: 100%;
      border-radius: 8px;
    }
  }

  .detail-content {
    line-height: 1.8;
    color: var(--el-text-color-primary);
    margin-bottom: 24px;

    :deep(p) {
      margin-bottom: 16px;
    }

    :deep(ul) {
      padding-left: 20px;
      margin-bottom: 16px;

      li {
        margin-bottom: 8px;
      }
    }
  }

  .detail-actions {
    display: flex;
    gap: 12px;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .market-news-view {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;

    .header-actions {
      flex-direction: column;
      gap: 12px;
    }
  }

  .news-item {
    flex-direction: column;

    .news-image {
      width: 100%;
      height: 160px;
    }

    .news-actions {
      flex-direction: row;
      justify-content: center;
    }
  }
}
</style>
