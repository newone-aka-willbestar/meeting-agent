# 自写 MCP Server

把会议数字员工的核心能力暴露成 **MCP 标准工具**，可被任何 MCP client（你的 agent、**Claude Desktop**）连接调用。

## 暴露的工具

| tool | 作用 | 转调的后端接口 |
|---|---|---|
| `create_todo` | 创建待办写入任务系统 | `POST /todos` |
| `search_meeting_history` | 跨会检索历史会议片段 | `GET /search` |
| `get_minutes` | 取某场会议的纪要 | `GET /meetings/{id}/extraction` |

设计：MCP server 是**协议适配器**，自己不碰数据库，全部转调后端 FastAPI。
传输用 **stdio**（Claude Desktop 把本脚本当子进程拉起，用标准输入输出通信）。

## 本地准备

```powershell
# 后端要先起着（提供 REST 接口）
cd D:\meeting_agent
docker compose up -d

# 给 MCP server 建独立 venv 装依赖
cd D:\meeting_agent\mcp-server
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 接入 Claude Desktop（演示炸点）

编辑 Claude Desktop 配置文件（Windows）：
`%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "meeting-agent": {
      "command": "D:\\meeting_agent\\mcp-server\\.venv\\Scripts\\python.exe",
      "args": ["D:\\meeting_agent\\mcp-server\\server.py"],
      "env": { "MCP_BACKEND_URL": "http://localhost:8000" }
    }
  }
}
```

保存后重启 Claude Desktop，就能在对话里直接让它调用这三个工具
（例如："帮我查一下上次关于支付模块我们定了什么"会触发 `search_meeting_history`）。

## 面试要点

- **MCP 是什么**：标准协议，把能力暴露成 tools，任何兼容 client 都能发现并调用。
- **比"直接给函数"强在哪**：通用插头——同一个 server 既被自家 agent 用、也被 Claude Desktop 等通用 client 用。
- **工具发现（discovery）**：client 连上后通过协议握手拿到工具清单（名字/参数 schema/描述），再按需调用。
- **为什么能被 Claude Desktop 连上**：因为遵循 MCP 协议 + stdio 传输，Claude Desktop 作为通用 MCP host 即可拉起并通信。
