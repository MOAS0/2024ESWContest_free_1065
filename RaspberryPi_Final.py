import adafruit_dht
import serial
from RPi import GPIO
import board
import time
import firebase_admin
from firebase_admin import credentials, firestore, db

# Initialize Firebase
cred = credentials.Certificate('path/to/your-firebase-adminsdk.json')  # Firebase 인증서 파일 경로
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-firebase-database-url/'  # Firebase 데이터베이스 URL
})

# Initialize serial communication
ser = serial.Serial(
    port='/dev/ttyACM0',  # 시리얼 포트 설정
    baudrate=9600,  # 통신 속도 설정
    parity=serial.PARITY_NONE,  # 패리티 비트 없음
    stopbits=serial.STOPBITS_ONE,  # 정지 비트 1개
    bytesize=serial.EIGHTBITS,  # 데이터 비트 8개
    timeout=8  # 타임아웃 시간 설정
)
ser.isOpen()

# Main loop
while True:
    # 시리얼 포트에 수신된 데이터가 있을 때
    if ser.in_waiting > 0:
        dir_ref = db.reference()  # Firebase 데이터베이스 참조 생성
        dir_ref.update({'trigger': 1})  # 'trigger' 값을 1로 업데이트
        
        # 시리얼 포트에서 한 줄의 데이터를 읽어와서 디코딩 후 리스트로 변환
        text = list(ser.readline().decode('utf-8').strip().split())
        
        # 데이터의 첫 번째 값이 'bad,'일 때
        if text[0] == 'bad,':
            dir_ref.update({'weight_state': 'bad'})  # 'weight_state' 값을 'bad'로 업데이트
            dir_ref.update({'weight': str(text[1])})  # 'weight' 값을 업데이트
        
        # 데이터의 첫 번째 값이 'good,'일 때
        elif text[0] == 'good,':
            dir_ref.update({'weight_state': 'good'})  # 'weight_state' 값을 'good'으로 업데이트
            dir_ref.update({'weight': str(text[1])})  # 'weight' 값을 업데이트

    dir_ref = db.reference('wafer')  # 'wafer' 경로의 데이터베이스 참조 생성
    wafer_state = dir_ref.get()  # 현재 'wafer' 상태를 가져옴
    
    # 'wafer' 상태가 'normal'일 때
    if wafer_state == 'normal':
        ser.write("normal\n".encode())  # 시리얼 포트로 'normal' 메시지 전송
        if(ser.in_waiting > 0):
            text = list(ser.readline().decode('utf-8').strip().split())
            if text[0] == 'cho':
                db.reference().update({'wafer': 'neutral'})  # 'wafer' 상태를 'neutral'로 업데이트
    
    # 'wafer' 상태가 'broken'일 때
    elif wafer_state == 'broken':
        ser.write("broken\n".encode())  # 시리얼 포트로 'broken' 메시지 전송
        if(ser.in_waiting > 0):
            text = list(ser.readline().decode('utf-8').strip().split())
            if text[0] == 'cho':
                db.reference().update({'wafer': 'neutral'})  # 'wafer' 상태를 'neutral'로 업데이트

    time.sleep(0.1)  # 0.1초 대기
