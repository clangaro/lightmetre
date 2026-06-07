void setup() {
  Serial.begin(9600);
}

void loop() {
  int val1 = analogRead(A0);
  int val2 = analogRead(A1);
  int val3 = analogRead(A2);
  int val4 = analogRead(A3);

  Serial.print(val1); Serial.print(",");
  Serial.print(val2); Serial.print(",");
  Serial.print(val3); Serial.print(",");
  Serial.println(val4);

  delay(1000);  // Send every second
}
