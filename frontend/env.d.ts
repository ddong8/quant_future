/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module 'nprogress' {
  interface NProgress {
    configure(options: { showSpinner?: boolean }): NProgress
    start(): NProgress
    done(): NProgress
  }
  
  const nprogress: NProgress
  export default nprogress
}