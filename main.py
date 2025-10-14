
import os
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import base64
from tqdm import tqdm

try:
    _query = os.environ['QUERY']
except KeyError:
    raise ValueError("环境变量 'QUERY' 未设置，请先配置该变量") from None

try:
    query = base64.b64decode(_query).decode('utf-8')
except Exception as e:
    raise ValueError("环境变量 'QUERY' 不是有效的 Base64 编码，请检查该变量") from e


options = ChromeOptions()
<<<<<<< HEAD
driver = webdriver.Remote(options=options, command_executor="http://localhost:4444")
=======
driver = webdriver.Remote(options=options, command_executor="https://jeff-haemal-uncompromisingly.ngrok-free.dev")
>>>>>>> ebd64c3 (添加爬取数据的输出文件，包含数学教育相关文献的标题和摘要)
driver.implicitly_wait(5)
BASEURL = 'https://xueshu.baidu.com/ndscholar/browse/search?wd={}'

try:
    driver.get(BASEURL.format(query.replace(' ', '+')))
    data = []
    driver.find_element(By.CLASS_NAME, 'paper-wrap')

    for e in tqdm(driver.find_elements(By.CLASS_NAME, 'paper-wrap')):
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

    with open(f"outputs/crawled-data-{_query}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False))
except Exception as e:
    print(e)    
driver.quit()