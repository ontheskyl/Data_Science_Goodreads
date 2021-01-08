import requests
import time
import pandas as pd

import multiprocessing
from multiprocessing import Pool
import argparse
import sys

from bs4 import BeautifulSoup


def convert_number(num):
    num = num.replace(",","")
    return float(num)


def create_rating_data():
    url_book = []
    book_title = []
    username = []
    user_url = []
    user_rating = []
    
    return url_book, book_title, username, user_url, user_rating


def multi_run_wrapper(args):
   return get_info_rating_each_page(*args)


def get_info_rating_each_page(nickname, page, temp_username, temp_user_url):
    
    source = requests.get("https://www.goodreads.com/review/list/{}?page={}&print=true&shelf=read&sort=date_added&view=table".format(nickname, page))
    soup =   BeautifulSoup(source.text, 'html.parser')

    url_book, book_title, username, user_url, user_rating = create_rating_data()

    try:
        temp = soup.find("tbody", {"id": "booksBody"})
        temp = temp.findAll("tr", {"class": "bookalike review"})
    except:
        return None
        
    for (id, book) in enumerate(temp):
        try:
            url_book.append("https://www.goodreads.com" + str(book.find("td", {"class": "field title"}).find("a").get("href")))
        except:
            url_book.append(None)
        try:
            book_title.append(str(book.find("td", {"class": "field title"}).find("a").contents[0]).strip())
        except:
            book_title.append(None)
        try:
            user_rating.append(len(book.find("td", {"class": "field rating"}).findAll("span", {"class": "staticStar p10"})))
        except:
            user_rating.append(None)
            
        username.append(temp_username)
        user_url.append("https://www.goodreads.com" + temp_user_url)

    return pd.DataFrame({"url_book": url_book, "book_title": book_title, "username": username, 
                        "user_url": user_url, "user_rating": user_rating})


def get_user_rating_book(nickname):

    user_rating_book = pd.DataFrame({"url_book": [], "book_title": [], "username": [], 
                                    "user_url": [], "user_rating": []})
    
    source = requests.get("https://www.goodreads.com/review/list/{}?page=1&print=true&shelf=read&sort=date_added&view=table".format(nickname))
    soup =   BeautifulSoup(source.text, 'html.parser')
    
    try:
        temp = soup.find("div", {"id": "header"}).findAll("a")
    except:
        return None
    
    temp_username = str(temp[1].contents[0])
    temp_user_url = str(temp[1].get("href"))

    try:
        pages = min(100, int(soup.find("div", {"id": "reviewPagination"}).findAll("a")[-2].contents[0]))
    except:
        pages = 1

    inputs = [(nickname, i, temp_username, temp_user_url) for i in range(1, pages + 1)]
        
    url_book, book_title, username, user_url, user_rating = create_rating_data()

    pool = Pool()

    user_rating_book = pd.concat(pool.map(multi_run_wrapper, inputs), ignore_index = True)
        

    return user_rating_book


if __name__ == '__main__':

    __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
    
    parser = argparse.ArgumentParser()

    parser.add_argument("--nickname", "-name", type=str, help="set nickname")


    args = parser.parse_args()

    
    user_rating_book = get_user_rating_book(args.nickname)
    
    if user_rating_book is not None:
        user_rating_book.to_csv("user_rating_book.csv", mode = "a", index = False, header = False, encoding = "utf-8")
    
