# 多阶段构建 - 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 配置npm使用淘宝镜像源并安装依赖
RUN npm config set registry https://registry.npmmirror.com && \
    npm ci --only=production && npm install -D sass-embedded

# 设置构建时环境变量
ARG VITE_API_BASE_URL=/api
ARG VITE_WS_BASE_URL=/api/v1/ws
ARG VITE_APP_TITLE=量化交易平台
ARG VITE_ENABLE_MOCK=false

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL
ENV VITE_APP_TITLE=$VITE_APP_TITLE
ENV VITE_ENABLE_MOCK=$VITE_ENABLE_MOCK

# 复制源代码
COPY . .

# 构建应用
RUN npx vite build --config vite.config.simple.ts

# 生产阶段 - 使用nginx提供静态文件
FROM nginx:alpine as production-stage

# 复制构建好的文件到nginx目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]