<template>
  <div 
    ref="containerRef" 
    class="virtual-list-container"
    :style="{ height: containerHeight + 'px' }"
    @scroll="handleScroll"
  >
    <div 
      class="virtual-list-phantom" 
      :style="{ height: totalHeight + 'px' }"
    ></div>
    
    <div 
      class="virtual-list-content"
      :style="{ transform: `translateY(${offsetY}px)` }"
    >
      <div
        v-for="(item, index) in visibleItems"
        :key="getItemKey(item, startIndex + index)"
        class="virtual-list-item"
        :style="{ height: itemHeight + 'px' }"
      >
        <slot 
          :item="item" 
          :index="startIndex + index"
          :isVisible="true"
        >
          {{ item }}
        </slot>
      </div>
    </div>
    
    <!-- 加载更多指示器 -->
    <div 
      v-if="loading && hasMore" 
      class="virtual-list-loading"
    >
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载中...</span>
    </div>
    
    <!-- 无更多数据提示 -->
    <div 
      v-if="!hasMore && items.length > 0" 
      class="virtual-list-no-more"
    >
      没有更多数据了
    </div>
    
    <!-- 空状态 -->
    <div 
      v-if="items.length === 0 && !loading" 
      class="virtual-list-empty"
    >
      <slot name="empty">
        <el-empty description="暂无数据" />
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { throttle } from 'lodash-es'

interface Props {
  items: T[]
  itemHeight: number
  containerHeight: number
  buffer?: number
  keyField?: keyof T | ((item: T, index: number) => string | number)
  loading?: boolean
  hasMore?: boolean
  loadMoreThreshold?: number
}

const props = withDefaults(defineProps<Props>(), {
  buffer: 5,
  keyField: 'id',
  loading: false,
  hasMore: true,
  loadMoreThreshold: 100
})

const emit = defineEmits<{
  loadMore: []
  scroll: [{ scrollTop: number; scrollLeft: number }]
  itemVisible: [{ item: T; index: number }]
  itemHidden: [{ item: T; index: number }]
}>()

const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)

// 计算可见区域的项目数量
const visibleCount = computed(() => {
  return Math.ceil(props.containerHeight / props.itemHeight) + props.buffer * 2
})

// 计算总高度
const totalHeight = computed(() => {
  return props.items.length * props.itemHeight
})

// 计算开始索引
const startIndex = computed(() => {
  const start = Math.floor(scrollTop.value / props.itemHeight) - props.buffer
  return Math.max(0, start)
})

// 计算结束索引
const endIndex = computed(() => {
  const end = startIndex.value + visibleCount.value
  return Math.min(props.items.length, end)
})

// 计算可见项目
const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value)
})

// 计算偏移量
const offsetY = computed(() => {
  return startIndex.value * props.itemHeight
})

// 获取项目的唯一键
const getItemKey = (item: T, index: number): string | number => {
  if (typeof props.keyField === 'function') {
    return props.keyField(item, index)
  }
  if (typeof props.keyField === 'string' && item && typeof item === 'object') {
    return (item as any)[props.keyField] ?? index
  }
  return index
}

// 节流的滚动处理函数
const handleScroll = throttle((event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
  
  emit('scroll', {
    scrollTop: target.scrollTop,
    scrollLeft: target.scrollLeft
  })
  
  // 检查是否需要加载更多
  const scrollBottom = target.scrollTop + target.clientHeight
  const threshold = target.scrollHeight - props.loadMoreThreshold
  
  if (scrollBottom >= threshold && props.hasMore && !props.loading) {
    emit('loadMore')
  }
}, 16) // 约60fps

// 滚动到指定索引
const scrollToIndex = (index: number, behavior: ScrollBehavior = 'smooth') => {
  if (!containerRef.value) return
  
  const targetScrollTop = index * props.itemHeight
  containerRef.value.scrollTo({
    top: targetScrollTop,
    behavior
  })
}

// 滚动到指定项目
const scrollToItem = (item: T, behavior: ScrollBehavior = 'smooth') => {
  const index = props.items.findIndex((i, idx) => getItemKey(i, idx) === getItemKey(item, 0))
  if (index !== -1) {
    scrollToIndex(index, behavior)
  }
}

// 获取可见项目的索引范围
const getVisibleRange = () => {
  return {
    start: startIndex.value,
    end: endIndex.value - 1
  }
}

// 检查项目是否可见
const isItemVisible = (index: number) => {
  return index >= startIndex.value && index < endIndex.value
}

// 监听可见项目变化，触发相应事件
let previousVisibleItems: T[] = []

watch(visibleItems, (newItems, oldItems) => {
  // 检测新出现的项目
  newItems.forEach((item, index) => {
    const actualIndex = startIndex.value + index
    if (!previousVisibleItems.includes(item)) {
      emit('itemVisible', { item, index: actualIndex })
    }
  })
  
  // 检测消失的项目
  if (oldItems) {
    oldItems.forEach((item, index) => {
      const actualIndex = startIndex.value + index
      if (!newItems.includes(item)) {
        emit('itemHidden', { item, index: actualIndex })
      }
    })
  }
  
  previousVisibleItems = [...newItems]
}, { deep: true })

// 响应式更新
const updateLayout = async () => {
  await nextTick()
  if (containerRef.value) {
    // 触发重新计算
    handleScroll({ target: containerRef.value } as Event)
  }
}

// 监听数据变化
watch(() => props.items.length, updateLayout)
watch(() => props.itemHeight, updateLayout)
watch(() => props.containerHeight, updateLayout)

onMounted(() => {
  updateLayout()
})

onUnmounted(() => {
  handleScroll.cancel()
})

// 暴露方法给父组件
defineExpose({
  scrollToIndex,
  scrollToItem,
  getVisibleRange,
  isItemVisible,
  updateLayout
})
</script>

<style scoped>
.virtual-list-container {
  position: relative;
  overflow: auto;
  will-change: scroll-position;
}

.virtual-list-phantom {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: -1;
}

.virtual-list-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  will-change: transform;
}

.virtual-list-item {
  box-sizing: border-box;
}

.virtual-list-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: var(--el-text-color-regular);
  font-size: 14px;
  gap: 8px;
}

.virtual-list-no-more {
  text-align: center;
  padding: 16px;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

.virtual-list-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

/* 滚动条样式 */
.virtual-list-container::-webkit-scrollbar {
  width: 6px;
}

.virtual-list-container::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 3px;
}

.virtual-list-container::-webkit-scrollbar-thumb {
  background: var(--el-border-color-darker);
  border-radius: 3px;
}

.virtual-list-container::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

/* 性能优化 */
.virtual-list-container {
  /* 启用硬件加速 */
  transform: translateZ(0);
  /* 优化滚动性能 */
  -webkit-overflow-scrolling: touch;
  /* 减少重绘 */
  contain: layout style paint;
}

.virtual-list-content {
  /* 启用硬件加速 */
  transform: translateZ(0);
  /* 减少重绘 */
  contain: layout style paint;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .virtual-list-container::-webkit-scrollbar {
    width: 4px;
  }
  
  .virtual-list-loading,
  .virtual-list-no-more {
    padding: 12px;
    font-size: 12px;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .virtual-list-container {
    scroll-behavior: auto !important;
  }
}
</style>