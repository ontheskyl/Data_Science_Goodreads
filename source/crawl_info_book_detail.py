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


def create_null_dataframe_info_book_detail():
    return pd.DataFrame({"Book_Title": [], "Author_Name": [], "Author_Url": [],
                        "Description": [], "Rating": [], "Rating_Counts": [],
                        "Reviews_Counts": [], "Num_Pages": [], "Book_Format" :[],
                        "Time_publish": [], "Publisher": [], "ISBN": [], 
                        "Language": [], "Genres": [], "Book_Url": []})


def get_Detail_Book(url): # Lấy chi tiết từng url book

    time.sleep(0.5)
    source = requests.get(url)
    soup =   BeautifulSoup(source.text, 'html.parser')

    temp = soup.find("div", {"class": "last col stacked"})
    if temp == None:
        return None
    
    try:
        Image_url = str(temp.find("div", {"class": "bookCoverPrimary"}).find("img").get("src"))
    except:
        Image_url = None

    temp = temp.find("div", {"class": "last col"})
    if temp == None:
        return None
    
    try:
        Book_Title = str(temp.find("h1", {"id":"bookTitle"}).contents[0].strip())
    except:
        Book_Title = None

    try:
        Author = temp.find("a", {"class": "authorName"})
        Author_Url = str(Author.get("href"))
        Author_Name = str(Author.find("span").contents[0])
    except:
        Author_Url, Author_Name = None, None

    try:
        Description = temp.find("div", {"id": "description"}).findAll("span")
        if len(Description) > 1:
            Description = clean_html(str(Description[1]))
        else:
            Description = clean_html(str(Description[0]))
    except:
        Description = None

    try:
        Rating = convert_number(str(temp.find("span", {"itemprop": "ratingValue"}).contents[0].strip()))
    except:
        Rating = None

    try:
        Rating_Counts = convert_number(str(temp.find("meta", {"itemprop": "ratingCount"}).get("content")))
    except:
        Rating_Counts = None

    try:
        Reviews_Counts = convert_number(str(temp.find("meta", {"itemprop": "reviewCount"}).get("content")))
    except:
        Reviews_Counts = None

    temp = soup.find("div", {"id": "details"})
    if temp == None:
        return None
    
    try:
        Num_Pages = convert_number(str(temp.find("span", {"itemprop": "numberOfPages"}).contents[0])[:-5])
    except:
        Num_Pages = None

    try:
        Book_Format = str(temp.find("span", {"itemprop": "bookFormat"}).contents[0])
    except:
        Book_Format = None

    try:
        Publish = temp.findAll("div", {"class":"row"})
        Publish = [k for k in Publish if "Published" in str(k)][0].contents[0].strip().split("Published")[1].split("by")
        if len(Publish) > 1:
            Year_publish = Publish[0].strip()
            Publisher = Publish[1].strip()
        else:
            Year_publish = Publish[0].strip()
            Publisher = None
    except:
        Year_publish = None
        Publisher = None

    InfoDetail = temp.find("div", {"id":"bookDataBox"}).findAll("div", {"class": "clearFloats"})
    try:
        ISBN = [k for k in InfoDetail if "ISBN" in str(k)][0].find("div", {"class": "infoBoxRowItem"}).contents[0].strip()
        ISBN = str(ISBN)
    except:
        ISBN = None

    try:
        Language = [k for k in InfoDetail if "Edition Language" in str(k)][0].find("div", {"class": "infoBoxRowItem"}).contents[0].strip()
        Language = str(Language)
    except:
        Language = None

    temp = soup.find("div", {"class": "rightContainer"})
    Genres = {}
    if temp != None:
        try:
            temp = temp.findAll("div", {"class": "stacked"})[1].findAll("div", {"class": "elementList"})
            
            for element in temp:
                genre = element.find("div", {"class": "left"}).find("a").contents[0]
                users_number = convert_number(element.find("div", {"class": "right"}).find("a").contents[0][:-6])
                Genres[str(genre)] = users_number
        except:
            Genres = None
            
    else:
        Genres = None

    Genres = json.dumps(Genres)
    
    return pd.DataFrame({"Book_Title": Book_Title, "Author_Name": Author_Name, "Author_Url": Author_Url,
                        "Description": Description, "Rating": Rating, "Rating_Counts": Rating_Counts,
                        "Reviews_Counts": Reviews_Counts, "Num_Pages": Num_Pages, "Book_Format" :Book_Format,
                        "Time_publish": Year_publish, "Publisher": Publisher, "ISBN": ISBN, 
                        "Language": Language, "Genres": Genres, "Book_Url": url}, index=[0])


if __name__ == '__main__':

    __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
    
    parser = argparse.ArgumentParser()

    parser.add_argument("--min_index", "-min", type=int, help="set min index")
    parser.add_argument("--max_index", "-max", type=int, help="set max index")

    args = parser.parse_args()

    
    Info_General_Book = pd.read_csv("Info_Book_Url.csv")


    list_url_book = Info_General_Book.Book_Urls.to_list()
    
    pool = Pool()
    
    info_book_detail = create_null_dataframe_info_book_detail()
    
    inputs = list_url_book[args.min_index : args.max_index]

    info_book_detail = pd.concat(pool.map(get_Detail_Book, inputs), ignore_index = True)

    info_book_detail.to_csv("info_book_detail_ver_2.csv", mode = "a", index = False, header = False, encoding = "utf-8")
