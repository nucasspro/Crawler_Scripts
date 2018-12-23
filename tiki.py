import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import mysql.connector
from threading import Thread


BASE_URL = ["https://tiki.vn/bestsellers-month/lam-dep-suc-khoe/c1520?p=1&_lc=Vk4wMzkwMjQwMDg%3D", 
            "https://tiki.vn/bestsellers-month/lam-dep-suc-khoe/c1520?p=2&_lc=Vk4wMzkwMjQwMDg%3D"]
HOST = r"https://tiki.vn"
list_data = []


def getHTML(URL):
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        'DNT': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://tiki.vn/bestsellers-month/lam-dep-suc-khoe/c1520?p=2&_lc=Vk4wMzkwMjQwMDg%3D',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'vi,en;q=0.9,en-US;q=0.8',
    }

    response = requests.request("GET", URL, headers=headers)
    page_soup = BeautifulSoup(response.text, "html.parser")
    response.close()
    return page_soup


def getItems(page_soup):
    div_infomation = page_soup.find_all("div", {"class": "infomation"})
    urls = []
    for item in div_infomation:
        urls.append(item.p.a["href"])
    return urls


def getData(url):
    page_html = getHTML(url)
    item = {}
    try:
        item.update({"name": page_html.find_all("h1", {"class": "item-name"})[0].text.strip() })

        item.update({"url": url})
        
        product_detail_price_info = page_html.find_all("div", {"class": "col-xs-7 no-padding-right product-info-block"})
        
        item.update({"regular_price": product_detail_price_info[0].find_all("span", {"id": "span-list-price"})[0].text.strip()[:-2]})
        item.update({"offer_price": product_detail_price_info[0].find_all("span", {"id": "span-price"})[0].text.strip()[:-2]})
       
        if (page_html.find_all("div", {"class": "top-feature-item bullet-wrap"}) != 0):
            short_detail = page_html.find_all("div", {"class": "top-feature-item bullet-wrap"})[0]
            item.update({"short_detail": "".join([str(x) for x in short_detail]).strip()})
        else:
            item.update({"short_detail": ""})

        item.update({"image": page_html.find_all("img", {"id": "product-magiczoom"})[0]["src"]})

        if (page_html.find_all("div", {"class": "product-description"}) != 0):
            long_detail = page_html.find_all("div", {"class": "product-description"})[0].div
            item.update({"long_detail": "".join([str(x) for x in long_detail]).strip()[:-106]})
        else:
            item.update({"long_detail": ""})

        return item
    except Exception as ex:
        print(str(ex))
        return


def sleep_scrap():
    sleep(randint(5, 20))


def insertData(list_data):
    cnx = mysql.connector.connect(user="root", password="", host="127.0.0.1", database="tiki")
    cursor = cnx.cursor()
    for item in list_data:
        print("========================Inserting=========================")
        if (item != None):
            query = """INSERT INTO tiki (Name, ShortDetail, LongDetail, RegularPrice, OfferPrice, Image, URL) SELECT %s, %s, %s, %s, %s, %s, %s FROM DUAL WHERE NOT EXISTS (SELECT * FROM tiki WHERE URL = %s) LIMIT 1""" 
            cursor.execute(query, (str(item.get("name")), str(item.get("short_detail")), str(item.get("long_detail")), item.get("regular_price"), item.get("offer_price"), str(item.get("image")), str(item.get("url")), str(item.get("url"))))
    cnx.commit()
    cursor.close()
    cnx.close()


def runScrapy(url):
    item = getData(url)
    list_data.append(item)


def main():
    thread_list = []
    print("========================Starting==========================")
    for url in BASE_URL:
        page_soup = getHTML(url)
        urls = getItems(page_soup)
        for item in urls:
            thread = Thread(target=runScrapy, args=(item,))
            print("========================Start Thread==========================")
            thread.start()
            thread_list.append(thread)
        for item in thread_list:
            item.join()
    insertData(list_data)
    print("========================DONE==========================")


if __name__ == "__main__":
    main()


# CREATE TABLE tiki (
# Id INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
# Name TEXT NOT NULL,
# ShortDetail TEXT NOT NULL,
# LongDetail TEXT NOT NULL,
# RegularPrice Float NOT NULL,
# OfferPrice Float NULL,
# Image TEXT NULL,
# URL TEXT NOT NULL
# )