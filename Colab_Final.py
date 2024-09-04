import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.applications import MobileNet, Xception, ResNet50, InceptionV3
from tensorflow.keras.layers import Flatten, Conv2D, MaxPooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Firebase Admin SDK 초기화
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate('path/to/your-firebase-adminsdk.json')  # 인증 정보 파일 경로
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-database-url.firebaseio.com/'  # 데이터베이스 URL
})

# Google Drive 마운트
from google.colab import drive
drive.mount('/content/gdrive/')

root_dir = '/content'

# wafer_image 디렉토리가 존재하면 삭제
import os
import shutil
if os.path.exists(os.path.join(root_dir, 'wafer_image')):
    shutil.rmtree(os.path.join(root_dir, 'wafer_image'))

# wafer_image.zip 압축 해제
import zipfile
with zipfile.ZipFile(os.path.join(root_dir, 'wafer_image.zip'), 'r') as target_file:
    target_file.extractall(os.path.join(root_dir, 'wafer_image'))

# test 디렉토리 생성 (존재하지 않는 경우)
if not os.path.exists(os.path.join(root_dir, 'wafer_image/test')):
    os.mkdir(os.path.join(root_dir, 'wafer_image/test'))

if not os.path.exists(os.path.join(root_dir, 'wafer_image/test_image_files')):
    os.mkdir(os.path.join(root_dir, 'wafer_image/test_image_files'))

# 전체 라벨 수 확인
label_name_list = os.listdir(os.path.join(root_dir, 'wafer_image/train/'))
print('total label nums = ', len(label_name_list))
print('=================================================')
print(label_name_list)

# 데이터를 train과 test 세트로 분할
ratio = 0.1  # train : test = 90 : 10

src_root_dir = os.path.join(root_dir, 'wafer_image/train/')
dst_root_dir = os.path.join(root_dir, 'wafer_image/test/')

label_name_list = os.listdir(src_root_dir)

# test 디렉토리에 라벨 디렉토리 생성
for label_name in label_name_list:
    dst_label_name_dir = dst_root_dir + label_name
    if not os.path.exists(dst_label_name_dir):
        os.mkdir(dst_label_name_dir)

# 일부 이미지를 train 디렉토리에서 test 디렉토리로 이동
for label_name in label_name_list:
    train_image_file_list = glob.glob(src_root_dir + label_name + '/*')
    split_num = int(ratio * len(train_image_file_list))
    test_image_file_list = train_image_file_list[0:split_num]
    for image_file in test_image_file_list:
        shutil.move(image_file, dst_root_dir + label_name)

# train과 test 데이터 분할 확인
train_label_name_list = os.listdir(src_root_dir)
test_label_name_list = os.listdir(src_root_dir)

train_label_name_list.sort()
test_label_name_list.sort()

if train_label_name_list != test_label_name_list:
    print('fatal error !!!!')
else:
    print(len(train_label_name_list), len(test_label_name_list))

# 각 라벨별 train과 test 세트의 이미지 수 출력
for label_name in train_label_name_list:
    train_data_nums = len(os.listdir(src_root_dir + label_name))
    test_data_nums = len(os.listdir(dst_root_dir + label_name))
    print('train => ', label_name, train_data_nums, ' , test => ', label_name, test_data_nums)
    print('=======================================================')

# test 이미지를 별도의 디렉토리로 복사
for label_name in label_name_list:
    image_file_list = glob.glob(src_root_dir + label_name + '/*')
    print('total [%s] image file nums => [%s]' % (label_name, len(image_file_list)))
    copy_nums = 0
    for image_file in image_file_list:
        shutil.copy(image_file, dst_root_dir)  # 복사
        copy_nums = copy_nums + 1
    print('total copy nums => ', copy_nums)

# 이미지 크기 설정
IMG_WIDTH = 224
IMG_HEIGHT = 224

# 디렉토리 경로 정의
train_dir = os.path.join(root_dir, 'wafer_image/train/')
validation_dir = os.path.join(root_dir, 'wafer_image/train/')
test_dir = os.path.join(root_dir, 'wafer_image/test/')

# 훈련을 위한 데이터 증강 및 정규화
train_datagen = ImageDataGenerator(rescale=1./255, rotation_range=20, width_shift_range=0.2,
                                   height_shift_range=0.2, shear_range=0.2, zoom_range=0.2,
                                   validation_split=0.15)

# 검증을 위한 데이터 정규화
validation_datagen = ImageDataGenerator(rescale=1./255, validation_split=0.15)

# 훈련 데이터 생성기
train_generator = train_datagen.flow_from_directory(train_dir, batch_size=16, color_mode='rgb',
                                                    class_mode='sparse', subset='training',
                                                    target_size=(IMG_WIDTH, IMG_HEIGHT))

# 검증 데이터 생성기
validation_generator = validation_datagen.flow_from_directory(validation_dir, batch_size=16, color_mode='rgb',
                                                              class_mode='sparse', subset='validation',
                                                              target_size=(IMG_WIDTH, IMG_HEIGHT))

# 클래스 인덱스 출력
print(train_generator.class_indices)

# 사전 학습된 MobileNet 모델 로드 (탑 레이어 제외)
base_model = MobileNet(weights='imagenet', include_top=False, input_shape=(IMG_WIDTH, IMG_HEIGHT, 3))

# 새로운 모델 생성
model = Sequential()

# 베이스 모델 추가
model.add(base_model)

# 평탄화 레이어 추가
model.add(Flatten())

# 완전 연결 층 추가
model.add(Dense(32, activation='relu'))
model.add(Dropout(0.25))
model.add(Dense(2, activation='softmax'))

# 모델 컴파일
model.compile(loss='sparse_categorical_crossentropy',
              optimizer=tf.keras.optimizers.Adam(2e-5), metrics=['accuracy'])

# 모델 요약 출력
model.summary()

# 조기 종료 콜백
from tensorflow.keras.callbacks import EarlyStopping
earlystopping = EarlyStopping(monitor='val_loss', patience=5)

# 모델 훈련
hist = model.fit(train_generator, validation_data=validation_generator,
                 epochs=15, callbacks=[earlystopping])

# 훈련 데이터에 대한 모델 평가
loss, acc = model.evaluate(train_generator)
print("Restored model, accuracy: {:5.2f}%".format(100 * acc))

# 정확도 추세 플롯
import matplotlib.pyplot as plt
plt.plot(hist.history['accuracy'], label='train')
plt.plot(hist.history['val_accuracy'], label='validation')
plt.title('Accuracy Trend')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(loc='best')
plt.grid()
plt.show()

# 손실 추세 플롯
plt.plot(hist.history['loss'], label='train')
plt.plot(hist.history['val_loss'], label='validation')
plt.title('Loss Trend')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(loc='best')
plt.grid()
plt.show()

# 테스트 데이터 생성기
test_datagen = ImageDataGenerator(rescale=1./255)

# 테스트 데이터 생성기
test_generator = test_datagen.flow_from_directory(test_dir, batch_size=32, color_mode='rgb',
                                                  class_mode='sparse', target_size=(IMG_WIDTH, IMG_HEIGHT))

# 테스트 데이터에 대한 모델 평가
model.evaluate(test_generator)

# 단일 이미지 예측
import os
import numpy as np
import cv2

# 테스트 이미지 파일 경로 정의
test_image_file = 'gdrive/My Drive/depth_color.png'
IMG_WIDTH = 224
IMG_HEIGHT = 224

# 테스트 이미지 로드 및 전처리
src_img = cv2.imread(test_image_file, cv2.IMREAD_COLOR)
src_img = cv2.resize(src_img, dsize=(IMG_WIDTH, IMG_HEIGHT))
src_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2RGB)
src_img = src_img / 255.0

# 이미지를 4차원 텐서로 변환
src_img_array = np.array([src_img])
print(src_img_array.shape)

# 이미지 클래스 예측
pred = model.predict(src_img_array)
print(pred.shape)

# 예측 결과 시각화
import matplotlib.pyplot as plt
class_names = ['broken', 'normal']
plt.figure(figsize=(12, 12))

for pos in range(len(pred)):
    plt.subplot(3, 3, pos + 1)
    plt.axis('off')
    pred_str = class_names[np.argmax(pred[pos])]
    probility = '{0:0.4f}'.format(100 * max(pred[pos]))
    plt.title('pred:' + pred_str + ',' + probility + '%')
    print('pred:' + pred_str + ',' + probility + '%')
    plt.imshow(src_img_array[pos])

plt.tight_layout()
plt.show()

# Firebase 실시간 데이터베이스에 참조 생성 및 업데이트
ref = db.reference()
ref.update({'wafer': pred_str})  # 예측 결과를 'wafer' 키로 업데이트

ref = db.reference()
ref.update({'accuracy': probility})  # 예측 정확도를 'accuracy' 키로 업데이트

# Firebase 실시간 데이터베이스에서 데이터 가져오기
ref = db.reference()
ref = print(ref.get())  # 전체 데이터 출력
