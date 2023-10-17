import requests
import logging
import json
from bs4 import BeautifulSoup
import aria2p #python3.6 -m pip install aria2p[tui]
import dbm


log = logging.getLogger("Main")
logging.basicConfig(level=logging.INFO)

BT_URL = "https://cdn.btlm.top:65533/s"
ARIA2_HOST = "http://localhost"
ARIA2_PORT = 6800
ARIA2_SECRET = ""

def search_url(keywords) -> str:
    params = {
        "word": keywords,
        "sort": "viewnum"
    }
    headers = {
        "Host": "cdn.btlm.top:65533",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,en-US;q=0.8,en;q=0.7,zh;q=0.5,zh-TW;q=0.3,zh-HK;q=0.2",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://cdn.btlm.top:65533/?host=hu.btlm.pro&v=1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "iframe",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }
    ret = requests.get(BT_URL, params, headers=headers)
    if not ret.ok:
        log.warning("request: url={}, param={}, resp={}".format(BT_URL, params, ret.content.decode('u8')))
        raise Exception("resp exception. " + ret.content.decode('u8'))
    ret_s = BeautifulSoup(ret.content.decode('u8'), 'html.parser')
    links = ret_s.select(".result-resource-title")
    # [{name : url}]
    def parse_result(links):
        ret_list = []
        for i in links:
            ret = {}
            name = i.text
            url = "magnet:?xt=urn:btih:" + i.get('href')[6:]
            ret.setdefault(name, url)
            ret_list.append(ret)
        return ret_list
            
    return parse_result(links)

def log_error(keywords):
    with open("error.txt", "a") as f:
        f.write(keywords+"\n")
        
def already_download(keywords, value) -> bool:
    # con = sqlite3.connect("meta.db")
    # def init_db():
    #     ddl_downloaded = """
    #         create table if not exists downloaded(
    #                 id       INTEGER PRIMARY KEY UNIQUE AUTOINCREMENT,
    #                 magnet   TEXT    NOT NULL,
    #                 keywords TEXT,
    #                 date     TEXT
    #             );
    #     """
    #     cur = con.cursor()
    #     cur.execute(ddl_downloaded)
    # cur.execute("select ")
    db = None
    try:
        db = dbm.open("meta.db", "c")
        return keywords.strip() in db or value.strip() in db.values()
    finally:
        if db is not None:
            db.close()
        
def record_download(keywords, value):
    db = None
    try:
        db = dbm.open("meta.db", "c")
        db.setdefault(keywords.strip(), value)
    finally:
        if db is not None:
            db.close()
    

def download_magnet(magnet: str):
    aria2 = aria2p.API(
        aria2p.Client(
            host=ARIA2_HOST,
            port=ARIA2_PORT,
            secret=ARIA2_SECRET
        )
    )
    aria2.add_magnet(magnet)
    
def download(keywords):
    urls = search_url(keywords)
    if len(urls) == 0:
        log_error(keywords)
        log.warning("keyword {} no url found".format(keywords))
        return
    select_obj:dict = urls[0]
    name = list(select_obj.keys())[0]
    magnet = select_obj.get(name)
    if already_download(name, magnet):
        log.info("already download file {}, magnet {}".format(name, magnet))
    else:
        record_download(name, magnet)
    log.info("download {}, url={}".format(name, magnet))
    download_magnet(magnet)
    
def download_strs(keywords):
    keyword_ary = keywords.split(" ")
    for k in keyword_ary:
        nk = k.strip()
        if nk == "":
            continue
        download(nk)
    

if __name__ == "__main__":
    print("please enter keywords, split by space.")
    download_strs(input())