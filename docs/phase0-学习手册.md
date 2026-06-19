# Phase 0 逐步学习手册

> 这份文档逐条记录 Phase 0（脚手架）里**每一步具体做了什么、动了哪个文件、敲了什么命令、作用是什么**。
> 每一节末尾有「🔍 可以问 AI 的问题」——把那些问题逐个拿去问 AI，就能把每一步的运行原理挖透。
>
> 阅读顺序建议：从上往下。带 ⭐ 的是初学者最该先搞懂的。

---

## 目录

- [0. 总体顺序回顾](#0-总体顺序回顾)
- [P0a · 后端那套（Docker）](#p0a--后端那套docker)
  - [步骤 1：.gitignore](#步骤-1gitignore)
  - [步骤 2：.env.example](#步骤-2envexample)
  - [步骤 3：backend/requirements.txt](#步骤-3backendrequirementstxt)
  - [步骤 4：backend/Dockerfile ⭐](#步骤-4backenddockerfile-)
  - [步骤 5：backend/app/main.py ⭐](#步骤-5backendappmainpy-)
  - [步骤 6：infra/postgres/init/01-create-langfuse-db.sql](#步骤-6infrapostgresinit01-create-langfuse-dbsql)
  - [步骤 7：docker-compose.yml ⭐](#步骤-7docker-composeyml-)
  - [步骤 8：启动与验证命令](#步骤-8启动与验证命令)
- [P0b · 前端 + CI](#p0b--前端--ci)
  - [步骤 9：frontend/package.json](#步骤-9frontendpackagejson)
  - [步骤 10：frontend/vite.config.js ⭐](#步骤-10frontendviteconfigjs-)
  - [步骤 11：index.html](#步骤-11indexhtml)
  - [步骤 12：src/main.js](#步骤-12srcmainjs)
  - [步骤 13：src/App.vue](#步骤-13srcappvue)
  - [步骤 14：src/router/index.js](#步骤-14srcrouterindexjs)
  - [步骤 15-16：两个占位页面](#步骤-15-16两个占位页面)
  - [步骤 17：backend/requirements-dev.txt](#步骤-17backendrequirements-devtxt)
  - [步骤 18-19：后端测试](#步骤-18-19后端测试)
  - [步骤 20：.github/workflows/ci.yml ⭐](#步骤-20githubworkflowsciyml-)
  - [步骤 21：README.md](#步骤-21readmemd)
  - [步骤 22：前端启动与验证命令](#步骤-22前端启动与验证命令)
- [排错记录（真实踩坑）](#排错记录真实踩坑)
- [全部"可问 AI"问题汇总](#全部可问-ai问题汇总)

---

## 0. 总体顺序回顾

Phase 0 = 搭脚手架，不写任何业务功能，只把基础设施立起来并验证能跑。分两小步：

- **P0a**：后端 5 个服务用 Docker 一键起 + 一个最小后端接口 `/health`。
- **P0b**：前端空壳页 + 自动测试 + CI（持续集成）骨架 + README。

每一步都遵循"先写、再实际运行验证、通过了才下一步"。

---

## P0a · 后端那套（Docker）

### 步骤 1：.gitignore

- **做了什么**：新建 `.gitignore`。
- **文件**：[.gitignore](../.gitignore)
- **作用**：告诉 git「哪些文件不要纳入版本管理」。比如 `.env`（含密钥）、`node_modules/`（体积巨大、可重新安装）、上传的音频文件（运行时数据）。
- **原理关键词**：版本控制、忽略规则、密钥不入库。
- 🔍 **可以问 AI 的问题**：
  - `.gitignore` 的匹配规则语法是怎样的？`*.log`、`__pycache__/`、`/dist` 这几种写法分别匹配什么？
  - 为什么密钥文件绝对不能提交到 git？已经误提交了怎么彻底清除历史？

### 步骤 2：.env.example

- **做了什么**：新建环境变量样例文件。
- **文件**：[.env.example](../.env.example)
- **作用**：列出项目需要的所有配置项（数据库地址、各服务地址、LLM/ASR 的 key 等），但**不填真实密钥**。真正用时复制成 `.env`。`.env` 被 gitignore 忽略，`.env.example` 入库供别人参考。
- **原理关键词**：配置与代码分离（12-Factor App）、环境变量。
- 🔍 **可以问 AI 的问题**：
  - 为什么要把配置放进环境变量，而不是写死在代码里？这和「12-Factor App」的哪条原则有关？
  - `DATABASE_URL=postgresql://meeting:meeting_pw@postgres:5432/meeting` 这一串里每一段分别是什么含义？为什么主机名是 `postgres` 而不是 `localhost`？

### 步骤 3：backend/requirements.txt

- **做了什么**：声明后端运行时的 Python 依赖。
- **文件**：[backend/requirements.txt](../backend/requirements.txt)
- **作用**：列出 `fastapi`、`uvicorn`、`pydantic-settings` 三个包及其**精确版本号**。装环境时一条命令按这个清单安装。
- **原理关键词**：依赖管理、版本锁定、可复现构建。
- 🔍 **可以问 AI 的问题**：
  - `fastapi==0.115.6` 里的 `==` 和 `>=`、`~=` 有什么区别？为什么生产项目倾向锁死精确版本？
  - `uvicorn` 和 `fastapi` 分别扮演什么角色？为什么需要两个？（提示：一个是框架，一个是 ASGI 服务器）

### 步骤 4：backend/Dockerfile ⭐

- **做了什么**：写「如何把后端打包成一个 Docker 镜像」的说明书。
- **文件**：[backend/Dockerfile](../backend/Dockerfile)
- **作用**：从 `python:3.12-slim` 基础镜像开始，先拷依赖清单并安装，再拷源码，最后用 `uvicorn` 启动。
- **关键设计**：**先 COPY requirements.txt 装依赖，再 COPY 源码**——利用 Docker 的「层缓存」：源码常改、依赖不常改，这样改代码重建镜像时不必重新装依赖。
- **原理关键词**：镜像、镜像层（layer）、构建缓存、基础镜像。
- 🔍 **可以问 AI 的问题**：
  - Docker「镜像（image）」和「容器（container）」的区别是什么？用一个比喻说明。
  - Dockerfile 的每条指令（FROM/WORKDIR/COPY/RUN/CMD/EXPOSE）分别做什么？为什么 `RUN pip install` 会单独成一层？
  - 为什么调换 COPY 顺序就能加速重建？「层缓存」是怎么判断某一层能不能复用的？
  - `slim` 镜像和完整镜像、`alpine` 镜像有什么取舍？

### 步骤 5：backend/app/main.py ⭐

- **做了什么**：写后端的程序入口，目前只有一个健康检查接口。
- **文件**：[backend/app/main.py](../backend/app/main.py)
- **作用**：创建一个 FastAPI 应用，暴露 `GET /health`（返回 `{"status":"ok"}`）和 `GET /`。
- **关键设计**：`/health` 故意**极简**——不查数据库、不依赖外部服务，只回答「进程还活着吗」。因为编排系统（docker/k8s）靠它判断要不要重启服务。
- **原理关键词**：Web 框架、路由（route）、健康检查、ASGI。
- 🔍 **可以问 AI 的问题**：
  - `@app.get("/health")` 这个装饰器到底做了什么？一个 HTTP 请求从进来到返回，FastAPI 内部经历了哪些步骤？
  - 为什么健康检查接口不能去查数据库？如果查了会引发什么问题？
  - 什么是 ASGI？它和老的 WSGI 有什么区别？为什么处理流式/异步要用 ASGI？
  - FastAPI 是怎么自动生成 `/docs` 这个交互文档页的？

### 步骤 6：infra/postgres/init/01-create-langfuse-db.sql

- **做了什么**：写一段开机自动执行的 SQL，在同一个 Postgres 实例里多建一个 `langfuse` 库。
- **文件**：[infra/postgres/init/01-create-langfuse-db.sql](../infra/postgres/init/01-create-langfuse-db.sql)
- **作用**：让应用数据（`meeting` 库）和可观测数据（`langfuse` 库）分开存，又不用多起一个 Postgres 容器。
- **关键机制**：Postgres 官方镜像会在**数据卷首次初始化时**，自动执行 `/docker-entrypoint-initdb.d/` 目录下的脚本。
- **原理关键词**：数据库实例 vs 数据库、初始化脚本、数据卷首次初始化。
- 🔍 **可以问 AI 的问题**：
  - 「一个 Postgres 实例」和「一个数据库」是什么关系？一个实例里能有多个数据库吗？
  - `/docker-entrypoint-initdb.d/` 的脚本什么时候执行、什么时候**不**执行？（提示：和数据卷是否已存在数据有关）
  - 如果我已经 `docker compose up` 过一次再改这个 SQL，它会重新执行吗？为什么？

### 步骤 7：docker-compose.yml ⭐

- **做了什么**：用一个文件描述 5 个服务怎么一起启动。
- **文件**：[docker-compose.yml](../docker-compose.yml)
- **作用**：定义 backend / postgres / redis / qdrant / langfuse 五个服务，各自的镜像、端口映射、环境变量、数据卷、依赖关系。一句 `docker compose up` 全部拉起。
- **关键设计**：
  - `depends_on` + `condition: service_healthy`：backend 要**等 postgres 真正能连**才启动（靠 healthcheck 判断），不是容器一启动就冲上去。
  - `ports: "8000:8000"`：把容器内端口映射到宿主机，浏览器才能访问。
  - `volumes: pgdata`：数据存在「命名卷」里，容器删了数据还在。
- **原理关键词**：服务编排、端口映射、数据卷（volume）、容器网络、依赖与健康检查。
- 🔍 **可以问 AI 的问题**：
  - `ports: "8000:8000"` 这个「宿主机:容器」映射具体是怎么工作的？如果写成 `"9000:8000"` 会怎样？
  - 容器之间是怎么互相通信的？为什么 backend 连 postgres 用服务名 `postgres` 当主机名就行？（容器网络 / DNS）
  - `volumes`（命名卷）和「bind mount（挂本地目录）」有什么区别？`docker compose down` 和 `down -v` 的差别？
  - `depends_on` 只写服务名 vs 加 `condition: service_healthy`，行为差在哪？为什么「容器启动了」不等于「服务可用了」？
  - healthcheck 的 `test`、`interval`、`retries` 分别是什么意思？

### 步骤 8：启动与验证命令

- **做了什么 & 敲了什么**（按顺序）：
  1. `cp .env.example .env` —— 生成真正用的环境变量文件。
  2. `docker compose config --quiet` —— **先校验** compose 文件语法对不对（不真启动）。
  3. `docker compose up -d --build` —— 构建并后台启动全部服务。（`-d`=后台 detached，`--build`=顺便重新构建镜像）
  4. `docker compose ps` —— 查看 5 个服务状态，确认都是 `Up`/`healthy`。
  5. `curl http://localhost:8000/health` 等 —— 实际打接口，确认真能访问。
- **原理关键词**：声明式配置校验、detached 模式、健康状态。
- 🔍 **可以问 AI 的问题**：
  - `docker compose up` 不加 `-d` 和加 `-d` 有什么区别？日志去哪了？
  - `docker compose up`、`start`、`restart`、`down` 分别在什么场景用？
  - `curl -s -o /dev/null -w "%{http_code}"` 这串参数每一段是什么意思？

---

## P0b · 前端 + CI

### 步骤 9：frontend/package.json

- **做了什么**：声明前端项目的元信息、依赖、脚本命令。
- **文件**：[frontend/package.json](../frontend/package.json)
- **作用**：`dependencies` 列运行时要用的包（vue / vue-router / pinia / element-plus），`devDependencies` 列只在开发/构建时要的（vite 等）。`scripts` 定义 `npm run dev`、`npm run build` 这些命令。
- **原理关键词**：npm、依赖 vs 开发依赖、语义化版本（`^2.8.8`）。
- 🔍 **可以问 AI 的问题**：
  - `dependencies` 和 `devDependencies` 的区别？为什么要分？打包发布时哪些会被带上？
  - `^2.8.8`、`~2.8.8`、`2.8.8` 三种版本写法分别允许升级到哪个范围？
  - `package.json` 和 `package-lock.json` 是什么关系？后者有什么用？

### 步骤 10：frontend/vite.config.js ⭐

- **做了什么**：配置前端构建工具 Vite，重点是**开发代理**。
- **文件**：[frontend/vite.config.js](../frontend/vite.config.js)
- **作用**：dev 服务器跑在 5173 端口；凡是 `/api` 开头的请求，转发给后端 `http://localhost:8000`，并把 `/api` 前缀去掉（`/api/health` → 后端 `/health`）。
- **关键设计**：用代理绕开浏览器的「跨域（CORS）」限制；上线时把这层换成 nginx，前端代码不用改。
- **原理关键词**：开发服务器、跨域 CORS、反向代理、路径重写。
- 🔍 **可以问 AI 的问题**：
  - 「跨域（CORS）」到底是什么、为什么浏览器要有这个限制？不解决会报什么错？
  - Vite 的开发代理是怎么工作的——请求实际是浏览器直接发给后端，还是先到 Vite 再转发？
  - `changeOrigin: true` 是干嘛的？`rewrite` 那行正则 `/^\/api/` 匹配的是什么？
  - 上线后用 nginx 做反向代理，配置上和这个 dev 代理是对应的吗？

### 步骤 11：index.html

- **做了什么**：前端唯一的 HTML 入口页。
- **文件**：[frontend/index.html](../frontend/index.html)
- **作用**：提供一个挂载点 `<div id="app">`，并用 `<script type="module">` 加载 `main.js`。Vue 会把整个应用渲染进那个 div。
- **原理关键词**：单页应用（SPA）、挂载点、ES Module。
- 🔍 **可以问 AI 的问题**：
  - 什么是「单页应用（SPA）」？为什么整个站点只有一个 `index.html`？
  - `<script type="module">` 和普通 `<script>` 有什么区别？为什么 Vite 能靠它做到「启动飞快」？

### 步骤 12：src/main.js

- **做了什么**：前端的 JS 入口，组装整个应用。
- **文件**：[frontend/src/main.js](../frontend/src/main.js)
- **作用**：`createApp(App)` 创建应用，然后 `.use()` 挂上 Pinia（状态管理）、router（路由）、Element Plus（组件库），最后 `.mount('#app')` 渲染到页面。
- **原理关键词**：应用实例、插件机制（`use`）、挂载。
- 🔍 **可以问 AI 的问题**：
  - `app.use(xxx)` 这个「插件」机制是怎么工作的？Pinia / router 是怎么被「装」进 Vue 的？
  - Pinia（状态管理）解决什么问题？什么时候才需要它，而不是把数据放在组件里？

### 步骤 13：src/App.vue

- **做了什么**：根组件，定义整体布局（顶部导航 + 内容区）。
- **文件**：[frontend/src/App.vue](../frontend/src/App.vue)
- **作用**：用 Element Plus 的 `el-container`/`el-header`/`el-menu` 搭出顶部导航，`<router-view />` 是「内容占位坑」——当前路由对应的页面渲染在这里。
- **原理关键词**：组件、单文件组件（SFC）、`<router-view>`、响应式（`computed`）。
- 🔍 **可以问 AI 的问题**：
  - 一个 `.vue` 单文件组件里的 `<script setup>`、`<template>`、`<style>` 三块分别负责什么？
  - `<router-view />` 是怎么知道该显示哪个页面的？
  - `computed(() => route.path)` 这个「计算属性」和普通变量有什么区别？什么是「响应式」？

### 步骤 14：src/router/index.js

- **做了什么**：定义前端路由表。
- **文件**：[frontend/src/router/index.js](../frontend/src/router/index.js)
- **作用**：把 URL 路径映射到页面组件——`/` → 上传页，`/board` → 看板页。
- **原理关键词**：前端路由、`createWebHistory`（history 模式）。
- 🔍 **可以问 AI 的问题**：
  - 「前端路由」和「后端路由」有什么不同？为什么单页应用切页面不刷新整页？
  - `createWebHistory`（history 模式）和 `createWebHashHistory`（hash 模式，URL 带 `#`）有什么区别？history 模式上线要注意什么（刷新 404 问题）？

### 步骤 15-16：两个占位页面

- **做了什么**：写 `UploadView.vue`（上传页）和 `BoardView.vue`（看板页）两个占位组件。
- **文件**：[UploadView.vue](../frontend/src/views/UploadView.vue) ｜ [BoardView.vue](../frontend/src/views/BoardView.vue)
- **作用**：现在是占位内容。上传页放了个「测试后端连通」按钮，点了用 `fetch('/api/health')` 打后端，验证整条链路。看板页放了「决策/待办/风险」三个空卡片示意结构。
- **原理关键词**：`fetch`、async/await、事件绑定（`@click`）。
- 🔍 **可以问 AI 的问题**：
  - `fetch('/api/health')` 返回的为什么要 `await res.json()` 再用？Promise / async-await 是怎么回事？
  - 这个 `/api/health` 请求，从点击按钮到拿到结果，完整经过了哪些环节？（串起步骤 10 的代理）

### 步骤 17：backend/requirements-dev.txt

- **做了什么**：声明「开发/CI 时才用」的 Python 依赖。
- **文件**：[backend/requirements-dev.txt](../backend/requirements-dev.txt)
- **作用**：`-r requirements.txt` 先包含运行时依赖，再加上 `pytest`（测试）、`httpx`（测试客户端依赖）、`ruff`（代码检查）。这些线上跑服务不需要，所以和运行时依赖分开。
- **原理关键词**：开发依赖隔离、依赖文件递归引用（`-r`）。
- 🔍 **可以问 AI 的问题**：
  - 为什么要把测试/lint 工具和运行时依赖分成两个文件？线上镜像装它们有什么坏处？
  - `ruff` 是干嘛的？「linter」和「formatter」是一回事吗？

### 步骤 18-19：后端测试

- **做了什么**：写一个针对 `/health` 的自动化测试。
- **文件**：[backend/tests/test_health.py](../backend/tests/test_health.py)（还有空的 `tests/__init__.py` 让它成为一个包）
- **作用**：用 FastAPI 的 `TestClient` 在**内存里**把整个应用跑起来，发一个 `GET /health` 请求，断言状态码是 200、返回是 `{"status":"ok"}`。不用真启动服务器，所以快、也不依赖 docker。
- **原理关键词**：单元/接口测试、断言（assert）、TestClient、pytest 发现机制。
- 🔍 **可以问 AI 的问题**：
  - `TestClient` 不真正监听端口，是怎么把请求送进 FastAPI 应用的？
  - pytest 是怎么「找到」并运行测试的？为什么函数名要以 `test_` 开头、文件要叫 `test_*.py`？
  - `assert resp.json() == {"status": "ok"}` 失败时 pytest 会给出什么信息？

### 步骤 20：.github/workflows/ci.yml ⭐

- **做了什么**：写 GitHub Actions 的 CI 流水线。
- **文件**：[.github/workflows/ci.yml](../.github/workflows/ci.yml)
- **作用**：每次 push 或提 PR 时，GitHub 自动起两个任务——后端任务跑 `ruff check` + `pytest`；前端任务跑 `npm install` + `npm run build`。任一失败就标红，拦住坏代码。
- **关键设计**：`on:` 定义触发时机，`jobs:` 定义并行任务，每个 job 有一串 `steps`（拉代码 → 装环境 → 跑检查）。Phase 4 会在这里加 eval 门禁。
- **原理关键词**：CI/CD、流水线、触发器（trigger）、Job/Step、Runner。
- 🔍 **可以问 AI 的问题**：
  - CI（持续集成）和 CD（持续部署）分别指什么？CI 解决了团队协作里的什么痛点？
  - 这个 yml 里 `on`、`jobs`、`steps`、`runs-on`、`uses` 各是什么含义？
  - `uses: actions/checkout@v4` 这种「现成 action」是从哪来的、怎么复用别人写好的步骤？
  - 「CI 门禁（gate）」是什么意思？怎么配置成「检查不过就不许合并」？

### 步骤 21：README.md

- **做了什么**：写项目说明书（架构图、怎么启动、目录结构）。
- **文件**：[README.md](../README.md)
- **作用**：让任何人（包括面试官）clone 下来能看懂怎么跑。里面用 Mermaid 画了架构图。
- 🔍 **可以问 AI 的问题**：
  - 一份好的开源/项目 README 应该包含哪些部分？面试官会从 README 看出什么？
  - Mermaid 是什么？`flowchart TD` 的语法怎么读？

### 步骤 22：前端启动与验证命令

- **做了什么 & 敲了什么**：
  1. `npm install` —— 按 package.json 下载所有依赖到 `node_modules/`。
  2. `npm run build` —— 用 Vite 把前端打包成生产用的静态文件（验证能构建）。
  3. `npm run dev` —— 启动开发服务器（5173），带热更新。
  4. 用 `Invoke-WebRequest http://localhost:5173/api/health` 探针，验证「前端→代理→后端」整条链路通。
- **原理关键词**：依赖安装、生产构建（build）、开发服务器、热更新（HMR）。
- 🔍 **可以问 AI 的问题**：
  - `npm run dev`（开发）和 `npm run build`（构建）产出的东西有什么本质区别？为什么开发时不直接用 build 的结果？
  - 什么是「热更新（HMR）」？为什么改一行代码页面能局部刷新而不整页重载？
  - `node_modules` 为什么动辄几百 MB、还不进 git？

---

## 排错记录（真实踩坑）

> 这两个 bug 是这次真实遇到并解决的，**面试时讲排错过程比讲功能更显功力**。

### 坑 1：国内拉不到 Docker 镜像（TLS handshake timeout）

- **现象**：`docker compose up` 拉 `qdrant/qdrant` 时报 `net/http: TLS handshake timeout`。
- **原因**：国内直连 Docker Hub（registry-1.docker.io）网络不稳，握手超时。
- **怎么定位**：`docker images` 看本地已有哪些、`docker info` 看有没有配镜像加速器（结果是没配）。
- **解决**：① 开代理后用 `docker pull redis:7-alpine` 做连通性探针，确认能拉了；② 把 compose 里 `qdrant/qdrant:latest` 钉成本地已有的 `v1.15.1`，少拉一个、也更可复现。
- 🔍 **可以问 AI 的问题**：
  - Docker 镜像是从哪里拉的？什么是 registry、镜像加速器（mirror）？国内常用哪些？
  - 为什么生产环境不该用 `latest` 标签？「可复现构建」为什么重要？
  - Docker Desktop 怎么配 HTTP 代理 / registry mirror？

### 坑 2：中文 Windows 让 pip 解码崩溃（UnicodeDecodeError）

- **现象**：`pip install -r requirements-dev.txt` 报 `'gbk' codec can't decode byte 0x80`。
- **原因**：Windows 中文系统默认编码是 GBK/cp936；旧版 pip 用 GBK 去读我那个**带 UTF-8 中文注释**的依赖文件，UTF-8 的中文字节不是合法 GBK → 解码失败。（同样的文件在 Docker 里没问题，因为容器是 UTF-8 环境。）
- **解决**：设环境变量 `PYTHONUTF8=1` 强制 Python 按 UTF-8 读文件，并升级 pip，再装成功。
- 🔍 **可以问 AI 的问题**：
  - 「字符编码」是什么？UTF-8 和 GBK/cp936 的区别？为什么同一串字节用不同编码读会乱码/报错？
  - `PYTHONUTF8=1` 这个开关具体改变了 Python 的什么行为？
  - 为什么同样的文件在 Linux 容器里没事、在中文 Windows 上就崩？「locale（区域设置）」是怎么影响默认编码的？

---

## 全部"可问 AI"问题汇总

把下面这些逐条问 AI（建议一次问一题、追问到懂），就能把 Phase 0 的原理全打通。按主题归类：

**Docker / 容器（最核心）**
1. 镜像和容器的区别？用比喻说明。
2. Dockerfile 每条指令的作用？为什么 COPY 顺序影响构建速度（层缓存）？
3. 端口映射 `8000:8000` 怎么工作？
4. 容器之间怎么通信、为什么用服务名当主机名？
5. 数据卷（volume）是什么？`down` 和 `down -v` 的区别？
6. `depends_on` 加不加 `service_healthy` 差在哪？为什么「容器起了 ≠ 服务可用」？
7. registry / 镜像加速器是什么？为什么别用 `latest`？

**后端 / Web**
8. 一个 HTTP 请求进 FastAPI 后内部经历什么？
9. 健康检查接口为什么要极简、不查 DB？
10. ASGI vs WSGI？为什么流式/异步要 ASGI？
11. `requirements.txt` 版本号 `==`/`>=`/`~=` 区别？为什么锁版本？

**前端**
12. 跨域 CORS 是什么？开发代理怎么绕开它？
13. 单页应用（SPA）是什么？前端路由 vs 后端路由？
14. Vue 单文件组件三块结构？什么是「响应式」？
15. `dependencies` vs `devDependencies`？`package-lock.json` 干嘛的？
16. 开发服务器 vs 生产构建的区别？什么是热更新（HMR）？

**测试 / CI**
17. `TestClient` 怎么不开端口就测接口？
18. pytest 怎么发现测试？命名规则为什么重要？
19. CI/CD 是什么？这个 yml 的 on/jobs/steps 怎么读？
20. 「CI 门禁」怎么拦住坏代码？

**编码 / 环境**
21. 字符编码（UTF-8 vs GBK）？为什么会乱码/报错？
22. locale 怎么影响默认编码？`PYTHONUTF8=1` 改了什么？

---

> 📌 用法建议：不要一次性把 22 题全问完。挑你最不懂的主题（建议从 **Docker** 开始），一题一题问，每题都追问「能不能再举个例子」「如果不这样会怎样」，直到你能合上文档自己讲一遍。这正是项目文档第 8 节说的「能离开代码在白板上讲明白 = 真懂了」。
