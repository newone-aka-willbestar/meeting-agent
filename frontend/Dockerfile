# ---------- 构建阶段：用 node 把前端打包成静态文件 ----------
FROM node:20-slim AS build
WORKDIR /app

# npm 源可切换：阿里云部署时传 --build-arg NPM_REGISTRY=https://registry.npmmirror.com，免梯子
ARG NPM_REGISTRY=https://registry.npmjs.org

COPY package.json package-lock.json ./
RUN npm config set registry $NPM_REGISTRY && npm install --no-fund --no-audit
COPY . .
# 部署时会议 app 挂在 /meeting/ 子路径下，所以 base 设成 /meeting/
RUN npm run build -- --base=/meeting/

# ---------- 运行阶段：nginx 托管 主页(/) + 会议 app(/meeting/) + 反代(/api) ----------
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
# 作品集主页放根目录
COPY portfolio/index.html /usr/share/nginx/html/index.html
# 会议 app 打包产物放 /meeting 子目录
COPY --from=build /app/dist /usr/share/nginx/html/meeting
EXPOSE 80
