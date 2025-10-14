# %%
import os
try:
    query = os.environ['QUERY']
except KeyError:
    raise ValueError("环境变量 'QUERY' 未设置，请先配置该变量") from None
# %%
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver

options = ChromeOptions()
driver = webdriver.Remote(options=options, command_executor="http://localhost:4444")
driver.get("https://bing.com")

# %%
with open(f"crawled-data-{query}.json", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
# %%