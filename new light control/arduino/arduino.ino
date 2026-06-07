const int sensor1 = A3;  
const int sensor2 = A1;
const int sensor3 = A4;
const int sensor4 = A2;

const unsigned long interval = 600000; // 10 minutes in milliseconds
unsigned long previousMillis = 0;

void setup() {
  Serial.begin(9600);  
  pinMode(sensor1, INPUT);
  pinMode(sensor2, INPUT);
  pinMode(sensor3, INPUT);
  pinMode(sensor4, INPUT);
  Serial.println("Hello from Arduino!");
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;

    int val1 = analogRead(sensor1);
    int val2 = analogRead(sensor2);
    int val3 = analogRead(sensor3);
    int val4 = analogRead(sensor4);

    Serial.print(val1); Serial.print(",");
    Serial.print(val2); Serial.print(",");
    Serial.print(val3); Serial.print(",");
    Serial.println(val4);  
  }
}
