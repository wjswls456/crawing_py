from datetime import datetime, timedelta
import os
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from notion_client import Client
import time
import requests

from quickstart import Calendar, insert_google_calendar_day, insert_google_calendar_time
from send_discord_message import send_discord_message

from dotenv import load_dotenv

load_dotenv()
# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 브라우저를 표시하지 않음 (옵션)
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")


# Notion API 키와 데이터베이스 ID를 설정합니다.
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
DATABASE_ID = os.getenv('DATABASE_ID')

notion = Client(auth = NOTION_API_KEY)


def fetch_bithumb_latest():

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    url = "https://feed.bithumb.com/notice?category=8&page=1"    
    link_array = []

    try:
        time.sleep(2)
        driver.get(url)
        time.sleep(2)
        

        notice_list = driver.find_elements(By.CSS_SELECTOR, ".NoticeContentList_notice-list__i337r li")
        index = 0
        # <li> 요소 반복 출력
        for notice in notice_list:

            if index >= 15:
                break

            title = notice.find_element(By.CSS_SELECTOR, ".NoticeContentList_notice-list__link-title__nlmSC").text
            index +=1

            if "에어드랍" in title or "기념 거래" in title:
                link = notice.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                link_array.append(link)         

        return link_array

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()  # 드라이버 종료는 finally 블록에서 처리



def fetch_bithumb_latest_detail(link,coin_list):

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    notion_database_coin_name = coin_list
    
    try:
            time.sleep(random.uniform(1,5))
            driver.get(link)
            time.sleep(2)
        

            ul_tags = driver.find_elements(By.XPATH, "//ul[@style='list-style-type: square;']")
            

            if ul_tags:
                    ul_tags = ul_tags[:-1]  # 마지막 요소 삭제

            for ul in ul_tags:
                li_tags = ul.find_elements(By.TAG_NAME, 'li')

                if len(li_tags) < 5:
                    continue
                

                period = li_tags[0].text.replace(" ","").replace("기간:","")

                if contains_valid_date_format(period):
                    print(period)
                else:
                    continue

                start_date = period.split("~")[0].split("(")[0]
                end_date = period.split("~")[1].split("(")[0]

                target = li_tags[1].text.replace(" ","").replace("대상:기간내","")
                if "를" in target:
                    coin_name = target.split("를")[0]
                elif "을" in target:
                    coin_name = target.split("을")[0]

                continuous_trading_day = target.split("일")[0][-1]

                event_payout_date = ''.join(re.findall(r'[0-9.]+',li_tags[4].text.replace(" ","").split("(")[0]))
                

                summary = "빗썸"+coin_name+"사고 팔기"

                notice = Notice(start_date,end_date , coin_name , event_payout_date,link)

                print("===================1================")
                print("coin_name : ",coin_name)


                # 중복된 코인 이름이 없는 경우
                if contains_character(notion_database_coin_name,notice.coin_name) : 
                    print("===================2================")

                    # 노션에 값을 추가 해야함
                    # 구글 캘린더에 추가해야함
                    continuous_trading_day_int = convert_to_int(continuous_trading_day)
                    if continuous_trading_day_int is not None :
                        event_payout_calendar = Calendar(convert_to_evening_time(event_payout_date,20),convert_to_evening_time(event_payout_date,21),"빗썸 "+coin_name+"에어 드랍",link)
                        insert_google_calendar_time(event_payout_calendar)
                        calendar = Calendar(convert_to_date(start_date),convert_to_date(end_date),summary,link)
                        google_event_data =insert_google_calendar_day(calendar)
                        add_to_notion_database(coin_name,summary,convert_to_date(start_date),add_to_date(start_date,continuous_trading_day-1),google_event_data['id'])
                        
                            
    except Exception as e:
        
        error_period = li_tags[0].text.replace(" ","")
        message = f"start_date: {start_date}, end_date: {end_date}, coin_name: {coin_name}, continuous_trading_day: {continuous_trading_day}, event_payout_date: {event_payout_date}/ 홈페이지 파싱 기간 문자열 : {error_period}"
        send_discord_message(message)
        send_discord_message(str(e))
    
    finally:
        driver.quit()  # 드라이버 종료는 finally 블록에서 처리

       



def convert_to_int(value):
    """문자열을 정수로 변환합니다. 변환할 수 없으면 None을 반환합니다."""
    try:
        return int(value)  # 문자열을 정수로 변환
    except ValueError:
        print(f"{value}는 정수로 변환할 수 없습니다.")
        return None  # 변환 실패 시 None 반환

def contains_character(arr, char):
    for element in arr:
        if element == char:
            return False
    return True

class Notice:
    def __init__(self, start_date,end_date, coin_name, event_payout_date,location):
        self.start_date = start_date
        self.end_date = end_date
        self.coin_name = coin_name
        self.event_payout_date = event_payout_date
        self.location=location


def add_to_date(date_str,day):
    # 입력된 날짜 문자열의 형식을 파악하여 datetime 객체로 변환
    date = datetime.strptime(date_str, "%Y.%m.%d")
    # 하루 더하기
    date_plus_one = date + timedelta(days=day)
    return date_plus_one.strftime("%Y-%m-%d")

def convert_to_date(date_str):
    # 입력된 날짜 문자열의 형식을 파악하여 datetime 객체로 변환
    date = datetime.strptime(date_str, "%Y.%m.%d")
    return date.strftime("%Y-%m-%d")
    


def convert_to_evening_time(date_str,hour):
    # 입력된 날짜 문자열의 형식을 파악하여 datetime 객체로 변환
    date = datetime.strptime(date_str, "%Y.%m.%d")
    
    # 저녁 8시로 시간 설정 (20:00:00)
    evening_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    # ISO 8601 형식으로 변환하여 반환
    return evening_time.isoformat()  # 서울 시간대 (+09:00)


def add_to_notion_database(coin_name,summary,start,end,event_id):
    try:
        # 페이지 생성
        properties = {
        "이벤트_ID":{
            "rich_text":[
                {
                    "text":{
                        "content":event_id
                    }
                }
            ]
        }
        ,
        "설명":{
            "rich_text":[
                {
                    "text":{
                        "content" : summary
                    }
                }
            ]
        },

        "이름": {
            "title": [
                {
                    "text": {
                        "content": coin_name
                    }
                }
            ]
        },
        "시작일": {
            "date": {
                "start" : start
            }
        },
        "종료일":{
            "date": {
                "start":end
            }
        },
        "생성일":{
            "date":{
                "start":get_korean_time()
            }
        }
        
        
    }


        response = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )
        print("데이터가 성공적으로 추가되었습니다.")
    except Exception as e:
        print("데이터 추가 중 오류 발생:", e)

def contains_valid_date_format(text):
    # YYYY.MM.DD 형식의 정규 표현식
    pattern = r'\b\d{4}\.\d{2}\.\d{2}\b'
    
    # 정규 표현식을 사용하여 형식 체크
    return bool(re.search(pattern, text))


def get_korean_time():
    utc_now = datetime.utcnow()  # UTC 현재 시간
    korean_time = utc_now   # 한국 시간 (UTC+9)으로 변환
    return korean_time.isoformat()

def get_coin_list():
    notion_database_coin_name = []
    response = notion.databases.query(
         DATABASE_ID,
         sort=[{"property": "순번", "direction": "aescending"}],
         page_size=10
         )


    if response.get('results'):
         for page in response['results']:
              name_property = page['properties'].get('이름')
              if name_property:
                   title = name_property['title']
                   if title:
                        name_value = title[0]['text']['content'] if title else '제목 없음'
                        notion_database_coin_name.append(name_value)
    return notion_database_coin_name

bithumb_site=fetch_bithumb_latest()
coin_list =get_coin_list()

for link in bithumb_site:
    time.sleep(5)
    fetch_bithumb_latest_detail(link,coin_list)




