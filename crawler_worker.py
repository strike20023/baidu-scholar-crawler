import docker
import time
import requests
import json
import sys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_container_sync(ip):  # 同步等待
    for _ in range(30):
        try:
            resp = requests.get(f"http://{ip}:4444/wd/hub/status", timeout=1)
            if resp.status_code == 200:
                return True
        except:
            pass
        time.sleep(2)
    raise Exception("容器启动超时")

def start_selenium_container():
    client = docker.from_env()
    container = client.containers.run(image="selenium/standalone-chrome:latest", detach=True, shm_size="2g", platform="linux/amd64")
    container.reload()
    networks = container.attrs['NetworkSettings']['Networks']
    ip_address = next(iter(networks.values()))['IPAddress']
    return container, ip_address

def init_driver(ip):
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Remote(options=options, command_executor=f"http://{ip}:4444")
    driver.implicitly_wait(5)
    return driver

def crawling(driver, query):
    BASEURL = 'https://xueshu.baidu.com/ndscholar/browse/search?wd={}'
    driver.get(BASEURL.format(query.replace(' ', '+')))
    data = []
    driver.find_element(By.CLASS_NAME, 'paper-wrap')  # 等待元素

    for e in driver.find_elements(By.CLASS_NAME, 'paper-wrap'):
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
    return {
        "status": "success",
        "query": query,
        "results_count": len(data),
        "data": data
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "No query provided"}))
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    logger.info(f"Worker 开始处理查询: {query}")
    
    container, ip = start_selenium_container()
    logger.info(f"容器启动，IP: {ip}")
    
    try:
        wait_for_container_sync(ip)
        driver = init_driver(ip)
        msg = crawling(driver, query)
        print(json.dumps(msg, ensure_ascii=False))  # 输出到 stdout
        logger.info(f"爬取完成，结果数: {len(msg.get('data', []))}")
    except Exception as e:
        error_msg = {"status": "error", "message": str(e)}
        print(json.dumps(error_msg))
        logger.error(f"爬取失败: {str(e)}")
    finally:
        container.stop()
        container.remove()
        logger.info("容器已清理")

        