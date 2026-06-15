#!/usr/bin/env python3
"""
Jenkins MCP Server — 将 Jenkins 操作暴露为 MCP Tools，供 AI Agent 调用。

用法:
  python jenkins_mcp_server.py
  或通过环境变量配置:
  JENKINS_URL=http://192.168.0.4:8080
  JENKINS_USERNAME=mcp-dev
  JENKINS_TOKEN=114144a252560bf1709ca15bf4a53ace19
  python jenkins_mcp_server.py
"""

import os
import sys
import json
import logging
from typing import Any

import jenkins
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ---------------------------------------------------------------------------
# 配置 — 优先级: 环境变量 > 硬编码默认值
# ---------------------------------------------------------------------------
JENKINS_URL = os.environ.get("JENKINS_URL", "http://192.168.0.4:8080")
JENKINS_USERNAME = os.environ.get("JENKINS_USERNAME", "mcp-dev")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "114144a252560bf1709ca15bf4a53ace19")

logging.basicConfig(
    level=logging.WARNING,  # 设 WARNING 避免 stdout 被日志污染（stdio MCP 要求）
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Jenkins 客户端
# ---------------------------------------------------------------------------
_server: jenkins.Jenkins | None = None


def get_server() -> jenkins.Jenkins:
    global _server
    if _server is None:
        _server = jenkins.Jenkins(
            url=JENKINS_URL,
            username=JENKINS_USERNAME,
            password=JENKINS_TOKEN,
        )
    return _server


# ---------------------------------------------------------------------------
# MCP Server 定义
# ---------------------------------------------------------------------------
app = Server("jenkins-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="jenkins_list_jobs",
            description="列出 Jenkins 中所有 Job 及其构建状态",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="jenkins_get_job",
            description="获取指定 Job 的详细信息（描述、参数、最近构建等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Job 名称",
                    },
                },
                "required": ["job_name"],
            },
        ),
        Tool(
            name="jenkins_build",
            description="触发一个 Jenkins Job 的构建（支持参数化构建）",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Job 名称",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "构建参数，键值对形式。例如: {\"version\": \"v2.5.1\", \"env\": \"staging\"}",
                    },
                },
                "required": ["job_name"],
            },
        ),
        Tool(
            name="jenkins_build_status",
            description="查询指定 Job 最近一次构建的状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Job 名称",
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "构建编号（可选，默认取最后一次构建）",
                    },
                },
                "required": ["job_name"],
            },
        ),
        Tool(
            name="jenkins_build_log",
            description="获取指定构建的控制台日志（默认返回尾部 50 行）",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_name": {
                        "type": "string",
                        "description": "Job 名称",
                    },
                    "build_number": {
                        "type": "integer",
                        "description": "构建编号（可选，默认取最后一次构建）",
                    },
                    "tail_lines": {
                        "type": "integer",
                        "description": "返回尾部 N 行（默认 50）",
                    },
                },
                "required": ["job_name"],
            },
        ),
        Tool(
            name="jenkins_queue",
            description="查看 Jenkins 构建队列中的等待任务",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        server = get_server()

        if name == "jenkins_list_jobs":
            return await _handle_list_jobs(server)

        elif name == "jenkins_get_job":
            return await _handle_get_job(server, arguments["job_name"])

        elif name == "jenkins_build":
            return await _handle_build(
                server,
                arguments["job_name"],
                arguments.get("parameters"),
            )

        elif name == "jenkins_build_status":
            return await _handle_build_status(
                server,
                arguments["job_name"],
                arguments.get("build_number"),
            )

        elif name == "jenkins_build_log":
            return await _handle_build_log(
                server,
                arguments["job_name"],
                arguments.get("build_number"),
                arguments.get("tail_lines", 50),
            )

        elif name == "jenkins_queue":
            return await _handle_queue(server)

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    except jenkins.JenkinsException as e:
        return [TextContent(type="text", text=f"Jenkins 错误: {e}")]
    except Exception as e:
        logger.exception("工具调用异常")
        return [TextContent(type="text", text=f"错误: {e}")]


# ---------------------------------------------------------------------------
# 工具处理函数
# ---------------------------------------------------------------------------


async def _handle_list_jobs(server: jenkins.Jenkins) -> list[TextContent]:
    jobs = server.get_all_jobs()
    if not jobs:
        return [TextContent(type="text", text="Jenkins 中没有任何 Job。")]

    lines = ["Jenkins Job 列表:"]
    for job in jobs:
        name = job.get("name", "?")
        color = job.get("color", "notbuilt")
        status_map = {
            "blue": "稳定",
            "blue_anime": "构建中",
            "red": "失败",
            "red_anime": "构建中(失败)",
            "yellow": "不稳定",
            "yellow_anime": "构建中(不稳定)",
            "aborted": "已中止",
            "disabled": "已禁用",
            "notbuilt": "未构建",
        }
        status = status_map.get(color, color)
        lines.append(f"  - {name} [{status}]")
    lines.append(f"\n共 {len(jobs)} 个 Job")
    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_get_job(server: jenkins.Jenkins, job_name: str) -> list[TextContent]:
    info = server.get_job_info(job_name)
    lines = [
        f"Job: {info.get('name', job_name)}",
        f"描述: {info.get('description', '(无)')}",
        f"URL: {info.get('url', '')}",
        f"可构建: {'是' if info.get('buildable') else '否'}",
        f"并发构建: {'是' if info.get('concurrentBuild') else '否'}",
    ]

    # 最近构建
    last_build = info.get("lastBuild")
    if last_build:
        lines.append(f"最近构建: #{last_build.get('number', '?')}")
    last_completed = info.get("lastCompletedBuild")
    if last_completed:
        lines.append(f"最近完成构建: #{last_completed.get('number', '?')}, 结果: {last_completed.get('result', '?')}")

    # 构建参数
    properties = info.get("property", [])
    for prop in properties:
        params = prop.get("parameterDefinitions")
        if params:
            lines.append("\n构建参数:")
            for p in params:
                default = p.get("defaultParameterValue", {})
                default_val = default.get("value", "(无默认值)") if default else "(无默认值)"
                lines.append(f"  - {p['name']} ({p['type']}): {p.get('description', '')} 默认={default_val}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_build(
    server: jenkins.Jenkins,
    job_name: str,
    parameters: dict | None = None,
) -> list[TextContent]:
    if parameters:
        # 参数化构建
        server.build_job(job_name, parameters=parameters)
        params_str = ", ".join(f"{k}={v}" for k, v in parameters.items())
        return [TextContent(
            type="text",
            text=f"✅ 已触发参数化构建: {job_name}\n参数: {params_str}\n请用 jenkins_build_status 查看进度。",
        )]
    else:
        server.build_job(job_name)
        return [TextContent(
            type="text",
            text=f"✅ 已触发构建: {job_name}\n请用 jenkins_build_status 查看进度。",
        )]


async def _handle_build_status(
    server: jenkins.Jenkins,
    job_name: str,
    build_number: int | None = None,
) -> list[TextContent]:
    if build_number is None:
        build_number = server.get_job_info(job_name)["lastBuild"]["number"]

    info = server.get_build_info(job_name, build_number)
    lines = [
        f"Job: {job_name}",
        f"构建编号: #{build_number}",
        f"结果: {info.get('result', '进行中...')}",
        f"时间戳: {info.get('timestamp', '?')}",
        f"持续时间: {info.get('duration', '?')} ms",
        f"URL: {info.get('url', '')}",
    ]

    # 构建参数
    actions = info.get("actions", [])
    for action in actions:
        params = action.get("parameters")
        if params:
            lines.append("\n构建参数:")
            for p in params:
                lines.append(f"  - {p['name']} = {p.get('value', '?')}")

    # 变更记录
    change_sets = info.get("changeSets", [])
    for cs in change_sets:
        items = cs.get("items", [])
        if items:
            lines.append(f"\n变更记录 ({len(items)} 条):")
            for item in items[:5]:  # 最多 5 条
                author = item.get("author", {}).get("fullName", "?")
                msg = item.get("msg", "")
                lines.append(f"  - {author}: {msg}")

    return [TextContent(type="text", text="\n".join(lines))]


async def _handle_build_log(
    server: jenkins.Jenkins,
    job_name: str,
    build_number: int | None = None,
    tail_lines: int = 50,
) -> list[TextContent]:
    if build_number is None:
        build_number = server.get_job_info(job_name)["lastBuild"]["number"]

    full_log = server.get_build_console_output(job_name, build_number)
    log_lines = full_log.splitlines()
    tail = log_lines[-tail_lines:] if len(log_lines) > tail_lines else log_lines

    header = f"=== {job_name} #{build_number} 控制台日志 (最后 {tail_lines} 行) ===\n"
    return [TextContent(type="text", text=header + "\n".join(tail))]


async def _handle_queue(server: jenkins.Jenkins) -> list[TextContent]:
    queue = server.get_queue_info()
    if not queue:
        return [TextContent(type="text", text="构建队列为空，无等待任务。")]

    lines = [f"构建队列 ({len(queue)} 个等待任务):"]
    for item in queue:
        task = item.get("task", {})
        lines.append(f"  - {task.get('name', '?')} (ID: {item.get('id', '?')}, 等待原因: {item.get('why', '?')})")

    return [TextContent(type="text", text="\n".join(lines))]


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
