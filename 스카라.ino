#include <HX711.h>
#include <Herkulex.h>
#include <SoftwareSerial.h>

#define MOTOR_1 0 // DRS-0601 15번 핀
#define MOTOR_2 1 // DRS-0601 14번 핀
#define HALL_SENSOR_PIN 2 // 홀 센서 핀
#define DOUT 3 // 로드셀
#define CLK 4 // 로드셀
#define Z_ACTUATOR_IN1 5
#define Z_ACTUATOR_IN2 6
#define GRIPPER_ACTUATOR_IN3 7
#define GRIPPER_ACTUATOR_IN4 8
#define ENABLE_PIN 9 // Z축_ENA
#define PUL 10 // 스텝모터_Pulse
#define DIR 11 // 스텝모터_Direction
#define ENA 12 // 스텝모터_Enable
#define NUM_READINGS 10

#define FLOOR_COUNT 8 // 렉의 층 수
#define MAX_SPEED 255 // Z축_SPEED
#define HOLD 50 // Z축_역전압
#define WEIGHT_THRESHOLD_HIGH 27.0
#define WEIGHT_THRESHOLD_LOW 25.0
#define WEIGHT_HIGH_MID 32.0
#define WEIGHT_LOW_MID 18.0
#define WEIGHT_TRIGGER 10.0 // 10g 이상 측정 시 Load_Cell_Weight() 호출
#define WEIGHT_CHECK_INTERVAL 1000 // 1초마다 무게 체크
#define GRIPPER_DELAY 1000
#define Z_ACTUATOR_DELAY 1500
#define FLOOR_BASE_ANGLE 48
#define FLOOR_ANGLE 10
#define GRIPPER_ANGLE -138

HX711 scale;

int currentFloor = 0;
bool normalRack[FLOOR_COUNT] = {0};
bool defectRack[FLOOR_COUNT] = {0};

float calibration_factor = 7000; // 로드셀 보정값

unsigned long lastWeightCheckTime = 0;
bool weightAboveThreshold = false;

void setup() {
  pinMode(Z_ACTUATOR_IN1, OUTPUT);
  pinMode(Z_ACTUATOR_IN2, OUTPUT);
  pinMode(GRIPPER_ACTUATOR_IN3, OUTPUT);
  pinMode(GRIPPER_ACTUATOR_IN4, OUTPUT);
  pinMode(HALL_SENSOR_PIN, INPUT_PULLUP);
  pinMode(PUL, OUTPUT);
  pinMode(DIR, OUTPUT);
  pinMode(ENA, OUTPUT);
  Serial.begin(115200);
  scale.begin(DOUT, CLK);
  scale.set_scale(calibration_factor);
  scale.tare();
  Herkulex.beginSerial3(115200);
  Herkulex.initialize();
  Herkulex.clearError(MOTOR_1);
  Herkulex.clearError(MOTOR_2);
  Herkulex.torqueON(MOTOR_1);
  Herkulex.torqueON(MOTOR_2);
  delay(1500);
}

void loop() {
  updateCurrentFloor();  // 자석 감지를 통한 층 정보 업데이트
  moveToUnknownWaferRack();  // 미지수 렉으로 이동
  controlGripper(GRIPPER_DELAY, Z_ACTUATOR_DELAY);  // 그리퍼 전진, 후진 및 상승/하강
  
  float weight = checkWeight();  // 무게 체크 및 웨이퍼 상태 판단
  moveToResultRack(weight);  // 정상 또는 불량 렉으로 웨이퍼 배치
  
  while (1) {}
}

// 현재 층을 홀 센서를 통해 업데이트
void updateCurrentFloor() {
  if (digitalRead(HALL_SENSOR_PIN) == LOW) {
    currentFloor++;
    delay(300);
    Serial.print("현재 층: ");
    Serial.println(currentFloor);
  }
}

// 미지수 웨이퍼 렉으로 이동
void moveToUnknownWaferRack() {
  moveMotorsToPosition(7, 5);
}

// 모터 이동 제어
void moveMotorsToPosition(int angle1, int angle2) {
  Herkulex.moveAllAngle(MOTOR_1, angle1, LED_GREEN);
  Herkulex.moveAllAngle(MOTOR_2, angle2, LED_BLUE);
  Herkulex.actionAll(1600);
}

// 그리퍼 전진, 후진, 상승 제어
void controlGripper(unsigned long forwardTime, unsigned long liftTime) {
  // 그리퍼 전진
  controlActuator(GRIPPER_ACTUATOR_IN3, GRIPPER_ACTUATOR_IN4, forwardTime, true);
    
  // Z축 상승
  controlActuator(Z_ACTUATOR_IN1, Z_ACTUATOR_IN2, liftTime, true);
    
  // 무게 체크 후 그리퍼 후진
  controlActuator(GRIPPER_ACTUATOR_IN3, GRIPPER_ACTUATOR_IN4, forwardTime, false);
}

// 액추에이터 제어 (전진/후진, 상승/하강)
void controlActuator(int in1Pin, int in2Pin, unsigned long time, bool forward) {
  digitalWrite(in1Pin, forward ? HIGH : LOW);
  digitalWrite(in2Pin, forward ? LOW : HIGH);
  delay(time);
  digitalWrite(in1Pin, LOW);
  digitalWrite(in2Pin, LOW);
}

// 평균 무게 계산 및 로드셀 측정
float checkWeight() {
  float sum = 0;
  for (int i = 0; i < NUM_READINGS; i++) {
    sum += scale.get_units();
    delay(100);
  }
  float weight = sum / NUM_READINGS;
  Serial.print("측정된 무게: ");
  Serial.println(weight);
  return weight;
}

// 웨이퍼를 정상 또는 불량 렉으로 이동
void moveToResultRack(float weight) {
  if (weight >= WEIGHT_THRESHOLD_HIGH && weight <= WEIGHT_HIGH_MID) {
    moveToEmptyFloorInRack(normalRack);
  } else if (weight >= WEIGHT_LOW_MID && weight <= WEIGHT_THRESHOLD_LOW) {
    moveToEmptyFloorInRack(defectRack);
  }
}

// 비어있는 렉 층으로 이동
void moveToEmptyFloorInRack(bool rack[]) {
  for (int i = 0; i < FLOOR_COUNT; i++) {
    if (!rack[i]) {
      Serial.print("비어 있는 층으로 이동: ");
      Serial.println(i);
      moveMotorsToPosition(FLOOR_BASE_ANGLE + i * FLOOR_ANGLE, GRIPPER_ANGLE);
      rack[i] = true;  // 해당 층에 웨이퍼 배치 완료 표시
      return;
    }
  }
  Serial.println("모든 층이 가득 찼습니다.");
}
