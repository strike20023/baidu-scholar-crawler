from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium import webdriver

options = ChromeOptions()
driver = webdriver.Remote(options=options, command_executor="http://localhost:4444")
driver.get("https://bing.com")
with open("bing.txt", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
driver.quit()