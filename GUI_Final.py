import tkinter as tk
from tkinter import PhotoImage
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

class ImageUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Semiconductor Process Monitoring')
        self.root.geometry('1440x900')
        self.root.config(bg='#808080')  # 배경 색을 회색으로 설정

        # Firebase 초기화
        cred = credentials.Certificate('path/to/your-firebase-adminsdk.json')  # 인증 정보 파일 경로
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://your-database-url.firebaseio.com/'  # 데이터베이스 URL
        })

        # Firebase 데이터 참조
        self.wafer_ref = db.reference('wafer')
        self.accuracy_ref = db.reference('accuracy')
        self.weight_ref = db.reference('weight')
        self.weight_state_ref = db.reference('weight_state')
        self.image_ref = db.reference('image_path')

        # 메인 프레임 생성
        main_frame = tk.Frame(root, bg='#808080', pady=20, padx=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 이미지 표시 프레임
        image_frame = tk.Frame(main_frame, bg='#808080')
        image_frame.pack(side=tk.LEFT, padx=20)

        # 데이터를 표시할 프레임
        data_frame = tk.Frame(main_frame, bg='#808080')
        data_frame.pack(side=tk.LEFT, padx=20)

        # 이미지를 표시할 라벨 생성
        self.image_label = tk.Label(image_frame, bg='#808080')
        self.image_label.pack()

        # Wafer, Accuracy, Weight, Weight state를 표시할 라벨 생성
        self.wafer_var = tk.StringVar()
        self.accuracy_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.weight_state_var = tk.StringVar()

        # 각 데이터를 표시할 라벨 및 프레임 생성
        self.create_data_label(data_frame, "Wafer", self.wafer_var, 0, "#000000", "#FFFFFF")
        self.create_data_label(data_frame, "Accuracy", self.accuracy_var, 1, "#FFFFFF", "#000000")
        self.create_data_label(data_frame, "Weight", self.weight_var, 2, "#000000", "#FFFFFF")
        self.create_data_label(data_frame, "Weight state", self.weight_state_var, 3, "#FFFFFF", "#000000")

        # Tkinter의 메인 루프에서 주기적으로 데이터 업데이트 및 UI 업데이트 실행
        self.update_data_and_ui()

    def create_data_label(self, parent, text, variable, row, bg_color, fg_color):
        frame = tk.Frame(parent, bg='#808080', bd=2, relief=tk.RAISED, width=450, height=150)
        frame.grid(row=row, column=0, padx=20, pady=20, sticky='nsew')
        frame.pack_propagate(False)  # 프레임 크기가 내부 위젯 크기에 맞춰지지 않도록 설정
        label = tk.Label(frame, textvariable=variable, font=('Helvetica', 30, 'bold'), bg=bg_color, fg=fg_color)
        label.pack(fill=tk.BOTH, expand=True)

    def update_data_and_ui(self):
        # Firebase에서 데이터를 가져오는 코드
        self.wafer = self.wafer_ref.get()
        self.accuracy = self.accuracy_ref.get()
        self.weight = self.weight_ref.get()
        self.weight_state = self.weight_state_ref.get()

        # UI 업데이트
        self.update_wafer(self.wafer)
        self.update_accuracy(self.accuracy)
        self.update_weight(self.weight)
        self.update_weight_state(self.weight_state)

        # 이미지 업데이트
        self.update_image()

        # 다음 업데이트를 예약
        self.root.after(3000, self.update_data_and_ui)

    def format_label_text(self, text, value, unit=""):
        return f"{text}  : {value} {unit}"

    def update_wafer(self, wafer):
        formatted_text = self.format_label_text("Wafer", wafer)
        self.wafer_var.set(formatted_text)

    def update_accuracy(self, accuracy):
        formatted_text = self.format_label_text("Accuracy", accuracy, "%")
        self.accuracy_var.set(formatted_text)

    def update_weight(self, weight):
        formatted_text = self.format_label_text("Weight", weight, "g")
        self.weight_var.set(formatted_text)

    def update_weight_state(self, weight_state):
        formatted_text = self.format_label_text("Weight state", weight_state)
        self.weight_state_var.set(formatted_text)

    def update_image(self):
        # Firebase에서 이미지 경로를 가져옴
        image_path = self.image_ref.get()

        if image_path:
            try:
                # 이미지 경로를 이용하여 이미지 로드
                image = PhotoImage(file=image_path)

                # 이미지 해상도를 줄이기 위해 subsample 사용
                image = image.subsample(2, 2)  # 가로, 세로로 1/2 크기로 줄임

                # 이미지 표시 라벨 업데이트
                self.image_label.config(image=image)
                self.image_label.image = image  # reference를 유지하기 위해 설정
            except Exception as e:
                # 이미지 로드 중 오류 발생 시 에러 메시지 출력
                print("Error loading image:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageUpdaterApp(root)
    root.mainloop()
