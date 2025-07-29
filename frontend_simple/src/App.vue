<template>
  <div id="app">
    <h1>🚀 量化交易平台</h1>
    <div>
      <button @click="testAPI">测试后端API</button>
      <pre>{{ result }}</pre>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      result: '点击按钮测试API...'
    }
  },
  methods: {
    async testAPI() {
      try {
        const response = await axios.get('http://localhost:8000/health')
        this.result = JSON.stringify(response.data, null, 2)
      } catch (error) {
        this.result = '错误: ' + error.message
      }
    }
  }
}
</script>