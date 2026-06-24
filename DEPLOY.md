# 部署到阿里云服务器

把项目跑到一台阿里云 Linux 服务器上，拿到一个 `http://公网IP` 的在线 demo 链接。
全程在服务器终端复制粘贴即可。

---

## 0. 买服务器

- 产品：**轻量应用服务器**（最简单）或 ECS
- 镜像/系统：**Ubuntu 22.04**
- 配置：**≥ 2 核 4G**（2G 跑 6 个容器会很吃力）
- 买完在控制台**安全组/防火墙**里**放行 80 端口**（HTTP）和 22（SSH，通常默认开）

记下服务器的**公网 IP**。

---

## 1. 登录服务器

用阿里云控制台的「远程连接」，或本地终端：
```bash
ssh root@你的公网IP
```

## 2. 加 4G swap（2 核 2G 服务器必做，否则构建会被内存杀掉）

```bash
fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
free -h   # 看到 Swap 有 4G 即成功
```

## 3. 装 Docker

```bash
curl -fsSL https://get.docker.com | bash
systemctl enable --now docker
docker version   # 能打印版本即成功
```

## 4. 配 Docker 镜像加速（拉镜像快、免梯子）

阿里云每个账号有专属加速地址：控制台搜「容器镜像服务」→ 镜像加速器，复制你的地址，替换下面的 `<你的加速地址>`：
```bash
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{ "registry-mirrors": ["<你的加速地址>"] }
EOF
systemctl restart docker
```

## 5. 拉代码

```bash
apt-get update && apt-get install -y git
git clone https://github.com/newone-aka-willbestar/meeting-agent.git
cd meeting-agent
```

## 6. 配置 .env

```bash
cp .env.prod.example .env
vi .env        # 改两处：POSTGRES_PASSWORD 设强密码、DASHSCOPE_API_KEY 填你的百炼 key
```
（vi 用法：`i` 进编辑，改完按 `Esc`，输入 `:wq` 回车保存退出。）

## 7. 一键起

```bash
docker compose -f docker-compose.prod.yml up -d --build
```
首次构建装依赖 + 打包前端，2G 服务器约 10-20 分钟（有 swap 撑着，慢但不会崩）。完成后：
```bash
docker compose -f docker-compose.prod.yml ps     # 看服务状态
```

## 8. 访问

- 作品集主页：**`http://你的公网IP`** —— 三个项目并排展示
- 会议 demo：**`http://你的公网IP/meeting/`** —— 上传音频看转写/决策待办风险/纪要周报/检索

把主页地址写进简历即可。

---

## 常用运维命令

```bash
# 看日志
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f worker

# 改了代码后重新部署
git pull && docker compose -f docker-compose.prod.yml up -d --build

# 停 / 启
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

## 排错

| 现象 | 处理 |
|---|---|
| 打不开网页 | 确认安全组放行了 80；`... ps` 看 web 是否 Up |
| 上传后一直 processing/failed | `logs worker` 看报错（多半是 DASHSCOPE_API_KEY 没填对） |
| 构建很慢/失败 | 确认第 3 步镜像加速配好；服务器内存是否够（≥4G） |
| 内存不足被 kill | 升配到 4G，或加 swap |

## 上线后建议

- 简历项目名后挂 `http://公网IP`；有域名可以解析过来、再上 HTTPS。
- ⚠️ 演示完把百炼 key 用量看一眼；长期挂着建议设 RAM/调用上限。
