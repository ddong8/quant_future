# 多阶段构建 - 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install && npm install -D sass-embedded

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