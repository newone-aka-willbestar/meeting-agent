"""自写 MCP server（护城河）。

用官方 MCP Python SDK 的 FastMCP，把核心能力暴露成 3 个标准 tool：
  - create_todo            创建待办，写入任务系统
  - search_meeting_history 跨会检索历史会议片段
  - get_minutes            获取某场会议的纪要

它是个"协议适配器"：自己不碰数据库，全部转调后端 FastAPI（REST）。
这样任何兼容 MCP 的 client（你的 agent、Claude Desktop）都能发现并调用这些工具。

传输用 stdio（FastMCP.run 默认）——Claude Desktop 会把本脚本当子进程拉起、用 stdio 通信。
连接方法见同目录 README.md。"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

# 后端地址。trust_env=False：忽略系统代理，避免本机代理劫持 localhost。
BACKEND_URL = os.environ.get("MCP_BACKEND_URL", "http://localhost:8000")
_client = httpx.Client(base_url=BACKEND_URL, trust_env=False, timeout=30.0)

mcp = FastMCP("meeting-agent")


@mcp.tool()
def create_todo(
    assignee: str,
    content: str,
    ddl: str | None = None,
    meeting_id: int | None = None,
) -> str:
    """创建一条待办并写入团队任务系统。

    参数：
        assignee: 负责人
        content: 待办内容
        ddl: 截止时间（可选）
        meeting_id: 来源会议 id（可选）
    """
    resp = _client.post(
        "/todos",
        json={
            "assignee": assignee,
            "content": content,
            "ddl": ddl,
            "meeting_id": meeting_id,
            "source": "mcp",
        },
    )
    resp.raise_for_status()
    todo = resp.json()
    return f"已创建待办 #{todo['id']}：{todo['assignee']} - {todo['content']}（ddl={todo['ddl']}）"


@mcp.tool()
def search_meeting_history(query: str, top_k: int = 5) -> str:
    """跨会检索历史会议片段，回答『上次关于 X 我们定了什么』这类问题。

    参数：
        query: 查询内容
        top_k: 返回条数（默认 5）
    """
    resp = _client.get("/search", params={"q": query, "top_k": top_k})
    resp.raise_for_status()
    results = resp.json()["results"]
    if not results:
        return "没有找到相关的历史会议片段。"
    return "\n".join(
        f"[会议{r['meeting_id']}] {r['text']}" for r in results
    )


@mcp.tool()
def get_minutes(meeting_id: int) -> str:
    """获取某场会议的纪要（markdown）。"""
    resp = _client.get(f"/meetings/{meeting_id}/extraction")
    if resp.status_code == 404:
        return f"会议 {meeting_id} 的纪要尚未生成。"
    resp.raise_for_status()
    return resp.json().get("minutes") or "（该会议暂无纪要）"


if __name__ == "__main__":
    mcp.run()  # 默认 stdio 传输
