# mcp_server.py
import os
import sys
import json
from typing import List, Dict
from contextlib import asynccontextmanager

import asyncio  # 用于锁

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm

from fastmcp import FastMCP, Context

from selenium import webdriver
options = ChromeOptions()
driver = webdriver.Remote(
    options=options,
    command_executor="http://localhost:4444"
)
driver.implicitly_wait(5)
if driver is None:
    raise "Driver 未初始化，请检查服务器启动"

crawler_lock = asyncio.Lock()

# 核心爬虫逻辑（复用全局 driver）
def run_crawler(query: str) -> str:
    if driver is None:
        return json.dumps({"error": "Driver 未初始化，请检查服务器启动"}, ensure_ascii=False)

    try:
        if not query.strip():
            raise ValueError("QUERY 不能为空")

        BASEURL = 'https://xueshu.baidu.com/ndscholar/browse/search?wd={}'
        encoded_query = query.replace(' ', '+')
        
        driver.get(BASEURL.format(encoded_query))
        
        data: List[Dict[str, str]] = []
        
        try:
            driver.find_element(By.CLASS_NAME, 'paper-wrap')
        except NoSuchElementException:
            return json.dumps({"error": "页面无结果或加载失败"}, ensure_ascii=False)

        elements = driver.find_elements(By.CLASS_NAME, 'paper-wrap')
        for e in tqdm(elements):
            title = e.find_element(By.CLASS_NAME, 'paper-title').text
            abstract = e.find_element(By.CLASS_NAME, 'paper-abstract').text
            e.find_element(By.CLASS_NAME, 'reference').click()
            APA_elem = driver.find_element(By.XPATH, "//*[contains(@class, 'sc-quote-list-item-l') and text()='APA']")
            APA = APA_elem.find_element(By.XPATH, "./..").find_element(By.CLASS_NAME, 'sc-quote-list-item-r').text.split('\n', 1)[0]
            driver.find_element(By.CLASS_NAME, 'ant-modal-close').click()
            data.append({
                'title': title,
                'abstract': abstract,
                'APA': APA
            })

        os.makedirs("outputs", exist_ok=True)
        safe_query = query.replace(' ', '_').replace('/', '_')
        filename = f"outputs/crawled-data-{safe_query}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        return json.dumps({
            "status": "success",
            "query": query,
            "results_count": len(data),
            "data": data,
            "saved_file": filename
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)



# 初始化 FastMCP 服务器
mcp = FastMCP(
    name="baidu-scholar-crawler",
    host="0.0.0.0",
    port=8080
)


# MCP Tool
@mcp.tool(
    name="run_baidu_scholar_crawler",
    description="运行百度学术爬虫工具（共享浏览器实例，不支持并发）。输入为明文查询字符串（e.g., '人工智能'）。会爬取标题、摘要、APA 引用，并保存到 outputs/ 目录。并发调用会排队。"
)
async def run_baidu_scholar_crawler(query: str) -> str:
    async with crawler_lock:
        result = run_crawler(query)  # sync call in async context
        return result

# Resource：添加 uri 参数
@mcp.resource(
    uri="crawler://description",  # 修复：添加所需 uri
    description="百度学术爬虫：使用共享 Selenium Remote 驱动（lifespan 初始化），查询明文字符串，支持提取标题、摘要、APA。输出保存为 JSON。不支持并行调用。"
)
async def get_crawler_description() -> str:
    return """
    这个工具复用共享 Selenium 驱动爬取 https://xueshu.baidu.com。
    - 输入：明文搜索词（e.g., '人工智能'）。
    - 输出：JSON 数据，包括标题、摘要、APA。
    - 依赖：Remote ChromeDriver (ngrok URL)，在服务器启动时初始化。
    - 注意：共享 driver 不支持并发（使用锁序列化）；网络延迟可能导致超时；确保 ngrok 活跃。
    """

if __name__ == "__main__":
    mcp.run(transport="sse")