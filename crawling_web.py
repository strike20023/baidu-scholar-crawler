import docker
import time
import requests

from typing import List

import asyncio
import aiohttp

async def wait_for_container(ip):
    async with aiohttp.ClientSession() as session:
        for _ in range(30):  # 最多等待60秒
            try:
                async with session.get(f"http://{ip}:4444/wd/hub/status", timeout=1) as resp:
                    if resp.status == 200:
                        return True
            except:
                pass
            await asyncio.sleep(2)  # 异步等待
        raise Exception("容器启动超时")
    

def start_selenium_container():
    client = docker.from_env()
    container = client.containers.run(image="selenium/standalone-chrome:latest",detach=True,shm_size="2g",platform="linux/amd64")
    container.reload()
    networks = container.attrs['NetworkSettings']['Networks']
    ip_address = next(iter(networks.values()))['IPAddress']
    return container, ip_address

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm

def init_driver(ip):
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Remote(options=options, command_executor=f"http://{ip}:4444")
    driver.implicitly_wait(5)
    return driver

def crawling(driver, query):
    BASEURL = 'https://xueshu.baidu.com/ndscholar/browse/search?wd={}&pn={}'
    data = []
    pn=0
    max_pn=30
    driver.get(BASEURL.format(query.replace(' ', '+'), pn))
    driver.find_element(By.CLASS_NAME, 'paper-wrap')
    len_data = driver.find_element(By.CLASS_NAME, 'search-nums').find_element(By.TAG_NAME, 'span').text
    len_data = int(len_data)
    while len_data>pn:
        if pn>=max_pn:
            break
        driver.get(BASEURL.format(query.replace(' ', '+'), pn))
        driver.find_element(By.CLASS_NAME, 'paper-wrap')
        
        for e in tqdm(driver.find_elements(By.CLASS_NAME, 'paper-wrap'), desc=f"爬取第 {pn//10+1} 页"):
            title = e.find_element(By.CLASS_NAME, 'paper-title').text
            abstract = e.find_element(By.CLASS_NAME, 'paper-abstract').text
            e.find_element(By.CLASS_NAME, 'reference').click()
            APA = driver.find_element(By.XPATH, "//*[contains(@class, 'sc-quote-list-item-l') and text()='APA']").find_element(By.XPATH, "./..").find_element(By.CLASS_NAME, 'sc-quote-list-item-r').text.split('\n',1)[0]
            driver.find_element(By.CLASS_NAME, 'ant-modal-close').click()
            data.append({
                'title': title,
                'abstract': abstract,
                'APA': APA
            })
        pn+=10
    return {
        "status": "success",
        "query": query,
        "results_count": len(data),
        "data": data
    }
from fastmcp import FastMCP, Context
import json
mcp = FastMCP(
    name="scholar-crawler(baidu)",
    host="0.0.0.0",
    port=8899
)

async def crawl_single_query(query: str) -> dict:
    """处理单个查询的爬取逻辑，包括启动容器、等待、初始化driver、爬取和清理"""
    container, ip = start_selenium_container()
    print(f"Start the container for query '{query}', IP: http://{ip}:7900")
    try:
        await wait_for_container(ip)
        print("Container ready, initializing driver")
        driver = init_driver(ip)
        print("Driver initialized, starting crawling")
        msg = crawling(driver, query)
        print(f"Crawling finished for '{query}', Number of results: {len(msg.get('data', []))}")
        return msg
    finally:
        try:
            driver.quit()
        except:
            pass
        container.stop()
        container.remove()

# MCP Tool
@mcp.tool(
    name="run_baidu_scholar_crawler",
    description="运行百度学术爬虫工具。输入为查询字符串（e.g., ['人工智能 虚拟现实', '电车难题 教育学']）。会爬取标题、摘要、APA 引用。可并发调用，每个查询独立容器并行处理。"
)
async def run_baidu_scholar_crawler(ctx: Context, queries: List[str]) -> str:
    """运行百度学术爬虫工具，使用 asyncio.gather 并行处理每个查询的独立容器和driver"""
    tasks = [crawl_single_query(ctx, query) for query in queries]
    msgs = await asyncio.gather(*tasks)
    return json.dumps(msgs, ensure_ascii=False)

@mcp.resource(
    uri="crawler://description",
    description="百度学术爬虫：每个查询使用独立的 Selenium Remote 驱动和容器，并行查询字符串，支持提取标题、摘要、APA。输出保存为 JSON。支持并行调用。"
)
async def get_crawler_description() -> str:
    return """
    这个工具为每个查询启动独立的 Selenium 容器和驱动，并行爬取 https://xueshu.baidu.com。
    - 输入：搜索词列表（e.g., ['人工智能 虚拟现实', '电车难题 教育学']）。
    - 输出：JSON 数据，包括标题、摘要、APA。
    - 优势：并行处理，提高效率，避免共享driver的潜在冲突。
    """

if __name__ == "__main__":
    mcp.run(transport="sse")