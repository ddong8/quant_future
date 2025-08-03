<template>
  <div 
    ref="containerRef"
    class="lazy-image-container"
    :class="{
      'is-loading': isLoading,
      'is-error': hasError,
      'is-loaded': isLoaded
    }"
    :style="containerStyle"
  >
    <!-- 占位符 -->
    <div 
      v-if="showPlaceholder" 
      class="lazy-image-placeholder"
    >
      <slot name="placeholder">
        <div class="default-placeholder">
          <el-icon size="24">
            <Picture />
          </el-icon>
        </div>
      </slot>
    </div>
    
    <!-- 加载中状态 -->
    <div 
      v-if="isLoading && showLoading" 
      class="lazy-image-loading"
    >
      <slot name="loading">
        <div class="default-loading">
          <el-icon class="is-loading" size="20">
            <Loading />
          </el-icon>
        </div>
      </slot>
    </div>
    
    <!-- 实际图片 -->
    <img
      v-show="isLoaded"
      ref="imageRef"
      :src="currentSrc"
      :alt="alt"
      :class="imageClass"
      :style="imageStyle"
      @load="handleLoad"
      @error="handleError"
    />
    
    <!-- 错误状态 -->
    <div 
      v-if="hasError" 
      class="lazy-image-error"
      @click="handleRetry"
    >
      <slot name="error">
        <div class="default-error">
          <el-icon size="24">
            <PictureFilled />
          </el-icon>
          <p>图片加载失败</p>
          <el-button size="small" type="primary" @click="handleRetry">
            重试
          </el-button>
        </div>
      </slot>
    </div>
    
    <!-- 渐进式加载效果 -->
    <div 
      v-if="progressive && lowQualitySrc && !isLoaded"
      class="lazy-image-progressive"
    >
      <img
        :src="lowQualitySrc"
        :alt="alt"
        class="progressive-image"
        @load="handleProgressiveLoad"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Picture, PictureFilled, Loading } from '@element-plus/icons-vue'

interface Props {
  src: string
  alt?: string
  width?: number | string
  height?: number | string
  fit?: 'fill' | 'contain' | 'cover' | 'none' | 'scale-down'
  lazy?: boolean
  progressive?: boolean
  lowQualitySrc?: string
  placeholder?: boolean
  loading?: boolean
  rootMargin?: string
  threshold?: number
  retries?: number
  timeout?: number
  imageClass?: string
  imageStyle?: Record<string, any>
  webp?: boolean
  avif?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  alt: '',
  fit: 'cover',
  lazy: true,
  progressive: false,
  placeholder: true,
  loading: true,
  rootMargin: '50px',
  threshold: 0.1,
  retries: 3,
  timeout: 10000,
  webp: true,
  avif: true
})

const emit = defineEmits<{
  load: [Event]
  error: [Event]
  intersect: [IntersectionObserverEntry]
}>()

const containerRef = ref<HTMLElement>()
const imageRef = ref<HTMLImageElement>()
const isLoading = ref(false)
const isLoaded = ref(false)
const hasError = ref(false)
const retryCount = ref(0)
const currentSrc = ref('')

// 计算容器样式
const containerStyle = computed(() => {
  const style: Record<string, any> = {}
  
  if (props.width) {
    style.width = typeof props.width === 'number' ? `${props.width}px` : props.width
  }
  
  if (props.height) {
    style.height = typeof props.height === 'number' ? `${props.height}px` : props.height
  }
  
  return style
})

// 显示占位符
const showPlaceholder = computed(() => {
  return props.placeholder && !isLoaded.value && !isLoading.value && !hasError.value
})

// 显示加载状态
const showLoading = computed(() => {
  return props.loading && isLoading.value && !hasError.value
})

// 获取最佳图片格式
const getBestImageSrc = (src: string): string => {
  if (!src) return src
  
  // 检查浏览器支持的格式
  const supportsAvif = props.avif && checkImageSupport('avif')
  const supportsWebp = props.webp && checkImageSupport('webp')
  
  // 如果原始URL已经是优化格式，直接返回
  if (src.includes('.avif') || src.includes('.webp')) {
    return src
  }
  
  // 尝试生成优化格式的URL
  const baseUrl = src.replace(/\.(jpg|jpeg|png)$/i, '')
  
  if (supportsAvif) {
    return `${baseUrl}.avif`
  }
  
  if (supportsWebp) {
    return `${baseUrl}.webp`
  }
  
  return src
}

// 检查图片格式支持
const checkImageSupport = (format: string): boolean => {
  const canvas = document.createElement('canvas')
  canvas.width = 1
  canvas.height = 1
  
  try {
    const dataUrl = canvas.toDataURL(`image/${format}`)
    return dataUrl.indexOf(`data:image/${format}`) === 0
  } catch {
    return false
  }
}

// 创建 Intersection Observer
let observer: IntersectionObserver | null = null

const createObserver = () => {
  if (!('IntersectionObserver' in window)) {
    // 不支持 IntersectionObserver，直接加载
    loadImage()
    return
  }
  
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        emit('intersect', entry)
        
        if (entry.isIntersecting) {
          loadImage()
          observer?.unobserve(entry.target)
        }
      })
    },
    {
      rootMargin: props.rootMargin,
      threshold: props.threshold
    }
  )
  
  if (containerRef.value) {
    observer.observe(containerRef.value)
  }
}

// 加载图片
const loadImage = async () => {
  if (isLoading.value || isLoaded.value) return
  
  isLoading.value = true
  hasError.value = false
  
  try {
    const src = getBestImageSrc(props.src)
    await loadImageWithTimeout(src)
    currentSrc.value = src
  } catch (error) {
    console.error('Image load failed:', error)
    handleLoadError()
  }
}

// 带超时的图片加载
const loadImageWithTimeout = (src: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    let timeoutId: NodeJS.Timeout
    
    const cleanup = () => {
      clearTimeout(timeoutId)
      img.onload = null
      img.onerror = null
    }
    
    img.onload = () => {
      cleanup()
      resolve()
    }
    
    img.onerror = () => {
      cleanup()
      reject(new Error('Image load failed'))
    }
    
    // 设置超时
    timeoutId = setTimeout(() => {
      cleanup()
      reject(new Error('Image load timeout'))
    }, props.timeout)
    
    img.src = src
  })
}

// 处理图片加载成功
const handleLoad = (event: Event) => {
  isLoading.value = false
  isLoaded.value = true
  hasError.value = false
  retryCount.value = 0
  
  emit('load', event)
}

// 处理图片加载错误
const handleError = (event: Event) => {
  handleLoadError()
  emit('error', event)
}

// 处理加载错误
const handleLoadError = () => {
  isLoading.value = false
  hasError.value = true
  
  // 如果是格式优化失败，尝试原始格式
  if (currentSrc.value !== props.src && retryCount.value === 0) {
    retryCount.value++
    currentSrc.value = props.src
    setTimeout(() => {
      isLoading.value = true
      hasError.value = false
    }, 100)
  }
}

// 处理渐进式加载
const handleProgressiveLoad = () => {
  // 渐进式图片加载完成，可以添加一些效果
}

// 重试加载
const handleRetry = () => {
  if (retryCount.value >= props.retries) {
    return
  }
  
  retryCount.value++
  hasError.value = false
  loadImage()
}

// 预加载图片
const preload = () => {
  if (!props.lazy) {
    loadImage()
  }
}

// 监听 src 变化
watch(() => props.src, () => {
  if (!props.src) return
  
  // 重置状态
  isLoading.value = false
  isLoaded.value = false
  hasError.value = false
  retryCount.value = 0
  currentSrc.value = ''
  
  // 重新加载
  if (props.lazy) {
    createObserver()
  } else {
    loadImage()
  }
})

onMounted(() => {
  if (!props.src) return
  
  if (props.lazy) {
    createObserver()
  } else {
    loadImage()
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})

// 暴露方法给父组件
defineExpose({
  preload,
  retry: handleRetry,
  isLoading,
  isLoaded,
  hasError
})
</script>

<style scoped>
.lazy-image-container {
  position: relative;
  display: inline-block;
  overflow: hidden;
  background: var(--el-fill-color-lighter);
}

.lazy-image-placeholder,
.lazy-image-loading,
.lazy-image-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-lighter);
}

.default-placeholder {
  color: var(--el-text-color-placeholder);
}

.default-loading {
  color: var(--el-color-primary);
}

.default-error {
  text-align: center;
  color: var(--el-text-color-regular);
}

.default-error p {
  margin: 8px 0;
  font-size: 12px;
}

.lazy-image-container img {
  width: 100%;
  height: 100%;
  object-fit: v-bind('props.fit');
  transition: opacity 0.3s ease;
}

.lazy-image-progressive {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

.progressive-image {
  width: 100%;
  height: 100%;
  object-fit: v-bind('props.fit');
  filter: blur(2px);
  opacity: 0.8;
}

/* 加载状态 */
.is-loading .lazy-image-container img {
  opacity: 0;
}

.is-loaded .lazy-image-container img {
  opacity: 1;
}

.is-error .lazy-image-container img {
  opacity: 0;
}

/* 错误状态可点击 */
.lazy-image-error {
  cursor: pointer;
}

.lazy-image-error:hover {
  background: var(--el-fill-color-light);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .default-error {
    font-size: 12px;
  }
  
  .default-error .el-button {
    font-size: 12px;
    padding: 4px 8px;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .lazy-image-container img,
  .progressive-image {
    transition: none;
  }
}
</style>