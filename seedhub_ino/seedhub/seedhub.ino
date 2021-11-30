#include "DHT.h"
#include <SoftwareSerial.h>
//============
//save the initial time at startup
unsigned long fans_time = millis(); // used for fan toggling 
unsigned long soil_time = millis(); // used for checkup time
unsigned long leds_time = millis(); // used for leds toggling
unsigned long info_time = millis(); // used for info reporting
unsigned long fan_cycle = millis(); // used for keep track of time
unsigned long pump_time = millis(); // used for water pump toggling
unsigned long fade_time = millis(); // used for fading leds when on
static const unsigned long ONE_HOUR = 3600000; // represents one hour
unsigned long checkup_time = 300000; // soil check time, default is 5 mins
unsigned long fan_minutes = 1800000;  // fan turn on cycle, default is 30 minutes
//============
#define DHTType     DHT11     // Type of DHT sensor
#define DHTPin      9         // pin connected to DHT sensor
#define soilSensor  A0        // pin connected to soil sensor
#define gasSensor   A1        // pin connected to gas sensor
#define relayPin    8         // pin connected to pum relay
#define ledStrip    6         // pin connected to led strip
#define fanPin      5         // pin connected to fan mosfet
#define BT_RX       2         // pin connected to BT receive
#define BT_TX       3         // pin connected to BT transmit
//============
const byte cmd_size = 32;     // size of serial message
char serial_in[cmd_size];     // array for serial message
char serial_tmp[cmd_size];    // temporary array for use when parsing
char command[cmd_size] = {0}; // command from pc
int cmd_value = 0;            // value for command
boolean new_data = false;     // indicates command received
//============
int soil_moisture = 0;        // soil moisture read from sensor
const int dry     = 810;      // soil moisture sensor dry measure
const int wet     = 420;      // soil moisture sensor wet measure
int   air_quality     = 0;    // air quiality from sensor
float air_humidity    = 0;    // air humidity from sensor
float air_temperature = 0;    // air temperature from sensor
int led_bright  = 127;        // brightness of led strip, default is 127 ( 50% ) 
float gamma = 0.20;           // affects the width of peak (more or less darkness)
float beta = 0.5;             // shifts the gaussian to be symmetric
float smoothness_pts = 768;   // larger=slower change in brightness 
int led_hours = 12;           // led strip cycle, default is 12 hours
bool led_on   = false;        // indicates whether the leds are on
bool pump_on = false;         // indicates whether the pump is on
bool fans_on = false;         // indicated whether the fans are on
bool dimm_on = false;         // indicates whether leds dimm
bool logs_on = false;         // indicates whether autolog is on
bool programming_bt = false;  // indicates whether BT is in AT mode
static int hours_passed = 0;
//============
int pref_soil_moisture = 40;    // user defined soil moisture (default is 40)
int pref_pump_runtime = 1000;   // user defined pump time (seconds, def is 1)
int pref_fans_runtime = 30000;  // user defined fans time (seconds, def is 30)
//============
DHT dht(DHTPin, DHTType);             // initializing the DHT sensior
SoftwareSerial BTSerial(BT_RX,BT_TX); // initializing the BT module
//============
void setup(){
  Serial.begin(9600);
  BTSerial.begin(9600);
  Serial.setTimeout(2);
  pinMode(relayPin, OUTPUT);
  pinMode(soilSensor, INPUT);
  pinMode(ledStrip, OUTPUT);
  pinMode(fanPin, OUTPUT);
  digitalWrite(relayPin, HIGH);
  dht.begin();
  delay(500);
  //toggleLed(); //set led as on when circuit starts
}

//============
void loop(){
  do_loop();
}
//============
void do_loop(){
  unsigned long loop_time = millis();
  readCommand();
  readBTCommand();
  if (new_data == true) {
    strcpy(serial_tmp, serial_in);
    // this temporary copy is necessary to protect the original data
    // because strtok() used in parseData() replaces the commas with \0
    parseData();
    new_data = false;
    if(strcmp(command, "toggle_pump") == 0 ){
      togglePump();
      pump_time = loop_time;
    }
    else if(strcmp(command, "set_check") == 0 ){
      setCheckupTime(cmd_value);
    }
    else if(strcmp(command, "set_pump") == 0 ){
      setPumpTime(cmd_value);
    }
    else if(strcmp(command, "set_soil") == 0 ){
      setSoilMoisture(cmd_value);
    }
    else if(strcmp(command, "set_ledb") == 0 ){
      setLedBrightness();
    }
    else if(strcmp(command, "set_ledh") == 0 ){
      setLedHours(cmd_value);
    }
    else if(strcmp(command, "set_fans") == 0 ){
      setFansRuntime(cmd_value);
    }
    else if(strcmp(command, "get_conf") == 0 ){
      printSettings();
    }
    else if (strcmp(command, "read_info") == 0 ) {
      printInfo();
    }
    else if(strcmp(command, "toggle_leds") == 0 ){
      toggleLeds();
    }
    else if(strcmp(command, "toggle_fans") == 0 ){
      toggleFans();
      fans_time = loop_time;
    }
    else if(strcmp(command, "toggle_dimm") == 0 ){
      toggleDimm();
    }
    else if(strcmp(command, "toggle_logs") == 0 ){
      toggleLogs();
    }
  }
  // each five minute check the soil_moisture
  if(info_time - soil_time > checkup_time){
    // if the soil moisture is below desired level, turn pump;
    if(soil_moisture < pref_soil_moisture){
      togglePump();
      pump_time = loop_time;
    }
    soil_time = loop_time;
  }
  // handle brightness change
  if(loop_time - fade_time > 5 && dimm_on){
    handleBrightnessChange(loop_time);
  }
  // toggle leds each led_hours
  if(loop_time - leds_time > ONE_HOUR){
    hours_passed++;
    if(hours_passed == led_hours){
      hours_passed = 0;
      toggleLeds();
    }
    leds_time = loop_time;
  }
  // turn on the fans each fan_minutes
  if(loop_time - fan_cycle > fan_minutes){
    toggleFans();
    fan_cycle = loop_time;
  }
  // handle pump status
  handlePumpStatus(loop_time);
  handleFanStatus(loop_time);
}
//============
void toggleLogs(){
  if (logs_on){
    logs_on = false;
    return;
  }
  logs_on = true;
  printLog("Toggling logs");
}
//============
void setFansRuntime(int seconds){
  pref_fans_runtime = seconds * 1000;
  printLog("Set fan runtime OK");
}
//============
void setLedHours(int hours){
  led_hours = hours * 1000 * 60 * 60;
  printLog("Set led hours OK");
}
//============
void setCheckupTime(int minutes){
  checkup_time = minutes * 1000 * 60;
  printLog("Set checkup time OK");
}
//============
void toggleDimm(){
  printLog("Toggling dimming");
  if(dimm_on){
    dimm_on = false;
    return;
  }
  dimm_on = true;
}
//============
void handleFanStatus(unsigned long loop_time){
  if(fans_on){
    digitalWrite(fanPin, HIGH);
    if(loop_time - fans_time > pref_fans_runtime){
      toggleFans();
    }
  } else {
    digitalWrite(fanPin, LOW);
  }
}
//============
void handlePumpStatus(unsigned long loop_time){
  if(pump_on){
    digitalWrite(relayPin, LOW);
    if(loop_time - pump_time > pref_pump_runtime){
      togglePump();
    }
  } else {
    digitalWrite(relayPin, HIGH);
  }
}
//============
void handleBrightnessChange(unsigned long t){
  if(led_on){
    float pwm_val = 255.0*(exp(-(pow(((led_bright++/smoothness_pts)-beta)/gamma,2.0))/2.0));
    analogWrite(ledStrip, int(pwm_val));
    fade_time = t;
    if(smoothness_pts < led_bright){
      led_bright = 3;
    }
  }
}
//============
void toggleFans(){
 printLog("Toggling fans");
 if (fans_on){
    fans_on = false;
    return;
  }
  fans_on = true;
}
//============
void setLedBrightness(){
  led_bright = cmd_value;
  analogWrite(ledStrip, led_bright);
  dimm_on = false;
  if(led_bright > 0)
    led_on = true;
  else led_on = false;
  printLog("set_ledb OK!");
}
//============
void toggleLeds(){
  printLog("Toggling leds");
  if(led_on){
    analogWrite(ledStrip, 0);
    led_on = false;
  }else{
    analogWrite(ledStrip, led_bright);
    led_on = true;
  }
}
//============
void setSoilMoisture(int percentage){
  pref_soil_moisture = percentage;
  printLog("set_soil OK!");
}
//============
void setPumpTime(int seconds) {
  pref_pump_runtime = seconds*1000;
  printLog("set_pump OK!");
}
//============
void togglePump(){
 printLog("Toggled pump");
 if (pump_on){
    pump_on = false;
    return;
  }
  pump_on = true;
}
//============
void printInfo() {
  air_quality     = analogRead(gasSensor);
  soil_moisture   = analogRead(soilSensor);
  soil_moisture   = map(soil_moisture,dry,wet,0,100);
  air_temperature = dht.readTemperature();
  air_humidity    = dht.readHumidity();
  BTSerial.print("Soil moisture:");
  BTSerial.print(soil_moisture);
  BTSerial.print("%\tAir temperature:");
  BTSerial.print(air_temperature);
  BTSerial.print("C\tAir humidity:");
  BTSerial.print(air_humidity);
  BTSerial.print("%\tAir quality:");
  BTSerial.print(air_quality);
  BTSerial.println("ppm");
  Serial.print("Soil moisture:");
  Serial.print(soil_moisture);
  Serial.print("%\tAir temperature:");
  Serial.print(air_temperature);
  Serial.print("C\tAir humidity:");
  Serial.print(air_humidity);
  Serial.print("%\tAir quality:");
  Serial.print(air_quality);
  Serial.println("ppm");
}
//============
void readCommand() {
  static boolean reading_cmd = false;
  static byte idx = 0;
  char begin_char = '<';
  char close_char = '>';
  char read_char;
  while (Serial.available() > 0 && new_data == false) {
    read_char = Serial.read(); 
    if (reading_cmd == true) {
      if (read_char != close_char) {
        serial_in[idx] = read_char;
        idx++;
        if (idx >= cmd_size) {
          idx = cmd_size - 1;
        }
      }
      else {
        serial_in[idx] = '\0'; // terminate the string
        reading_cmd = false;
        idx = 0;
        new_data = true;
      }
    }
    else if (read_char == begin_char) {
      reading_cmd = true;
    }
  }
}
//============
void readBTCommand() {
  static boolean reading_cmd = false;
  static byte idx = 0;
  char begin_char = '<';
  char close_char = '>';
  char read_char;

  while (BTSerial.available() > 0 && new_data == false) {
    read_char = BTSerial.read(); 
    if (reading_cmd == true) {
      if (read_char != close_char) {
        serial_in[idx] = read_char;
        idx++;
        if (idx >= cmd_size) {
          idx = cmd_size - 1;
        }
      }
      else {
        serial_in[idx] = '\0'; // terminate the string
        reading_cmd = false;
        idx = 0;
        new_data = true;
      }
    }
    else if (read_char == begin_char) {
      reading_cmd = true;
    }
  }
}
//============
void parseData() {
  char * str_idx;                   // this is used by strtok() as an index
  str_idx = strtok(serial_tmp,","); // get the first part - the string
  strcpy(command, str_idx);         // copy it to command
  str_idx = strtok(NULL, ",");      // this continues where the previous call left off
  cmd_value = atoi(str_idx);        // convert this part to an integer
}
//============
void printData() {
  Serial.print("Command: ");
  Serial.print(command);
  Serial.print("\tValue: ");
  Serial.print(cmd_value);
}
//============
void printBTData() {
  BTSerial.print("Command: ");
  BTSerial.print(command);
  BTSerial.print("\tValue: ");
  BTSerial.print(cmd_value);
}
//============
void printSettings(){
  Serial.print("Pref checkup time:");
  Serial.print(checkup_time/60000);
  Serial.print("m\tPref soil moisture:");
  Serial.print(pref_soil_moisture);
  Serial.print("%\tPref pump runtime:");
  Serial.print(pref_pump_runtime/1000);
  Serial.print("s\tPref fans runtime:");
  Serial.print(pref_fans_runtime/1000);
  Serial.print("m\tPref fans cycle:");
  Serial.print(fan_minutes/60000);
  Serial.print("m\tPref led brightness:");
  Serial.print(led_bright);
  Serial.print("%\tPref led hours:");
  Serial.print(led_hours);
  Serial.print("h\tPref led animation:");
  Serial.print(dimm_on ? "Yes" : "No");
  Serial.print("\tAuto loggin on:");
  Serial.println(logs_on ? "Yes" : "No");
  BTSerial.print("Pref checkup time:");
  BTSerial.print(checkup_time/60000);
  BTSerial.print("m\tPref soil moisture:");
  BTSerial.print(pref_soil_moisture);
  BTSerial.print("%\tPref pump runtime:");
  BTSerial.print(pref_pump_runtime/1000);
  BTSerial.print("s\tPref fans runtime:");
  BTSerial.print(pref_fans_runtime/1000);
  BTSerial.print("s\tPref fans cycle:");
  BTSerial.print(fan_minutes/60000);
  BTSerial.print("m\tPref led brightness:");
  BTSerial.print(led_bright);
  BTSerial.print("%\tPref led hours:");
  BTSerial.print(led_hours);
  BTSerial.print("h\tPref led animation:");
  BTSerial.print(dimm_on ? "Yes" : "No");
  BTSerial.print("\tAutologgin on:");
  BTSerial.println(logs_on ? "Yes" : "No");
}
//============
void printLog(String txt){
  if(logs_on){
    Serial.println(txt);
    BTSerial.println(txt);
  }
}
