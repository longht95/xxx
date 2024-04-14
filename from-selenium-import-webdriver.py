import json
import re
import sys
import pyotp
import requests
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
import time
import os
import random
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
from files import read_following_accounts_from_file, read_profile_list_from_file, read_urls_comment_by_main_account, read_white_account_from_file
import concurrent.futures
from finds import find_back_navigation, find_button_search, find_contents, find_home_button, find_images, find_input_search
from urllib.parse import urlparse

load_dotenv()

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
def action_tweet_ads(tweet_details, action, wait, profile, driver):
    action.move_to_element(tweet_details).perform()
    time.sleep(random.uniform(0.5, 2))
    action.click(tweet_details).perform()
    time.sleep(random.uniform(10, 30))
    elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
    while True:
        element_show_more = None
        is_done = False
        for e in elements:
            if is_twwet_ad(e):
                print('Ads')
                element_ads = find_url_ads_by_element(e)
                urls_clicked = read_following_accounts_from_file(os.getenv("PROCESS_ADS_PATH")+profile.username+'.txt')
                if element_ads:
                    print('click ads url')
                    url_ads = get_host_name(element_ads.get_attribute('href'))
                    if url_ads not in urls_clicked:
                        action.move_to_element(e).perform()
                        time.sleep(random.uniform(10,20))
                        action.click(element_ads).perform()
                        window_handles = driver.window_handles
                        new_window_handle = window_handles[1]
                        current_window_handle = window_handles[0]
                        driver.switch_to.window(new_window_handle)
                        with open(os.getenv("PROCESS_ADS_PATH")+profile.username+'.txt', 'a+') as file:
                            file.write(url_ads+'\n')
                        
                        
                        while True:
                            if is_scroll_down_complete(driver):
                                try:
                                    time.sleep(random.uniform(10,20))
                                    links = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                                    random.shuffle(links)
                                    if len(links) > 0:
                                        action.move_to_element(links[0]).perform()
                                        time.sleep(random.uniform(5,10))
                                        action.click(links[0]).perform()
                                except:
                                    pass
                                break
                            action.scroll_by_amount(0, int(random.randint(400, 600))).perform()
                            time.sleep(random.uniform(5,10))
                            
                        driver.close()
                        driver.switch_to.window(current_window_handle)
                        time.sleep(random.uniform(5,10))
                        is_done = True
                if element_ads is None:
                    print('element_ads is null')
                    print(e.text)
                    check = e.find_elements(By.CSS_SELECTOR, 'a[href]')
                    for c in check:
                        print(c.get_attribute('href'))
                    url_post_ads = find_url_tweet(e)
                    print(url_post_ads)
                    if url_post_ads and url_post_ads not in urls_clicked:
                        is_done = True
                        action.scroll_to_element(e).perform()
                        time.sleep(random.uniform(5, 10))
                        print('click ads post')
                        action_details(wait, action, e)
                        with open(os.getenv("PROCESS_ADS_PATH")+profile.username+'.txt', 'a+') as file:
                                file.write(url_post_ads+'\n')
                        print('click normal')
            if is_done:
                break
            button_show_more = find_show_more_in_tweet(e)
            if button_show_more is not None:
                element_show_more = button_show_more
        if is_done:
            break
        if element_show_more is not None:
            try:
                action.scroll_to_element(element_show_more).perform()
                time.sleep(random.uniform(1, 3))
                action.click(element_show_more).perform()
            except Exception as e:
                print('exception click show more')
                print(e)
        time.sleep(random.uniform(1, 5))
        action.reset_actions()
        
        if element_show_more is None:
            try:
                if is_scroll_down_complete(driver):
                    break
                action.scroll_by_amount(0, int(random.randint(600, 900))).perform()
            except:
                break
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
    
    closeButton = find_back_navigation(wait)
    action.move_to_element(closeButton).perform()
    time.sleep(random.uniform(0.5, 2))
    action.click().perform()
    time.sleep(random.uniform(5, 10))
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
def scroll(driver, wait, action, profile, max_runtime, start_time):
    #New code
    white_accounts = read_white_account_from_file(os.getenv('PROFILE_PATH'))
    following_accounts = read_following_accounts_from_file(os.getenv("PROCESS_ACCOUNT_PATH")+profile.username+'.txt')
    
    urls_comment_by_main_account = read_urls_comment_by_main_account()
    main_accounts_not_yet_follow = [account for account in profile.accounts if account not in following_accounts]
    white_accounts_not_yet_follow = [account for account in white_accounts if account not in following_accounts]
    random.shuffle(white_accounts_not_yet_follow)

    #End code
    element = valid_twwets_by_twwets(wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]'))))[0]
    #element = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))[0]
    is_tab = is_tab_for_me(driver, wait)
    follow_count = random.randint(5, 15)
    follow_runtime = follow_count * 60
    post_count = random.randint(3,5)
    post_runtime = post_count * 60
    
    is_posted = False
    percent_post_tweet = 0.1
    count_error = 0
    while True:
        if action_start(driver) == 1:
            while True:
                if action_continue(driver) == 1:
                    break
        else :
            action_continue(driver)
        current_time = time.time()
        elapsed_time = current_time - start_time
        url_current = find_url_tweet(element)
        is_tweet_by_white_account = is_tweet_by_account(element, white_accounts)
        is_tweet_by_main_account = is_tweet_by_account(element, profile.accounts)
        
        if url_current is None:
            element = wait.until(lambda driver: waitNewElement(driver, url_current, True))
            continue
        
        total_comment = get_number_commnet(element)
        if profile.view_ads and is_tweet_by_main_account and total_comment >= 2:
            ads_tweets = read_following_accounts_from_file(os.getenv("PROCESS_ADS_POST")+profile.username+'.txt')
            if url_current not in ads_tweets:
                with open(os.getenv("PROCESS_ADS_POST")+profile.username+'.txt', 'a+') as file:
                        file.write(url_current+'\n')
                print('seeding ads')
                tweet_details = find_twwet_details(element)
                if (tweet_details and random_boolean(profile.percent_click_ads)):
                    action_tweet_ads(tweet_details, action, wait, profile, driver)
                    element = wait.until(lambda driver: waitNewElement(driver, url_current, False))
        
        #Post twwet
        if elapsed_time >= post_runtime and profile.post and is_posted is False:
            post_count += random.randint(3,5)
            post_runtime = post_count * 60
            if random_boolean(percent_post_tweet):
                is_posted = True
                action_push_tweet(wait,action, profile.content_post)
                action_by_pass_bot(driver, action)
                element = valid_twwets_by_twwets(wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]'))))[0]
                url_current = find_url_tweet(element)
            else:
                percent_post_tweet += 0.1
        #end Post twwet
        if (elapsed_time >= follow_runtime and len(white_accounts_not_yet_follow) > 0):
            follow_count += random.randint(5, 15)
            follow_runtime = follow_count * 60
            #search with account
            action_search_by_keyword(wait, action, white_accounts_not_yet_follow[0])
            time.sleep(random.uniform(2,10))
            elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
            for element in elements:
                tag_a = is_white_list_account(element, [white_accounts_not_yet_follow[0]])
                if tag_a:
                    action_follow_in_profile(wait, tag_a, profile.username, action, white_accounts_not_yet_follow[0])
                    time.sleep(random.uniform(3, 10))
                    break
            button_home = find_home_button(wait)
            action.move_to_element(button_home).perform()
            time.sleep(random.uniform(0.5,2))
            action.click(button_home).perform()
            time.sleep(random.uniform(3, 10))
            white_accounts, following_accounts, urls_comment_by_main_account, main_accounts_not_yet_follow, white_accounts_not_yet_follow = refresh(profile.username,profile.accounts)
            #exception
            try:
                element = wait.until(lambda driver: waitNewElement(driver, url_current, False))
            except:
                element = wait.until(lambda driver: waitNewElement(driver, url_current, True))
        if elapsed_time >= max_runtime:
            break
        
        is_tweet_find_main_account = len(main_accounts_not_yet_follow) > 0 and is_tweet_comment_by_main_account(element, urls_comment_by_main_account, main_accounts_not_yet_follow)
        if is_tweet_find_main_account:
            action_find_main_account(action, element, wait, main_accounts_not_yet_follow, profile.username)
            white_accounts, following_accounts, urls_comment_by_main_account, main_accounts_not_yet_follow, white_accounts_not_yet_follow = refresh(profile.username,profile.accounts)
            element = wait.until(lambda driver: waitNewElement(driver, url_current, False))

        ################
        action.reset_actions()
        action.scroll_to_element(element).perform()
        isVideo = is_video_tweet(element)

        #End code
        element_url_follow_account, user_follow_account = find_url_white_account(element, [*white_accounts_not_yet_follow, *main_accounts_not_yet_follow])


        if element_url_follow_account is not None and user_follow_account is not None:
            action_follow_in_profile(wait, element_url_follow_account, profile.username, action, user_follow_account)
            white_accounts, following_accounts, urls_comment_by_main_account, main_accounts_not_yet_follow, white_accounts_not_yet_follow = refresh(profile.username,profile.accounts)
            try:
                element = wait.until(lambda driver: waitNewElement(driver, url_current, False))
            except:
                element = wait.until(lambda driver: waitNewElement(driver, url_current, True))
        if isVideo == False: 
            #just like and comment in white accounts and main accounts (50% main)
            is_skip = False
            if (is_tweet_by_main_account):
                tweet_read = read_following_accounts_from_file(os.getenv("PROCESS_COMMENT_PATH")+profile.username+'.txt')
                is_skip = url_current in tweet_read
            
            isLike = (random_boolean(profile.like_rate) and is_tweet_by_white_account) or (is_tweet_by_main_account and random_boolean(profile.percent_like_main) and is_skip is False)
            isComment = (random_boolean(profile.comment_rate) and is_tweet_by_white_account) or (is_tweet_by_main_account and random_boolean(profile.percent_comment_main) and is_skip is False)
            isDetail = is_tweet_by_main_account and random_boolean(0.15) and is_skip is False
            time.sleep(random.uniform(5, 15))
            if isDetail:
                action_details(wait, action, element)
            if isLike:
                action_like(action, element)
            if isComment:
                action_comment(element, action, driver)
                action_by_pass_bot(driver, action)
            if is_tweet_by_main_account and is_skip is False:
                with open(os.getenv("PROCESS_COMMENT_PATH")+profile.username+'.txt', 'a+') as file:
                    file.write(url_current+'\n')

        try:
            element = wait.until(lambda driver: waitNewElement(driver, url_current, False))
        except Exception as e:
            element = wait.until(lambda driver: waitNewElement(driver, url_current, True))
            continue
            return
            count_error += 1
            element = wait.until(lambda driver: waitNewElement(driver, url_current, True))
            if (count_error == 2):
                print('switch tab')
                navigation = driver.find_element(By.CSS_SELECTOR, 'nav[aria-live="polite"][role="navigation"]')
                tab_list = navigation.find_elements(By.TAG_NAME, 'a')
                if (is_tab):
                    action.move_to_element(tab_list[1]).perform()
                    time.sleep(1)
                    action.click().perform()
                    is_tab = False
                else:
                    action.move_to_element(tab_list[0]).perform()
                    time.sleep(1)
                    action.click().perform()
                    is_tab = True
                time.sleep(10)
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
            if (count_error == 3):
                return
def get_number_commnet(element):
    try:
        reply = element.find_element(By.CSS_SELECTOR, 'div[data-testid="reply"]')
        number_comment = reply.find_element(By.CSS_SELECTOR, 'span[data-testid="app-text-transition-container"]')
        if number_comment and number_comment.text != '':
            return int(number_comment.text)
    except:
        return 0
    return 0
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
def action_login(driver, action, wait, profile):
    if driver.current_url == 'https://twitter.com/':
        try:
            button_sign_in = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[role="link"][data-testid="loginButton"]')))
            if button_sign_in:
                action.move_to_element(button_sign_in).perform()
                action.click(button_sign_in).perform()
                time.sleep(5)
                
                input_email = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"][type="text"]')))
                if input_email:
                    action.send_keys_to_element(input_email, profile.username).perform()
                    button_next = find_element_by_text(driver, By.TAG_NAME, 'span', 'Next')
                    if button_next:
                        action.move_to_element(button_next).perform()
                        action.click(button_next).perform()
                        time.sleep(5)
                        
                        input_password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"][type="password"]')))
                        if input_password:
                            action.send_keys_to_element(input_password, profile.password).perform()
                            time.sleep(5)
                            button_log_in = find_element_by_text(driver, By.TAG_NAME, 'span', 'Log in')
                            if button_log_in:
                                action.click(button_log_in).perform()
                                time.sleep(5)
                                
                                input_otp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="text"][type="text"][data-testid="ocfEnterTextTextInput"]')))
                                if input_otp:                                
                                    totp = pyotp.TOTP(profile.scret_key)
                                    action.send_keys_to_element(input_otp, totp.now()).perform()
                                    button_next = find_element_by_text(driver, By.TAG_NAME, 'span', 'Next')
                                    if button_next:
                                        action.move_to_element(button_next).perform()
                                        action.click(button_next).perform()
        except:
            print('exception login')
            print(profile.username)
            pass
def process_profile(profile):
    width = random.uniform(350,400)
    height = random.uniform(900,1080)
    max_runtime = profile.time_process * 60
    start_time = time.time()
    chrome_options = uc.ChromeOptions()
    preferences = {
        "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
        "webrtc.multiple_routes_enabled": False,
        "webrtc.nonproxied_udp_enabled" : False
    }
    chrome_options.add_experimental_option("prefs", preferences)
    chrome_options.add_argument("--window-size="+str(width)+","+str(height))
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--load-extension=C:/Users/Long/Downloads/extension")
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
    driver.get("https://twitter.com/")
    time.sleep(10)
    action_login(driver, action, wait, profile)
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
                scroll(driver,wait,action, profile, max_runtime, start_time)
            except StaleElementReferenceException as s:
                action_by_pass_bot(driver, action)
                print('StaleElementReferenceException')
                if action_start(driver) == 1:
                    while True:
                        if action_continue(driver) == 1:
                            break
                
                else :
                    action_continue(driver)
                action_login(driver, action, wait, profile)
                continue
            except NoSuchElementException as n:
                action_by_pass_bot(driver, action)
                if action_start(driver) == 1:
                    while True:
                        if action_continue(driver) == 1:
                            break
                else :
                    action_continue(driver)
                print('NoSuchElementException')
                print(n)
                action_login(driver, action, wait, profile)
                continue
            except Exception as e:
                print(e)
                if action_start(driver) == 1:
                    while True:
                        if action_continue(driver) == 1:
                            break
                else :
                    action_continue(driver)
                action_login(driver, action, wait, profile)
                break
        
            
    else:
        time.sleep(120)
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

#automation
def find_element_ads_in_elements(elements):
    try:
        for e in elements:
            span_elements = e.find_elements(By.TAG_NAME, 'span')
            for s in span_elements:
                if s.text == 'Ad':
                    return e
    except:
        return None
    return None
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
    
def action_comment(element, action, driver):
    print('comment')
    images = find_images(element)
    contents = find_contents(element)
    content_coment = None
    if contents is not None and len(images) > 0:
        try:
            content_coment = generate_comment_by_image_and_text(''.join(contents), images)
        except Exception as e:
            print('Exception text and images')
            print(e)
    else:
        try:
            content_coment = generate_comment_by_text(''.join(contents))
        except Exception as e:
            print('Exception only text')
            print(e)
    if (content_coment):
        button_comment = find_by_css_selector(element, 'div[role="button"][data-testid="reply"]')
        if button_comment:
            action.reset_actions()
            #action.move_to_element(button_comment).perform()
            time.sleep(random.uniform(0.5, 2))
            action.click(button_comment).perform()
            time.sleep(random.uniform(1, 5))

            input_text = find_by_css_selector_wait(driver, 'div[role="textbox"][data-testid="tweetTextarea_0"]')
            print('input_text')
            print(input_text)
            if input_text:
                #action.move_to_element(input_text).perform()
                time.sleep(random.uniform(0.5, 2))
                action.click(input_text).perform()
                time.sleep(random.uniform(10, 30))
                contents = list(content_coment)
                for c in contents:
                    action.send_keys(c).perform()
                    time.sleep(random.uniform(0.2, 1))
                time.sleep(random.uniform(0.5, 2))
                publish = find_by_css_selector_wait(driver,'div[role="button"][data-testid="tweetButton"]')
                if publish:
                    #action.move_to_element(publish).perform()
                    time.sleep(random.uniform(0.5, 2))
                    action.click(publish).perform()
                    time.sleep(random.uniform(5, 10))
                else:
                    wait = WebDriverWait(driver, 60)
                    button_back = find_button_back(wait)
                    if button_back:
                        action.click(button_back).perform()
                    button_discard = find_by_css_selector_wait(driver, 'div[role="button"][data-testid="confirmationSheetCancel"]')
                    if button_discard:
                        action.click(button_discard).perform()

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
#NEW
def action_like(action, element):
    buttonLike = find_by_css_selector(element, 'div[role="button"][data-testid="like"]')
    if buttonLike:
        action.move_to_element(buttonLike).perform()
        time.sleep(random.uniform(0.5, 2))
        action.click(buttonLike).perform()
        action.reset_actions()
        time.sleep(random.uniform(2, 5))

def action_find_main_account(action, element, wait, accounts, username):
    url_tweet = find_url_tweet_by_element(element)
    if (url_tweet):
        action.scroll_to_element(url_tweet).perform()
        time.sleep(random.uniform(0.5, 2))
        action.click(url_tweet).perform()
        time.sleep(random.uniform(1, 10))
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
        while True:
            is_done = False
            element_show_more = None
            for e in elements:
                account_main, account_follow = find_url_white_account(e, accounts)
                button_show_more = find_show_more_in_tweet(e)
                if button_show_more is not None:
                    element_show_more = button_show_more
                if (account_main is not None):
                    is_done = True
                    action_follow_in_profile(wait, account_main, username, action, account_follow)
                    break
            if is_done:
                break
            if element_show_more is not None:
                try:
                    action.scroll_to_element(element_show_more).perform()
                    time.sleep(random.uniform(1, 3))
                    action.click(element_show_more).perform()
                except Exception as e:
                    print('exception click show more')
                    print(e)
            time.sleep(random.uniform(1, 5))
            action.reset_actions()
            
            if element_show_more is None:
                try:
                    action.scroll_by_amount(0, int(random.randint(600, 900))).perform()
                except:
                    break
            elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')))
            
        button_home = find_home_button(wait)
        action.move_to_element(button_home).perform()
        time.sleep(random.uniform(0.5,2))
        action.click(button_home).perform() 
        

def action_follow_in_profile(wait, element, username, action, account_follow):
    action.scroll_to_element(element).perform()
    time.sleep(random.uniform(1, 3))
    action.click(element).perform()
    time.sleep(random.uniform(3, 10))
    button_follow = find_button_follow_profile(wait)
    if button_follow:
        time.sleep(random.uniform(0.5, 2))
        action.click(button_follow).perform()
        with open(os.getenv("PROCESS_ACCOUNT_PATH")+username+'.txt', 'a+') as file:
            file.write(account_follow+'\n')
    else:
        button_unfollow = find_button_unfollow_profile(wait)
        if button_unfollow:
            with open(os.getenv("PROCESS_ACCOUNT_PATH")+username+'.txt', 'a+') as file:
                file.write(account_follow+'\n')
    
    button_back = find_button_back(wait)
    if button_back:
        action.move_to_element(button_back).perform()
        time.sleep(random.uniform(0.5, 2))
        action.click(button_back).perform()
    
    action.reset_actions()
#ok
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
def find_element_by_text(element, by, tag_name, text):
    try:
        elements = element.find_elements(by, tag_name)
        for e in elements:
            if text == e.text:
                return e
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
    max_threads = int(os.getenv("MAX_THREAD"))
    profiles = read_profile_list_from_file(os.getenv("PROFILE_PATH"))
    random.shuffle(profiles)
    profiles_start = [profile for profile in profiles if profile.start]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_profile, profile) for profile in profiles_start]