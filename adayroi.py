import requests
from bs4 import BeautifulSoup
from time import sleep
from random import randint
import mysql.connector
from threading import Thread


BASE_URL = ["https://www.adayroi.com/ao-nu-c3?q=%3Abestselling-desc&page=0","https://www.adayroi.com/ao-nu-c3?q=%3Abestselling-desc&page=1"]
HOST = r"https://www.adayroi.com"
list_data = []


def getHTML(URL):
    headers = {
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
        "DNT": "1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "vi,en;q=0.9,en-US;q=0.8",
    }

    response = requests.request("GET", URL, headers=headers)
    page_soup = BeautifulSoup(response.text, "html.parser")
    response.close()
    return page_soup


def getItems(page_soup):
    product_container = page_soup.find_all("div", {"class": "product-list__container"})
    product_list_container = product_container[0].find_all("a", {"class":"product-item__thumbnail"})
    urls = []
    for item in product_list_container:
        urls.append(HOST + item["href"])
    return urls


def getData(url):
    page_html = getHTML(url)
    item = {}
    try:
        item.update({"name": page_html.find_all("div", {"class": "product-detail__title"})[0].h1.text.strip() })
        item.update({"url": url})
        
        product_detail_price_info = page_html.find_all("div", {"class": "product-detail__price-info"})
        
        # Voi item co gia goc va gia khuyen mai
        if ("price-info__sale" in str(product_detail_price_info[0]) and "price-info__original" in str(product_detail_price_info[0])):
            item.update({"regular_price": product_detail_price_info[0].find_all("span", {"class": "price-info__original"})[0].text.strip()[:-1].replace(".", "")})
            item.update({"offer_price": product_detail_price_info[0].find_all("span", {"class": "price-info__sale"})[0].text.strip()[:-1].replace(".", "")})
        # Voi item co gia sieu khuyen mai
        elif "price-info__super-sale" in str(product_detail_price_info[0]):
            item.update({"regular_price": product_detail_price_info[0].find_all("span", {"class": "price-info__super-sale"})[0].b.text.strip()[:-1].replace(".", "")})
            item.update({"offer_price": ""})
        # Voi item chi co gia goc
        else:
            item.update({"regular_price": product_detail_price_info[0].find_all("span", {"class": "price-info__sale"})[0].text.strip()[:-1].replace(".", "")})
            item.update({"offer_price": ""})
        
        if (page_html.find_all("li", {"class":"nobullet"}) != 0):
            item.update({"short_detail": str(page_html.find_all("li", {"class":"nobullet"})[0].ul)})
        else:
            item.update({"short_detail": ""})

        item.update({"image":page_html.find_all("meta", {"property": "og:image"})[0]["content"]})

        product_detail_description = page_html.find_all("div", {"class": "product-detail__description"})[0]
        item.update({"long_detail": "".join([str(x) for x in product_detail_description]).strip()})  

        return item
    except Exception as ex:
        print(str(ex))
        return


def sleep_scrap():
    sleep(randint(5, 20))


def insertData(list_data):
    cnx = mysql.connector.connect(user="root", password="", host="127.0.0.1", database="adayroi")
    cursor = cnx.cursor()
    for item in list_data:
        print("========================Inserting=========================")
        if (item != None):
            query = """INSERT INTO adayroi (Name, ShortDetail, LongDetail, RegularPrice, OfferPrice, Image, URL) SELECT %s, %s, %s, %s, %s, %s, %s FROM DUAL WHERE NOT EXISTS (SELECT * FROM adayroi WHERE URL = %s) LIMIT 1""" 
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


# CREATE TABLE adayroi (
# Id INT(11) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
# Name TEXT NOT NULL,
# ShortDetail TEXT NOT NULL,
# LongDetail TEXT NOT NULL,
# RegularPrice Float NOT NULL,
# OfferPrice Float NULL,
# Image TEXT NULL,
# URL TEXT NOT NULL
# )