<template>
  <div class="economic-calendar-view">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon><Calendar /></el-icon>
          财经日历
        </h1>
        <p class="page-description">重要经济事件和数据发布时间表</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          @change="onDateChange"
          :shortcuts="dateShortcuts"
        />
        <el-select v-model="selectedImportance" placeholder="重要性筛选" style="width: 120px">
          <el-option label="全部" value="all" />
          <el-option label="高" value="high" />
          <el-option label="中" value="medium" />
          <el-option label="低" value="low" />
        </el-select>
        <el-button @click="refreshEvents" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="calendar-content">
      <!-- 日历视图切换 -->
      <div class="view-controls">
        <el-radio-group v-model="viewMode" @change="onViewModeChange">
          <el-radio-button label="calendar">日历视图</el-radio-button>
          <el-radio-button label="list">列表视图</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 日历视图 -->
      <div v-if="viewMode === 'calendar'" class="calendar-view">
        <el-calendar v-model="selectedDate" @input="onDateChange">
          <template #date-cell="{ data }">
            <div class="calendar-cell">
              <div class="date-number">{{ data.day.split('-').pop() }}</div>
              <div class="events-indicator" v-if="getEventsForDate(data.day).length > 0">
                <div 
                  v-for="event in getEventsForDate(data.day).slice(0, 3)" 
                  :key="event.id"
                  :class="['event-dot', `importance-${event.importance}`]"
                ></div>
                <span v-if="getEventsForDate(data.day).length > 3" class="more-events">
                  +{{ getEventsForDate(data.day).length - 3 }}
                </span>
              </div>
            </div>
          </template>
        </el-calendar>
      </div>

      <!-- 列表视图 -->
      <div v-if="viewMode === 'list'" class="list-view">
        <el-skeleton :loading="loading" animated>
          <template #template>
            <div v-for="i in 5" :key="i" class="event-skeleton">
              <el-skeleton-item variant="circle" style="width: 40px; height: 40px;" />
              <div class="skeleton-content">
                <el-skeleton-item variant="h3" style="width: 60%" />
                <el-skeleton-item variant="text" style="width: 100%" />
                <el-skeleton-item variant="text" style="width: 40%" />
              </div>
            </div>
          </template>
          
          <template #default>
            <div class="events-timeline">
              <div 
                v-for="(dayEvents, date) in groupedEvents" 
                :key="date" 
                class="day-events"
              >
                <div class="day-header">
                  <h3 class="day-title">{{ formatDate(date) }}</h3>
                  <el-tag size="small">{{ dayEvents.length }} 个事件</el-tag>
                </div>
                
                <div class="events-list">
                  <div 
                    v-for="event in dayEvents" 
                    :key="event.id"
                    class="event-item"
                    @click="openEventDetail(event)"
                  >
                    <div class="event-time">
                      <div class="time-display">{{ formatTime(event.time) }}</div>
                      <div :class="['importance-indicator', `importance-${event.importance}`]">
                        <span class="importance-text">{{ getImportanceText(event.importance) }}</span>
                      </div>
                    </div>
                    
                    <div class="event-content">
                      <div class="event-header">
                        <h4 class="event-title">{{ event.title }}</h4>
                        <el-tag :type="getCurrencyType(event.currency)" size="small">
                          {{ event.currency }}
                        </el-tag>
                      </div>
                      
                      <p class="event-description">{{ event.description }}</p>
                      
                      <div class="event-data" v-if="event.forecast || event.previous">
                        <div class="data-item" v-if="event.forecast">
                          <span class="data-label">预期:</span>
                          <span class="data-value">{{ event.forecast }}</span>
                        </div>
                        <div class="data-item" v-if="event.previous">
                          <span class="data-label">前值:</span>
                          <span class="data-value">{{ event.previous }}</span>
                        </div>
                        <div class="data-item" v-if="event.actual">
                          <span class="data-label">实际:</span>
                          <span :class="['data-value', getActualClass(event)]">{{ event.actual }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div class="event-actions">
                      <el-button text @click.stop="toggleReminder(event)">
                        <el-icon :class="{ 'reminded': event.hasReminder }">
                          <Bell />
                        </el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </el-skeleton>
      </div>

      <!-- 今日重要事件 -->
      <div class="today-events" v-if="todayImportantEvents.length > 0">
        <h3 class="section-title">
          <el-icon><Star /></el-icon>
          今日重要事件
        </h3>
        <div class="important-events-grid">
          <div 
            v-for="event in todayImportantEvents" 
            :key="event.id"
            class="important-event-card"
            @click="openEventDetail(event)"
          >
            <div class="card-header">
              <div class="event-time">{{ formatTime(event.time) }}</div>
              <el-tag :type="getCurrencyType(event.currency)" size="small">
                {{ event.currency }}
              </el-tag>
            </div>
            <h4 class="card-title">{{ event.title }}</h4>
            <div class="card-data" v-if="event.forecast || event.previous">
              <div class="data-row">
                <span>预期: {{ event.forecast || '--' }}</span>
                <span>前值: {{ event.previous || '--' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 事件详情对话框 -->
    <el-dialog
      v-model="showEventDetail"
      :title="selectedEvent?.title"
      width="60%"
      :before-close="closeEventDetail"
    >
      <div class="event-detail" v-if="selectedEvent">
        <div class="detail-header">
          <div class="detail-meta">
            <el-tag :type="getCurrencyType(selectedEvent.currency)">
              {{ selectedEvent.currency }}
            </el-tag>
            <div :class="['importance-badge', `importance-${selectedEvent.importance}`]">
              {{ getImportanceText(selectedEvent.importance) }}
            </div>
            <span class="event-time">{{ formatDateTime(selectedEvent.date, selectedEvent.time) }}</span>
          </div>
        </div>
        
        <div class="detail-description">
          <p>{{ selectedEvent.description }}</p>
        </div>
        
        <div class="detail-data" v-if="selectedEvent.forecast || selectedEvent.previous || selectedEvent.actual">
          <h4>数据详情</h4>
          <el-table :data="[selectedEvent]" style="width: 100%">
            <el-table-column prop="forecast" label="预期值" />
            <el-table-column prop="previous" label="前值" />
            <el-table-column prop="actual" label="实际值">
              <template #default="{ row }">
                <span :class="getActualClass(row)">{{ row.actual || '--' }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div class="detail-impact" v-if="selectedEvent.impact">
          <h4>市场影响</h4>
          <p>{{ selectedEvent.impact }}</p>
        </div>
        
        <div class="detail-actions">
          <el-button @click="toggleReminder(selectedEvent)">
            <el-icon><Bell /></el-icon>
            {{ selectedEvent.hasReminder ? '取消提醒' : '设置提醒' }}
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Calendar, 
  Refresh, 
  Star, 
  Bell 
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

interface EconomicEvent {
  id: string
  title: string
  description: string
  date: string
  time: string
  currency: string
  importance: 'high' | 'medium' | 'low'
  forecast?: string
  previous?: string
  actual?: string
  impact?: string
  hasReminder: boolean
}

const loading = ref(false)
const selectedDate = ref(new Date())
const selectedImportance = ref('all')
const viewMode = ref('list')
const events = ref<EconomicEvent[]>([])
const selectedEvent = ref<EconomicEvent | null>(null)
const showEventDetail = ref(false)

// 日期快捷选项
const dateShortcuts = [
  {
    text: '今天',
    value: new Date()
  },
  {
    text: '明天',
    value: () => {
      const date = new Date()
      date.setTime(date.getTime() + 3600 * 1000 * 24)
      return date
    }
  },
  {
    text: '一周后',
    value: () => {
      const date = new Date()
      date.setTime(date.getTime() + 3600 * 1000 * 24 * 7)
      return date
    }
  }
]

// 过滤后的事件
const filteredEvents = computed(() => {
  let filtered = events.value
  
  if (selectedImportance.value !== 'all') {
    filtered = filtered.filter(event => event.importance === selectedImportance.value)
  }
  
  return filtered
})

// 按日期分组的事件
const groupedEvents = computed(() => {
  const groups: Record<string, EconomicEvent[]> = {}
  
  filteredEvents.value.forEach(event => {
    if (!groups[event.date]) {
      groups[event.date] = []
    }
    groups[event.date].push(event)
  })
  
  // 按时间排序
  Object.keys(groups).forEach(date => {
    groups[date].sort((a, b) => a.time.localeCompare(b.time))
  })
  
  return groups
})

// 今日重要事件
const todayImportantEvents = computed(() => {
  const today = dayjs().format('YYYY-MM-DD')
  return events.value
    .filter(event => event.date === today && event.importance === 'high')
    .slice(0, 6)
})

// 获取指定日期的事件
const getEventsForDate = (date: string) => {
  return events.value.filter(event => event.date === date)
}

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY年MM月DD日 dddd')
}

// 格式化时间
const formatTime = (time: string) => {
  return time
}

// 格式化日期时间
const formatDateTime = (date: string, time: string) => {
  return `${formatDate(date)} ${time}`
}

// 获取重要性文本
const getImportanceText = (importance: string) => {
  const texts: Record<string, string> = {
    high: '高',
    medium: '中',
    low: '低'
  }
  return texts[importance] || '未知'
}

// 获取货币类型
const getCurrencyType = (currency: string) => {
  const types: Record<string, string> = {
    USD: 'primary',
    EUR: 'success',
    GBP: 'warning',
    JPY: 'info',
    CNY: 'danger'
  }
  return types[currency] || 'default'
}

// 获取实际值样式类
const getActualClass = (event: EconomicEvent) => {
  if (!event.actual || !event.forecast) return ''
  
  const actual = parseFloat(event.actual)
  const forecast = parseFloat(event.forecast)
  
  if (actual > forecast) return 'positive'
  if (actual < forecast) return 'negative'
  return 'neutral'
}

// 生成模拟数据
const generateMockEvents = (): EconomicEvent[] => {
  const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CNY']
  const importances: ('high' | 'medium' | 'low')[] = ['high', 'medium', 'low']
  
  const eventTemplates = [
    {
      title: '非农就业人数',
      description: '美国劳工部发布的月度就业数据，反映经济健康状况',
      impact: '对美元汇率和股市有重大影响'
    },
    {
      title: 'CPI消费者物价指数',
      description: '衡量通胀水平的重要指标',
      impact: '影响央行货币政策决策'
    },
    {
      title: 'GDP国内生产总值',
      description: '衡量经济总体表现的核心指标',
      impact: '反映经济增长速度和健康程度'
    },
    {
      title: '央行利率决议',
      description: '央行货币政策委员会利率决定',
      impact: '直接影响货币汇率和债券市场'
    },
    {
      title: '制造业PMI',
      description: '制造业采购经理人指数',
      impact: '预示经济活动的变化趋势'
    }
  ]

  const events: EconomicEvent[] = []
  
  // 生成未来7天的事件
  for (let i = 0; i < 7; i++) {
    const date = dayjs().add(i, 'day').format('YYYY-MM-DD')
    const eventsPerDay = Math.floor(Math.random() * 5) + 2
    
    for (let j = 0; j < eventsPerDay; j++) {
      const template = eventTemplates[Math.floor(Math.random() * eventTemplates.length)]
      const currency = currencies[Math.floor(Math.random() * currencies.length)]
      const importance = importances[Math.floor(Math.random() * importances.length)]
      
      const hour = Math.floor(Math.random() * 12) + 8
      const minute = Math.floor(Math.random() * 4) * 15
      const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
      
      events.push({
        id: `event_${i}_${j}`,
        title: `${currency} ${template.title}`,
        description: template.description,
        date,
        time,
        currency,
        importance,
        forecast: Math.random() > 0.5 ? (Math.random() * 10).toFixed(1) : undefined,
        previous: Math.random() > 0.3 ? (Math.random() * 10).toFixed(1) : undefined,
        actual: Math.random() > 0.7 ? (Math.random() * 10).toFixed(1) : undefined,
        impact: template.impact,
        hasReminder: Math.random() > 0.8
      })
    }
  }
  
  return events.sort((a, b) => {
    const dateCompare = a.date.localeCompare(b.date)
    if (dateCompare !== 0) return dateCompare
    return a.time.localeCompare(b.time)
  })
}

// 刷新事件
const refreshEvents = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    events.value = generateMockEvents()
    ElMessage.success('财经日历刷新成功')
  } catch (error) {
    ElMessage.error('刷新失败，请重试')
  } finally {
    loading.value = false
  }
}

// 日期变化处理
const onDateChange = (date: Date) => {
  selectedDate.value = date
}

// 视图模式变化处理
const onViewModeChange = (mode: string) => {
  viewMode.value = mode
}

// 打开事件详情
const openEventDetail = (event: EconomicEvent) => {
  selectedEvent.value = event
  showEventDetail.value = true
}

// 关闭事件详情
const closeEventDetail = () => {
  showEventDetail.value = false
  selectedEvent.value = null
}

// 切换提醒状态
const toggleReminder = (event: EconomicEvent) => {
  event.hasReminder = !event.hasReminder
  ElMessage.success(event.hasReminder ? '提醒设置成功' : '提醒已取消')
}

onMounted(() => {
  refreshEvents()
})
</script>

<style lang="scss" scoped>
.economic-calendar-view {
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

.calendar-content {
  .view-controls {
    margin-bottom: 24px;
    text-align: center;
  }
}

.calendar-view {
  .calendar-cell {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;

    .date-number {
      font-weight: 600;
      margin-bottom: 4px;
    }

    .events-indicator {
      display: flex;
      gap: 2px;
      align-items: center;

      .event-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;

        &.importance-high {
          background: var(--el-color-danger);
        }

        &.importance-medium {
          background: var(--el-color-warning);
        }

        &.importance-low {
          background: var(--el-color-info);
        }
      }

      .more-events {
        font-size: 10px;
        color: var(--el-text-color-secondary);
        margin-left: 2px;
      }
    }
  }
}

.list-view {
  .event-skeleton {
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

  .events-timeline {
    .day-events {
      margin-bottom: 32px;

      .day-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 2px solid var(--el-color-primary-light-8);

        .day-title {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }

      .events-list {
        .event-item {
          display: flex;
          gap: 16px;
          padding: 16px;
          background: var(--el-bg-color);
          border-radius: 12px;
          margin-bottom: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          border: 1px solid var(--el-border-color-lighter);

          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
            border-color: var(--el-color-primary-light-7);
          }

          .event-time {
            width: 120px;
            flex-shrink: 0;
            text-align: center;

            .time-display {
              font-size: 16px;
              font-weight: 600;
              color: var(--el-text-color-primary);
              margin-bottom: 8px;
            }

            .importance-indicator {
              padding: 4px 8px;
              border-radius: 12px;
              font-size: 12px;
              font-weight: 500;

              &.importance-high {
                background: var(--el-color-danger-light-8);
                color: var(--el-color-danger);
              }

              &.importance-medium {
                background: var(--el-color-warning-light-8);
                color: var(--el-color-warning);
              }

              &.importance-low {
                background: var(--el-color-info-light-8);
                color: var(--el-color-info);
              }
            }
          }

          .event-content {
            flex: 1;

            .event-header {
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              margin-bottom: 8px;

              .event-title {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
                color: var(--el-text-color-primary);
                line-height: 1.4;
              }
            }

            .event-description {
              margin: 0 0 12px 0;
              font-size: 14px;
              color: var(--el-text-color-regular);
              line-height: 1.5;
            }

            .event-data {
              display: flex;
              gap: 16px;
              font-size: 12px;

              .data-item {
                display: flex;
                gap: 4px;

                .data-label {
                  color: var(--el-text-color-secondary);
                }

                .data-value {
                  font-weight: 500;
                  color: var(--el-text-color-primary);

                  &.positive {
                    color: var(--el-color-success);
                  }

                  &.negative {
                    color: var(--el-color-danger);
                  }

                  &.neutral {
                    color: var(--el-text-color-primary);
                  }
                }
              }
            }
          }

          .event-actions {
            display: flex;
            align-items: center;

            .el-button {
              padding: 8px;

              .reminded {
                color: var(--el-color-warning);
              }
            }
          }
        }
      }
    }
  }
}

.today-events {
  margin-top: 32px;

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

  .important-events-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;

    .important-event-card {
      background: var(--el-bg-color);
      border-radius: 12px;
      padding: 16px;
      cursor: pointer;
      transition: all 0.3s ease;
      border: 1px solid var(--el-border-color-lighter);

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        border-color: var(--el-color-primary-light-7);
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .event-time {
          font-size: 14px;
          font-weight: 600;
          color: var(--el-color-primary);
        }
      }

      .card-title {
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        line-height: 1.4;
      }

      .card-data {
        .data-row {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }
}

.event-detail {
  .detail-header {
    margin-bottom: 20px;

    .detail-meta {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 16px;

      .importance-badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;

        &.importance-high {
          background: var(--el-color-danger-light-8);
          color: var(--el-color-danger);
        }

        &.importance-medium {
          background: var(--el-color-warning-light-8);
          color: var(--el-color-warning);
        }

        &.importance-low {
          background: var(--el-color-info-light-8);
          color: var(--el-color-info);
        }
      }

      .event-time {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .detail-description {
    margin-bottom: 20px;
    line-height: 1.6;
    color: var(--el-text-color-primary);
  }

  .detail-data,
  .detail-impact {
    margin-bottom: 20px;

    h4 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    p {
      margin: 0;
      line-height: 1.6;
      color: var(--el-text-color-regular);
    }
  }

  .detail-actions {
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .economic-calendar-view {
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

  .important-events-grid {
    grid-template-columns: 1fr;
  }

  .event-item {
    flex-direction: column;

    .event-time {
      width: 100%;
      text-align: left;
    }
  }
}
</style>
