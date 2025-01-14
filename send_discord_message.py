import requests
import json

webhook_url = "https://discord.com/api/webhooks/1328541041556721826/1TBRFZ25Vu-qJh7un3EOopyq91ybY7Xt85SVcKANP7z6vVA0H7SzfVBUa6EBCBnbn1KN"
def send_discord_message( content, username="에러", avatar_url=None):
    """
    Discord Webhook을 호출하여 메시지를 전송하는 함수.

    :param webhook_url: Discord Webhook URL
    :param content: 전송할 메시지 내용
    :param username: 사용자 이름 (선택 사항)
    :param avatar_url: 사용자 아바타 URL (선택 사항)
    """
    # 메시지 데이터 설정
    data = {
        "content": content
    }
    
    if username:
        data["username"] = username
    if avatar_url:
        data["avatar_url"] = avatar_url

    # POST 요청 보내기
    response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})

    # 응답 확인
    if response.status_code == 204:
        print("메시지가 성공적으로 전송되었습니다.")
    else:
        print(f"메시지 전송 실패: {response.status_code} {response.text}")

