import requests
import time
import pandas as pd
from datetime import datetime

import multiprocessing
from multiprocessing import Pool
import argparse
import sys

from bs4 import BeautifulSoup
import re # Xử lý đoạn mã có tag html

from tqdm import tqdm
import gc # Garbage Collector
import json


def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def convert_number(num):
    num = num.replace(",","")
    return float(num)

def create_user_data():
    book_id = []
    book_url = []
    username = []
    user_url = []
    user_rating = []
    return book_id, book_url, username, user_url, user_rating

def get_user_from_comments(book):
    
    source = requests.get(book)
    soup =   BeautifulSoup(source.text, 'html.parser')

    try:
      temp = soup.find("div", {"id": "bookReviews"})
    except:
      return None

    book_id, book_url, username, user_url, user_rating = create_user_data()

    try:
      reviews = temp.find_all('div', class_ = 'friendReviews elementListBrown')
    except:
      return None

    for review in reviews:
      try:
        book_id.append(str(soup.find("h1", {"id":"bookTitle"}).contents[0].strip()))
      except:
        book_id.append(None)
        
      # user_url / username
      info_user = review.find('a')
      user_url.append(str(info_user['href']))
      username.append(str(info_user['title']))
      
      # user_rating
      user_rating.append(len(review.find_all('span', class_="staticStar p10")))
      
      # book_url
      book_url.append(book)
      
    return pd.DataFrame({"book_id": book_id, "book_url": book_url, "username": username, 
                        "user_url": user_url, "user_rating": user_rating})

def create_null_dataframe_info_user():
    return pd.DataFrame({"book_id": [], "book_url": [], "username": [], 
                        "user_url": [], "user_rating": []})

if __name__ == '__main__':

    __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
    
    parser = argparse.ArgumentParser()

    parser.add_argument("--min_index", "-min", type=int, help="set min index")
    parser.add_argument("--max_index", "-max", type=int, help="set max index")

    args = parser.parse_args()
    
    Info_General_Book = pd.read_csv("Info_Book_Url.csv")
    list_url_book = Info_General_Book.Book_Urls.to_list()

    pool = Pool()
    
    min_index = args.min_index
    max_index = args.max_index
    print(min_index)
    for count in tqdm(range(min_index, max_index, 100)):
        
      info_user_detail = create_null_dataframe_info_user()
    
      inputs = list_url_book[count:count + 100]

      info_user_detail = pd.concat(pool.map(get_user_from_comments, inputs), ignore_index = True)

      info_user_detail.to_csv("info_user_detail.csv", mode = "a", index = False, header = False, encoding = "utf-8")
      time.sleep(2)
      
    
    

