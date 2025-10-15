# %%
import os
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import base64
from tqdm import tqdm
# %%


options = ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Remote(options=options, command_executor="http://localhost:4444")
driver.implicitly_wait(5)
BASEURL = 'https://xueshu.baidu.com/ndscholar/browse/search?wd={}&pn={}'
# %%
query = '人工智能 虚拟现实'
data = []
driver.get(BASEURL.format(query.replace(' ', '+'), 0))
driver.find_element(By.CLASS_NAME, 'paper-wrap')
len_data = driver.find_element(By.CLASS_NAME, 'search-nums').find_element(By.TAG_NAME, 'span').text
len_data = int(len_data)
# %%
pn=0
max_pn=30
while len_data>pn:
    if pn>max_pn:
        break
    print(f"正在爬取第 {pn//10+1} 页")
    driver.get(BASEURL.format(query.replace(' ', '+'), pn))
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
    pn+=10
# %%
print(data)