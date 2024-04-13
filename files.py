import os
import numpy as np
import pandas as pd

class UrlPost:
    def __init__(self, url, username):
        self.url = url
        self.username = username
class HashTag:
    def __init__(self, keyword, username):
        self.keyword = keyword
        self.username = username
class Profile:
    def __init__(self, name, password, scret_key, proxy, profile_dir, like_rate, comment_rate, view_ads, user_ads, time_process, start, accounts, work, post, content_post, percent_click_ads,percent_comment_main,percent_like_main):
        self.username = name
        self.password = password
        self.scret_key = scret_key
        self.proxy = proxy
        self.profile_dir = profile_dir
        self.like_rate = float(like_rate)
        self.comment_rate = float(comment_rate)
        self.view_ads = bool(view_ads)
        self.user_ads = user_ads
        self.time_process = int(time_process)
        self.start = bool(start)
        if accounts:
            self.accounts = str(accounts).split(',')
        else:
            self.accounts = []
        self.work = bool(work)
        self.post = bool(post)
        self.content_post = content_post
        self.percent_click_ads = float(percent_click_ads)
        self.percent_comment_main = float(percent_comment_main)
        self.percent_like_main = float(percent_like_main)

def read_profile_list_from_file1(file_path, sheet_name):
    profiles = []
    ser = pd.read_excel(file_path,sheet_name=sheet_name, header=None, skiprows=1)
    num_rows = len(ser)  # Số hàng trong Series
    for row_index in range(num_rows):
        value = ser.iloc[row_index]
        profile = Profile(*value)
        profiles.append(profile)
    return profiles

def read_profile_list_from_file(file_path):
    profiles = []
    ser = pd.read_excel(file_path,sheet_name='Account X', header=None, skiprows=1)
    num_rows = len(ser)  # Số hàng trong Series
    for row_index in range(num_rows):
        value = ser.iloc[row_index]
        profile = Profile(*value)
        profiles.append(profile)
    return profiles
    
        
def read_white_account_from_file(file_path):
    white_list = []
    ser = pd.read_excel(file_path,sheet_name='white_list', header=None)
    num_rows = len(ser)
    for row_index in range(num_rows):
        value = ser.iloc[row_index]
        white_list.append(value[0])
    return white_list



#New code
def read_urls_comment_by_main_account():
    urls = []
    ser = pd.read_excel(os.getenv('PROFILE_PATH'),sheet_name='Url_comment', header=None)
    num_rows = len(ser)
    for row_index in range(num_rows):
        value = ser.iloc[row_index]
        url_post = UrlPost(*value)
        urls.append(url_post)
    return urls

def read_hashtag_comment_by_main_account():
    urls = []
    ser = pd.read_excel(os.getenv('PROFILE_PATH'),sheet_name='HashTags', header=None)
    num_rows = len(ser)
    for row_index in range(num_rows):
        value = ser.iloc[row_index]
        url_post = HashTag(*value)
        urls.append(url_post)
    return urls

########
def read_following_accounts_from_file(file_path):
    accounts = []
    with open(file_path, 'a+') as file:
        file.seek(0)
        for line in file:
            account = line.strip()
            accounts.append(account)
    return accounts