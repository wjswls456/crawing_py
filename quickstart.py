import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv


# 서비스 계정 키 파일 경로
SERVICE_ACCOUNT_FILE = os.getenv('ACCOUNT_JSON')
print("SERVICE_ACCOUNT_FILE : ",SERVICE_ACCOUNT_FILE)
print("SERVICE_ACCOUNT_FILE_type : ",type(SERVICE_ACCOUNT_FILE))
service_account_info = json.loads(SERVICE_ACCOUNT_FILE)
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = os.getenv('CALENDAR_ID')

def create_service():
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )
    return build('calendar', 'v3', credentials=creds)

def create_event(event_details, all_day=True):
    
    if all_day:
        event = {
            'summary': event_details.summary,
            'location': event_details.location,
            'description': event_details.description,
            'start': {
                'date': event_details.start,  # 시작 날짜
            },
            'end': {
                'date': event_details.end,  # 종료 날짜
            },
            'timeZone': 'Asia/Seoul'
        }
    else:
        event = {
            'summary': event_details.summary,
            'location': event_details.location,
            'description': event_details.description,
            'start': {
                'dateTime': event_details.start,  # 시작 시간 (ISO 8601 형식)
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': event_details.end,  # 종료 시간 (ISO 8601 형식)
                'timeZone': 'Asia/Seoul',
            },
            'reminders':{
                'useDefault': False,
                'overrides':{
                    {'method': 'popup', 'minutes': 10},
                }
            }
        }
    return event

def insert_event(event):
    
    service = create_service()
    print(event)
    
    try:
        event_response = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print('이벤트가 추가되었습니다.')
        print("event_response['id'] : ", event_response['id'])
        print(event_response)
        return event_response
    except Exception as e:
        print(f'이벤트 추가 중 오류 발생: {e}')
        return False

def insert_google_calendar_day(event_details):
    """하루 종일 이벤트를 추가합니다."""
    event = create_event(event_details, all_day=True)
    return insert_event(event)


def insert_google_calendar_time(event_details):
    """특정 시간 이벤트를 추가합니다."""
    event = create_event(event_details, all_day=False)
    return insert_event(event)


class Calendar:
    def __init__(self, start_date,end_date, summary,location):
        self.start = start_date
        self.end = end_date
        self.summary = summary
        self.location = location
        self.description = "빗썸 에러 드랍 이벤트"

