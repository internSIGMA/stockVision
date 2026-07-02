from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_cookie():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    driver.get("https://stockbit.com")
    
    input("Login dulu manual, lalu tekan ENTER...")

    cookies = driver.get_cookies()
    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

    driver.quit()
    return cookie_str

cookie = get_cookie()
print(cookie)