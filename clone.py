import json
import pyotp
import re
import sys
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
import time
import os
import requests
import random
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium_stealth import stealth                                                                                        
from dotenv import load_dotenv
from AI import generate_comment_by_image_and_text, generate_comment_by_text, generate_content_by_text, generate_post
from Checker import is_video_tweet, is_white_list_account
from actions import action_details
from files import read_following_accounts_from_file, read_hashtag_comment_by_main_account, read_profile_list_from_file, read_profile_list_from_file1, read_urls_comment_by_main_account, read_white_account_from_file
import concurrent.futures
from finds import find_back_navigation, find_button_search, find_contents, find_home_button, find_images, find_input_search
from urllib.parse import urlparse

load_dotenv()

def get_ip_proxy(http):
    try:
        proxy = {
            'http': http
        }
        response = requests.get('http://httpbin.org/ip', proxies=proxy, timeout=10)
        if response.status_code == 200:
            return response.json()['origin']
        else:
            return None
    except Exception as e:
        return None

def wait_until_new_ip(current_ip, http):
    print(current_ip)
    if current_ip is None:
        current_ip = get_ip_proxy(http)
    while True:
        new_ip = get_ip_proxy(http)
        print(new_ip)
        if new_ip is not None and current_ip != new_ip:
            return new_ip
        time.sleep(10)

def find_twwet_details(element):
    try:
        regex = r"https:\/\/twitter\.com\/\w+\/status\/\d+$"
        pattern = re.compile(regex)
        return next((e for e in element.find_elements(By.TAG_NAME, "a") if pattern.match(e.get_attribute("href"))), None)
    except:
        return None
def is_twwet_ad(element):
    try:
        elements = element.find_elements(By.TAG_NAME, 'span')
        for e in elements:
            if 'Ad' == e.text:
                return True
    except:
        return False
    return False

def find_element_by_text(element, by, tag_name, text):
    try:
        elements = element.find_elements(by, tag_name)
        for e in elements:
            if text == e.text:
                return e
    except:
        return None
    return None

def get_host_name(url):
    try:
        parsed_url = urlparse(url)
        return parsed_url.hostname
    except:
        return None
def is_scroll_down_complete(driver):
    viewport_height = driver.execute_script("return window.innerHeight;")
    document_height = driver.execute_script("return document.body.scrollHeight;")
    scroll_position = driver.execute_script("return window.scrollY;")
    return viewport_height + scroll_position >= document_height
def find_button_follow(tweet_details):
    try:
        buttons = tweet_details.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
        for b in buttons:
            span = b.find_elements(By.TAG_NAME, 'span')
            for s in span:
                if s.text == 'Follow':
                    return b
    except:
        return None
    return None
def scroll(driver, wait, action, profile, max_runtime, start_time, new_ip):
    start_time_follow = time.time()
    max_runtime_follow = 1 * 60
    is_follow = False
    time.sleep(random.uniform(5,10))
    if action_start(driver) == 1:
        while True:
            if action_continue(driver) == 1:
                break
    element = valid_twwets_by_twwets(wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]'))))[0]
    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time >= max_runtime:
            break
        if action_start(driver) == 1:
            while True:
                if action_continue(driver) == 1:
                    break
        current_time_follow = time.time()
        elapsed_time_follow = current_time_follow - start_time_follow
        if elapsed_time_follow >= max_runtime_follow and is_follow is False:
            print('action')
            action_follow_by_search(driver, action, wait, max_runtime, start_time)
            is_follow = True
            button_home = find_home_button(wait)
            if button_home:
                action.click(button_home).perform()
                element = wait.until(lambda driver: waitNewElement(driver, None, True))
        url_current = find_url_tweet(element)
        action.move_to_element(element).perform()
        time.sleep(random.uniform(2,5))
        element = wait.until(lambda driver: waitNewElement(driver, url_current, False))

def action_follow_by_search(driver, action, wait, max_runtime, start_time):
    if action_start(driver) == 1:
        while True:
            if action_continue(driver) == 1:
                break
    hash_tags = read_hashtag_comment_by_main_account()
    for tag in hash_tags:
        action_search_by_keyword(wait, action, tag.keyword)
        element = valid_twwets_by_twwets(wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]'))))[0]
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time >= max_runtime:
                return 1
            url_current = find_url_tweet(element)
            is_tweet_by_main_account = is_tweet_by_account(element, [tag.username])
            action.move_to_element(element).perform()
            time.sleep(random.uniform(1,2))
            if is_tweet_by_main_account:
                tweet_content = element.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')
                action.move_to_element(tweet_content).perform()
                time.sleep(random.uniform(1,2))
                action.click(tweet_content).perform()
                tweet_details = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
                time.sleep(random.uniform(5,10))
                follow_button = find_button_follow(tweet_details)
                if follow_button:
                    print('click follow')
                    action.move_to_element(follow_button).perform()
                    time.sleep(random.uniform(1,2))
                    action.click(follow_button).perform()
                time.sleep(random.uniform(5,10))
                if action_start(driver) == 1:
                    while True:
                        if action_continue(driver) == 1:
                            break
                break
            if is_scroll_down_complete(driver):
                break
            element = wait.until(lambda driver: waitNewElement(driver, url_current, False))
def rotate_ip(key):
    url = "http://127.0.0.1:9000/rotate/{}".format(key)
    print(url)
    try:
        response = requests.post(url)
        if response.status_code == 200:
            response_data = response.json()
            real_ip_address = response_data.get('realIpAddress')
            return real_ip_address
        else:
            print('not 200')
            return None
    except requests.exceptions.RequestException as e:
        print(e)
        return None
def process_profile(profile):
    width = random.uniform(350,400)
    height = random.uniform(900,1080)
    max_runtime = profile.time_process * 60
    chrome_options = uc.ChromeOptions()
    preferences = {
        "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
        "webrtc.multiple_routes_enabled": False,
        "webrtc.nonproxied_udp_enabled" : False
    }
    #chrome_options.add_extension("C:/Users/Long/Downloads/xxx/extension.zip")
    chrome_options.add_argument(f"--load-extension=C:/Users/Long/Downloads/extension")
    chrome_options.add_experimental_option("prefs", preferences)
    chrome_options.add_argument("--window-size="+str(width)+","+str(height))
    chrome_options.add_argument("--disable-gpu")

    print('--proxy-server={}'.format(profile.proxy))
    if profile.proxy:
        chrome_options.add_argument('--proxy-server={}'.format(profile.proxy))
    print(profile.profile_dir)
    driver = uc.Chrome(driver_executable_path=os.getenv("DRIVER_PATH"),browser_executable_path=os.getenv("BROWSER_PATH"), options=chrome_options,version_main=119, user_multi_procs=True, user_data_dir=profile.profile_dir, use_subprocess=False)
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=False,
        )
    wait = WebDriverWait(driver, 60)
    action = ActionChains(driver)
    driver.set_window_size(width, height)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'})
    
    current_ip = None
    while True:
        current_ip = get_ip_proxy(profile.proxy)
        print(current_ip)
        if current_ip is not None:
            break
    print(current_ip)
    new_ip = None
    while True:
        real_ip = rotate_ip(profile.content_post)
        print(real_ip)
        if real_ip is not None and real_ip != current_ip:
            new_ip = real_ip
            break
        time.sleep(10)

    print(new_ip)
    
    start_time = time.time()
    
    driver.get("https://twitter.com/")
    time.sleep(5)
    if driver.current_url != 'https://twitter.com/home':
        try:
            button_sign_in = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[role="link"][data-testid="loginButton"]')))
            if button_sign_in:
                action.move_to_element(button_sign_in).perform()
                action.click(button_sign_in).perform()
                input_email = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"][type="text"]')))
                if input_email:
                    action.send_keys_to_element(input_email, profile.username).perform()
                    button_next = find_element_by_text(driver, By.TAG_NAME, 'span', 'Next')
                    if button_next:
                        action.move_to_element(button_next).perform()
                        time.sleep(1)
                        action.click(button_next).perform()
                        input_password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"][type="password"]')))
                        if input_password:
                            action.send_keys_to_element(input_password, profile.password).perform()
                            time.sleep(1)
                            button_log_in = find_element_by_text(driver, By.TAG_NAME, 'span', 'Log in')
                            if button_log_in:
                                action.click(button_log_in).perform()
                                input_otp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"][type="text"][data-testid="ocfEnterTextTextInput"]')))
                                if input_otp:                                
                                    totp = pyotp.TOTP(profile.scret_key)
                                    action.send_keys_to_element(input_otp, totp.now()).perform()
                                    button_next = find_element_by_text(driver, By.TAG_NAME, 'span', 'Next')
                                    if button_next:
                                        action.move_to_element(button_next).perform()
                                        action.click(button_next).perform()
        except:
            pass

    if profile.work:
        while True:
            try:
                if action_start(driver) == 1:
                    while True:
                        if action_continue(driver) == 1:
                            break
                else :
                    action_continue(driver)
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time >= max_runtime:
                    break
                result = scroll(driver,wait,action, profile, max_runtime, start_time, new_ip)
                if result == 1:
                    break
            except Exception as e:
                print('exception')
                print(e)
                if driver.current_url != 'https://twitter.com/home':
                    try:
                        button_sign_in = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[role="link"][data-testid="loginButton"]')))
                        if button_sign_in:
                            action.move_to_element(button_sign_in).perform()
                            action.click(button_sign_in).perform()
                            input_email = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"][type="text"]')))
                            if input_email:
                                action.send_keys_to_element(input_email, profile.username).perform()
                                button_next = find_element_by_text(driver, By.TAG_NAME, 'span', 'Next')
                                if button_next:
                                    action.move_to_element(button_next).perform()
                                    time.sleep(1)
                                    action.click(button_next).perform()
                                    input_password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"][type="password"]')))
                                    if input_password:
                                        action.send_keys_to_element(input_password, profile.password).perform()
                                        time.sleep(1)
                                        button_log_in = find_element_by_text(driver, By.TAG_NAME, 'span', 'Log in')
                                        if button_log_in:
                                            action.click(button_log_in).perform()
                                            input_otp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"][type="text"][data-testid="ocfEnterTextTextInput"]')))
                                            if input_otp:                                
                                                totp = pyotp.TOTP(profile.scret_key)
                                                action.send_keys_to_element(input_otp, totp.now()).perform()
                                                button_next = find_element_by_text(driver, By.TAG_NAME, 'span', 'Next')
                                                if button_next:
                                                    action.move_to_element(button_next).perform()
                                                    action.click(button_next).perform()
                    except:
                        pass
                if action_start(driver) == 1:
                    while True:
                        if action_continue(driver) == 1:
                            break
                continue
    if get_ip_proxy(profile.proxy) == new_ip:
        print('ip mapping khi ket thuc')
    else:
        print('ip khong mapping khi ket thuc')
    quit_driver(driver)

def action_continue(driver):
    action = ActionChains(driver)
    elements = driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"]')
    for element in elements:
        if element.get_attribute('value') == 'Continue to X':
            action.click(element).perform()
            print('click continue')
            return 1
    return 0
def action_start(driver):
    action = ActionChains(driver)
    elements = driver.find_elements(By.CSS_SELECTOR, 'input[type="submit"]')
    for element in elements:
        if element.get_attribute('value') == 'Start':
            action.click(element).perform()
            print('click start')
            return 1
    return 0
def quit_driver(driver):
    try:
        os.kill(driver.browser_pid, 15)
        if "linux" in sys.platform:
            os.waitpid(driver.browser_pid, 0)
            time.sleep(0.02)
        else:
            time.sleep(0.04)
    except:
        pass
    if hasattr(driver, "service") and getattr(driver.service, "process", None):
        driver.service.stop()
    try:
        if driver.reactor and isinstance(driver.reactor, uc.Reactor):
            driver.reactor.event.set()
    except:
        pass
    if (
        hasattr(driver, "keep_user_data_dir")
        and hasattr(driver, "user_data_dir")
        and not driver.keep_user_data_dir
    ):
        import shutil
        for _ in range(5):
            try:
                shutil.rmtree(driver.user_data_dir, ignore_errors=False)
            except FileNotFoundError:
                pass
            else:
                break
            time.sleep(0.1)
    driver.patcher = None

def valid_twwets_by_twwets(twwets):
    valid_twwets = []
    for twwet in twwets:
        if find_url_tweet(twwet) is not None:
            valid_twwets.append(twwet)
    return valid_twwets

def wait_new_element_by_index(driver, next_index):
    try:
        twwets = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']")
    except:
        return False
    if len(twwets) <= next_index:
        return False
    return twwets[next_index]
def waitNewElement(driver, url_current, lastIndex):
    try:
        twwets = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='cellInnerDiv']")
    except:
        return False
    valid_twwets = valid_twwets_by_twwets(twwets)
    if len(valid_twwets) == 0:
        return False
    if (lastIndex or url_current is None):
        return valid_twwets[-1]
    next_index = find_index_element(url_current, valid_twwets)
    if (next_index != -1 and next_index != len(valid_twwets)):
        return valid_twwets[next_index]
    return False

def is_tab_for_me(driver, wait):
    navigation_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'nav[aria-live="polite"][role="navigation"]')))
    #navigation = driver.find_element(By.CSS_SELECTOR, 'div[aria-live="polite"][role="navigation"]')
    list_tab_element = navigation_element.find_element(By.TAG_NAME, 'a')
    if (list_tab_element.get_attribute('aria-selected') == 'true'):
        return True
    return False

####random########
def random_boolean(percent):
    return random.random() < percent
def action_retry(driver, action):
    button_retry = find_button_by_text(driver, 'Retry')
    if button_retry:
        print('click retry')
        action.move_to_element(button_retry).perform()
        action.click(button_retry).perform()
def action_by_pass_bot(driver, action):
    button_got_it = find_button_by_text(driver, 'Got it')
    if button_got_it:
        action.move_to_element(button_got_it).perform()
        time.sleep(random.uniform(0.5, 2))
        action.click(button_got_it).perform()
        print('click got it')
        action.reset_actions()
def find_button_by_text(driver, text):
    wait = WebDriverWait(driver, 10)
    try:
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="button"]')))
        for e in elements:
            if e.text == text:
                return e
    except:
        return None   
    return None
    
def find_by_css_selector_wait(driver, css):
    wait = WebDriverWait(driver, 60)
    try:
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
    except:
        return None
def find_by_css_selector(driver, css):
    try:
        return driver.find_element(By.CSS_SELECTOR, css)
    except:
        return None
def action_details(wait, action, element):
    print('action_details')
    regex = r"https:\/\/twitter\.com\/\w+\/status\/\d+$"
    pattern = re.compile(regex)
    tweet = next((e for e in element.find_elements(By.TAG_NAME, "a") if pattern.match(e.get_attribute("href"))), None)
    if (tweet):
        action.move_to_element(tweet).perform()
        time.sleep(random.uniform(0.5, 2))
        action.click(tweet).perform()
        time.sleep(random.uniform(10, 30))
        
        closeButton = find_back_navigation(wait)
        action.move_to_element(closeButton).perform()
        time.sleep(random.uniform(0.5, 2))
        action.click().perform()
        time.sleep(random.uniform(5, 10))

def action_search_by_keyword(wait, action, keyword):
    if keyword:
        action.reset_actions()
        button_search = find_button_search(wait)
        action.move_to_element(button_search).perform()
        time.sleep(random.uniform(0.5, 2))
        action.click().perform()
        time.sleep(random.uniform(0.5,2))
        input_search = find_input_search(wait)
        action.move_to_element(input_search).perform()
        time.sleep(random.uniform(0.5,2))
        action.click(input_search).perform()
        time.sleep(random.uniform(0.5,2))
        input_search.clear()
        time.sleep(random.uniform(0.5,2))
        action.send_keys(keyword).perform()
        time.sleep(random.uniform(0.5,2))
        action.send_keys(Keys.RETURN).perform()

def refresh(username, accounts):
    white_accounts = read_white_account_from_file(os.getenv('PROFILE_PATH'))
    following_accounts = read_following_accounts_from_file(os.getenv("PROCESS_ACCOUNT_PATH")+username+'.txt')
    urls_comment_by_main_account = read_urls_comment_by_main_account()
    main_accounts_not_yet_follow = [account for account in accounts if account not in following_accounts]
    white_accounts_not_yet_follow = [account for account in white_accounts if account not in following_accounts]
    return white_accounts, following_accounts, urls_comment_by_main_account, main_accounts_not_yet_follow, white_accounts_not_yet_follow



def action_push_tweet(wait, action, content):
    home_button = find_home_button(wait)
    action.reset_actions()
    action.click(home_button).perform()
    content_text = generate_post()
    input_tweet = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"][data-testid="tweetTextarea_0"][role="textbox"]')))
    action.click(input_tweet).perform()
    time.sleep(random.uniform(0.5, 2))
    contents = list(content_text)
    for c in contents:
        action.send_keys(c).perform()
        time.sleep(random.uniform(0.2, 1))
    action.send_keys(Keys.ENTER).perform()
    
    time.sleep(random.uniform(5,10))
    button_post = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="button"][data-testid="tweetButtonInline"]')))
    action.reset_actions()
    action.scroll_to_element(button_post).perform()
    action.click(button_post).perform()
    action.reset_actions()

def find_by_css_selector(element, css):
    try:
        return element.find_element(By.CSS_SELECTOR, css)
    except:
        return None

def find_url_tweet_by_element(element):
    regex = r"https:\/\/twitter\.com\/\w+\/status\/\d+$"
    pattern = re.compile(regex)
    elements = element.find_elements(By.CSS_SELECTOR, 'a[href]')
    for e in elements:
        if pattern.match(e.get_attribute('href')):
            return e
    return None

def find_url_ads_by_element(element):
    try:
        elements = element.find_elements(By.CSS_SELECTOR, 'a[href]')
        for e in elements:
            if not e.get_attribute('href').startswith('https://twitter.com') and 'twclid' in e.get_attribute('href'):
                return e
    except:
        return None
    return None

def find_button_unfollow_profile(wait):
    try:
        script_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'script[type="application/ld+json"]')))
        data = json.loads(script_element.get_attribute('innerHTML'))
        identifier = data['author']['identifier']
        data_testid = '{}-unfollow'.format(identifier)
        button_follow = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="button"][data-testid="{}"]'.format(data_testid))))
        return button_follow
    except:
        return None

def find_button_follow_profile(wait):
    try:
        script_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'script[type="application/ld+json"]')))
        data = json.loads(script_element.get_attribute('innerHTML'))
        identifier = data['author']['identifier']
        data_testid = '{}-follow'.format(identifier)
        button_follow = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="button"][data-testid="{}"]'.format(data_testid))))
        return button_follow
    except:
        return None
#ok
def find_button_back(wait):
    try:
        svg_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'path')))
        for svg_tag in svg_elements:
            if svg_tag.get_attribute("d") in [os.getenv("PATH_CLOSE_BUTTON"), os.getenv("PATH_BACK_BUTTON")]:
                return svg_tag
        return None
    except:
        return None
#ok
def find_url_white_account(element, accounts):
    try:
        elements = element.find_elements(By.CSS_SELECTOR, 'a[href]')
        for e in elements:
            for account in accounts:
                if e.get_attribute('href').endswith(account):
                    return e, account
    except:
        return None, None
    return None, None

def find_index_element(url_current, tweets):
    if url_current:
        for index, tweet in enumerate(tweets):
            tweet_link = find_url_tweet(tweet)
            if tweet_link and tweet_link == url_current:
                return index + 1
    return -1
def find_show_more_in_tweet(element):
    try:
        elements = element.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
        for e in elements:
            if e.text == 'Show' or e.text == 'Show more replies':
                return e
    except:
        return None
    return None

def is_element_by_text(element, text):
    try:
        if element.text == text:
            return True
    except:
        pass
    return False
def find_url_tweet(element):
    regex = r"https:\/\/twitter\.com\/\w+\/status\/\d+$"
    pattern = re.compile(regex)
    try:
        elements = element.find_elements(By.CSS_SELECTOR, 'a[href]')
        for e in elements:
            if pattern.match(e.get_attribute('href')):
                return e.get_attribute('href')
    except:
        return None
    return None

def is_tweet_by_account(element, accounts):
    try:
        elements = element.find_elements(By.CSS_SELECTOR, 'a[href]')
        for e in elements:
            for account in accounts:
                if e.get_attribute('href').endswith(account):
                    return True
        return False
    except:
        return False

def is_tweet_comment_by_main_account(element, urls, main_accounts_not_yet_follow):
    elements = element.find_elements(By.CSS_SELECTOR, 'a[href]')
    for e in elements:
        for url in urls:
            if e.get_attribute('href') == url.url and url.username in main_accounts_not_yet_follow:
                return True
    return False

if __name__ == '__main__':
    max_threads = 1
    profiles = read_profile_list_from_file1(os.getenv("PROFILE_PATH"),'Clone_Follow')
    profiles_start = [profile for profile in profiles if profile.start]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_profile, profile) for profile in profiles_start]