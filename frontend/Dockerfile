# ---------- 构建阶段：用 node 把前端打包成静态文件 ----------
FROM node:20-slim AS build
WORKDIR /app

# npm 源可切换：阿里云部署时传 --build-arg NPM_REGISTRY=https://registry.npmmirror.com，免梯子
ARG NPM_REGISTRY=https://registry.npmjs.org

COPY package.json package-lock.json ./
RUN npm config set registry $NPM_REGISTRY && npm install --no-fund --no-audit
COPY . .
RUN npm run build

# ---------- 运行阶段：nginx 托管静态页 + 反代 /api 到后端 ----------
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
