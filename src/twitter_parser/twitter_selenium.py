# Web checkin handling
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

from utils.log_utils import log_screen


DEFAULT_TIMEOUT = 20

def setup_driver():
    options = Options()
    service = Service("/usr/bin/chromedriver")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox") # linux only
    # options.add_argument("--headless") 
    driver = webdriver.Chrome(service = service, options=options)

    return driver

def twitter_logging(driver, user, pwd):
    loging_url = "https://x.com/i/flow/login"

    # Small function to reduce code later
    def DriverWaitUntil(*args):
        return WebDriverWait(driver=driver, timeout=DEFAULT_TIMEOUT).until(*args)

    try:
        # head to login page
        driver.get(loging_url)

        DriverWaitUntil(EC.presence_of_element_located((By.NAME, "text")), # Function needs tuple!
                        'Timed out waiting for loggin page to load.')

        # find username/email field and send the username itself to the input field
        user_input = driver.find_element(By.NAME, "text")
        user_input.send_keys(user)
        user_input.send_keys(Keys.RETURN)
        
        DriverWaitUntil(EC.presence_of_element_located((By.NAME, "password")), # Function needs tuple!
                        'Timed out waiting for password input page to load.')
        
        # find password input field and insert password as well
        pwd_input = driver.find_element(By.NAME, "password")
        pwd_input.send_keys(pwd)
        pwd_input.send_keys(Keys.RETURN)

        DriverWaitUntil(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-testid="AppTabBar_Notifications_Link"]')),
                        'Timed out waiting for logging to be finished, Twitter main page not loading')
    
    except TimeoutException as timeout_exception:
        log_screen(f"Exception handling checkin operation: {timeout_exception}", level="ERROR", notify=True)
        log_screen(f"Exception catched.", level="ERROR")
        driver.quit()
        return False, False
    

def scroll_to_top(driver, waitUntilLoaded):
    # print("Scrolling to the top...")
    step_height = 700
    retries = 0
    max_retries = 5
    while True:
        current_height = driver.execute_script("return document.body.scrollHeight")
        
        driver.execute_script(f"window.scrollBy(0, -{step_height});")
        waitUntilLoaded()
        time.sleep(0.5)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        # print(f"Scrolling up: {current_height = }, {new_height = }")
        
        if new_height == current_height: retries += 1
        else:                            retries = 0
        
        if retries >= max_retries:
            # print("Reached the top or no more content to load.")
            break
    
    driver.execute_script(f"window.scrollTo(0, 0);")
    waitUntilLoaded()


"""
    Takes tweets from a given url, note that it provides repeated tweet tags
    due to scrolling and web reloading :(
"""
def get_tweet_html(driver, tweet_url):
    driver.get(tweet_url) 

    # Small function to reduce code later
    def DriverWaitUntil(*args):
        return WebDriverWait(driver=driver, timeout=DEFAULT_TIMEOUT).until(*args)
    
    # Wait for answer button to load all page   
    DriverWaitUntil(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tweetButtonInline"]')),
                    'Timed out waitin for tweet button line')
    
    def waitUntilLoaded():
        DriverWaitUntil( lambda d: d.execute_script('return document.readyState') == 'complete' ,
                        'Timed out waiting for complete state')
        DriverWaitUntil(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="primaryColumn"]')),
                        'Timed out waiting for primaryColumn to appear')
    ## Scroll to top :)
    scroll_to_top(driver, waitUntilLoaded)

    # Scroll down accumulating tweets :)
    combined_html = ""
    step_height = 500

    # print("Scrolling down to capture tweets...")
    while True:
        try:
            # Obtener tweets visibles
            elements = driver.find_elements(By.CSS_SELECTOR, 'div.css-175oi2r.r-16y2uox.r-1wbh5a2.r-1ny4l3l')
            for element in elements:
                element_html = element.get_attribute('outerHTML')
                combined_html += element_html
                
            driver.execute_script(f"window.scrollBy(0, {step_height});")
            waitUntilLoaded()

            # Verificar si hemos llegado al final
            current_height = driver.execute_script("return window.scrollY + window.innerHeight")
            total_height = driver.execute_script("return document.body.scrollHeight")
            # print(f"Scrolling down: {current_height = }, {total_height = }")

            if current_height >= total_height:
                break

        except StaleElementReferenceException:
            log_screen("Stale element reference exception detected.", level="ERROR")
            continue
        except TimeoutException:
            log_screen("Timed out while waiting to load new elements.", level="ERROR")
            break
        

    return combined_html


"""
    Provided an URL of a Twet that cites another one, it returns the
    cited URL
"""
def get_cited_tweet_url(driver, tweet_url):
    driver.get(tweet_url) 

    # Small function to reduce code later
    def DriverWaitUntil(*args):
        return WebDriverWait(driver=driver, timeout=DEFAULT_TIMEOUT).until(*args)
    
    DriverWaitUntil(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tweetButtonInline"]')),
                    'Timed out waitin for tweet button line')
    
    element = driver.find_element(By.CSS_SELECTOR, 'div.css-175oi2r.r-adacv.r-1udh08x.r-1kqtdi0.r-1867qdf.r-rs99b7.r-o7ynqc.r-6416eg.r-1ny4l3l.r-1loqt21')
    
    driver.execute_script("arguments[0].scrollIntoView();", element) 
    driver.execute_script("arguments[0].click();", element)

    DriverWaitUntil(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tweetButtonInline"]')),
                    'Timed out waitin for tweet button line')
    
    return driver.current_url



"""
    Provided an URL of a Twet that cites another one, it returns the
    cited URL
"""
def get_tweet_screenshot(driver, tweet_url, output_file):
    href_value = "/"+"/".join(tweet_url.split("/")[-3:])
    driver.set_window_size(1920*5, 1080*5)
    driver.get(tweet_url)  
    
    def DriverWaitUntil(*args):
        return WebDriverWait(driver=driver, timeout=DEFAULT_TIMEOUT).until(*args)
    
    DriverWaitUntil(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-testid="tweetButtonInline"]')),
                    'Timed out waitin for tweet button line')
    

    link_element = driver.find_element(By.XPATH, f'//a[@href="{href_value}"]')
    element = link_element.find_element(By.XPATH, './ancestor::article')

    element.screenshot(output_file)