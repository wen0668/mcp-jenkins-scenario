import requests
import json
import os

# ======================================================================
# === JENKINS 配置信息 (请确保这些信息是正确的!) ===
# ======================================================================
# 目标 Jenkins URL
JENKINS_URL = "http://192.168.0.4:8080"
# 用户名
JENKINS_USERNAME = "mcp-dev"
# 推荐使用 API Token 而非密码
JENKINS_TOKEN = "114144a252560bf1709ca15bf4a53ace19"
# ======================================================================

# 正确的 Jenkins API 端点是 /api/json，/job 是用于创建/操作具体 Job 的路径
# tree 参数只取需要的字段，减少不必要的数据传输
JOB_LIST_ENDPOINT = f"{JENKINS_URL}/api/json?tree=jobs[name,url,color]"

def list_jenkins_jobs():
    """
    使用用户名和API Token连接 Jenkins API，列出所有可用的项目/Job列表。
    """
    print(f"[*] 尝试连接 Jenkins: {JENKINS_URL}")
    
    # 使用 Token 进行认证的认证机制 (Basic Auth 的密码部分替换为 Token)
    auth = (JENKINS_USERNAME, JENKINS_TOKEN)
    
    try:
        # 发起GET请求获取Job列表 (正确的端点是 /api/json)
        response = requests.get(
            JOB_LIST_ENDPOINT, 
            auth=auth, 
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        # 检查HTTP状态码
        response.raise_for_status()
        
        # 解析JSON响应 — Jenkins 返回的是 {"jobs": [...]}，不是直接的数组
        data = response.json()
        jobs = data.get("jobs", [])
        
        print("\n================================")
        print("🎉 成功获取 Jenkins Job 列表 🎉")
        print("===========================================")
        
        # 遍历并打印每个Job的名称和状态
        job_count = 0
        for job in jobs:
            job_name = job.get("name", "名称未知")
            job_url = job.get("url", "")
            job_color = job.get("color", "")
            # color 反映构建状态: blue=成功, red=失败, blue_anime=构建中, ...
            status_map = {
                "blue": "✅ 稳定",
                "blue_anime": "🔄 构建中",
                "red": "❌ 失败",
                "red_anime": "🔄 构建中(失败)",
                "yellow": "⚠️ 不稳定",
                "yellow_anime": "🔄 构建中(不稳定)",
                "aborted": "⏹️ 已中止",
                "disabled": "🚫 已禁用",
                "notbuilt": "⬜ 未构建",
            }
            status = status_map.get(job_color, f"({job_color})")
            print(f"  - {job_name}  {status}")
            job_count += 1
            
        print(f"\n✅ 总共发现 {job_count} 个项目/Job。")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP 错误发生: {e}")
        if response.status_code == 401:
            print("   >>> 提示：认证失败 (401 Unauthorized)。请检查JENKINS_USERNAME和JENKINS_TOKEN是否正确。")
        elif response.status_code == 403:
            print("   >>> 提示：权限不足 (403 Forbidden)。请确认您的用户是否具有读取项目列表的权限。")
        elif response.status_code == 404:
            print("   >>> 提示：无法访问该URL (404)。请确认JENKINS_URL是否正确，以及该API端点是否支持。")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接错误：无法连接到Jenkins服务器。")
        print("   >>> 请检查JENKINS_URL是否正确，网络是否通畅，以及Jenkins服务是否正在运行。")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 发生未知请求错误: {e}")

if __name__ == "__main__":
    list_jenkins_jobs()