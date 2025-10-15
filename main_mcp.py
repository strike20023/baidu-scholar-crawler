from fastmcp import FastMCP
import json
import subprocess
import shlex
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any
import logging

# 可选：全局 logging 补充 ctx
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="scholar-crawler(baidu)",
    host="0.0.0.0",
    port=8899
)

# 辅助函数：运行单个 query 的子进程（供 Executor 调用）
def run_single_query(query: str) -> Dict[str, Any]:
    """在子进程中运行 crawler_worker.py，返回解析后的 dict"""
    cmd = f"python crawler_worker.py {shlex.quote(query)}"
    logging.info(f"子进程执行: {cmd}")  # 子进程日志
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            error = result.stderr.strip() or "Unknown error"
            return {"query": query, "status": "error", "message": error}
        
        output = result.stdout.strip()
        try:
            data = json.loads(output)
            return {"query": query, "status": "success", "data": data}
        except json.JSONDecodeError:
            return {"query": query, "status": "error", "message": "Invalid JSON output"}
    except subprocess.TimeoutExpired:
        return {"query": query, "status": "error", "message": "Timeout"}
    except Exception as e:
        return {"query": query, "status": "error", "message": str(e)}

@mcp.tool(
    name="run_baidu_scholar_crawler",
    description="运行百度学术爬虫工具。输入为查询字符串列表（e.g., ['人工智能', '虚拟现实']）。并发多进程爬取每个查询的标题、摘要、APA 引用，返回合并结果。"
)
async def run_baidu_scholar_crawler(queries: List[str]) -> str:  # 修改为 List[str]
    """批量运行百度学术爬虫 - 多进程并发"""
    if not queries:
        return json.dumps({"status": "error", "message": "Empty queries list"})
    
    print(f"主进程接收 {len(queries)} 个查询: {queries}")
    
    results = []
    with ProcessPoolExecutor(max_workers=16) as executor:
        future_to_query = {executor.submit(run_single_query, q): q for q in queries}
        
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                res = future.result()
                results.append(res)
                print(f"查询完成: {query} - 状态: {res['status']}")
            except Exception as e:
                err_res = {"query": query, "status": "error", "message": str(e)}
                results.append(err_res)
                print(f"查询异常: {query} - {str(e)}")
    
    # 合并结果
    overall = {
        "status": "success" if all(r["status"] == "success" for r in results) else "partial_success",
        "queries_count": len(queries),
        "results": results
    }
    
    print(f"所有查询处理完成，结果数: {len(results)}")
    return json.dumps(overall, ensure_ascii=False)

@mcp.resource(
    uri="crawler://description",
    description="百度学术爬虫：批量输入查询列表，使用多进程并发调用 Selenium，提取标题、摘要、APA。输出合并 JSON。支持并行。"
)
async def get_crawler_description() -> str:
    return """
    这个工具通过多进程批量调用爬取 https://xueshu.baidu.com。
    - 输入：查询列表（List[str]）。
    - 输出：合并 JSON，包括每个查询的结果或错误。
    注意：并发进程数受机器资源限制。
    """

if __name__ == "__main__":
    mcp.run(transport="sse")