#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <Arduino.h>
#include <U8g2lib.h>
#include <FastLED.h>

#ifdef U8X8_HAVE_HW_SPI
#include <SPI.h>
#endif
#ifdef U8X8_HAVE_HW_I2C
#include <Wire.h>
#endif

/* LED stuff */
//#define numDoorLed 1
#define numBlockDockLed 1
//#define doorDataPin 32
#define blockDockDataPin 5
//CRGB doorLed[numDoorLed];
CRGB dockLed[numBlockDockLed];

/* MQTT Stuff */
const char *ssid = "WPI-Open";
const char *password = NULL;
const char *ID = "esp_boi";  // Name of our device, must be unique
IPAddress broker(130, 215, 172, 60); // IP address of your MQTT broker eg. 192.168.1.50
WiFiClient wclient;
PubSubClient client(wclient); // Setup MQTT client

/* Publishers -> "esp32/..."  */
const char *room_state = "esp32/state";  
/* Subscribers -> "rpi/..."  */
const char *receive_code = "rpi/passcode";

/* LCD Stuff */
U8G2_SSD1306_128X64_NONAME_F_SW_I2C u8g2(U8G2_R0, /* clock=*/ 15, /* data=*/ 4, /* reset=*/ 16);
int16_t offset;        // current offset for the scrolling text
u8g2_uint_t width;      // pixel width of the scrolling text (must be lesser than 128 unless U8G2_16BIT is defined
const char *text = "Testing"; // scroll this text from right to left

const uint8_t tile_area_x_pos = 2;  // Update area left position (in tiles)
const uint8_t tile_area_y_pos = 3;  // Update area upper position (distance from top in tiles)
const uint8_t tile_area_width = 12;
const uint8_t tile_area_height = 3; // this will allow cour18 chars to fit into the area

const u8g2_uint_t pixel_area_x_pos = tile_area_x_pos * 8;
const u8g2_uint_t pixel_area_y_pos = tile_area_y_pos * 8;
const u8g2_uint_t pixel_area_width = tile_area_width * 8;
const u8g2_uint_t pixel_area_height = tile_area_height * 8;
/* End LCD Stuff */

/* Establish Servos */
Servo door1;
Servo door2;

/* Servo Variables */
int pos = 0;
const int servo1Pin = 14;
const int servo2Pin = 12;

int up1 = 40;
int down1 = 150;
int up2 = 160;
int down2 = 40;

/* Block Dock Variables */
const int doorDock1Pin = 27;

/* IR Variables */
const int irPin = 33; // 1100 no robot, < 1400 robot detected
float doorThreshold = 2000;
float irDistance;
const int numIRReadings = 50;
int totalIR;

/* Room States */
enum ROOM {Start, BlockDock, Door, DoorCode, End};  //ADD NEW STATES TO get_state() METHOD
static unsigned int state = Start;
static unsigned int nextState;
bool passcodeAccepted = false;

/* Turns enumerated state into string; to display to esp */
char* get_state(unsigned int state){
  char* retState[] = {"Start", "Block Dock", "Door", "DoorCode", "End"}; //add more states (in order of enumeration)...
  return retState[state];
}

void setup() {
  Serial.begin(115200);
//  while(!Serial) {} //comment out unless testing!
  /* setup MQTT protocols */
  WiFi.begin(ssid, NULL); // Connect to network
  while (WiFi.status() != WL_CONNECTED) { // Wait for connection
    delay(500);
  }
  Serial.println("WiFi connected");
  client.setServer(broker, 1883);
  client.setCallback(callback); 

  /* Servo setup  */
  door1.setPeriodHertz(50);    // standard 50 hz servo
  door2.setPeriodHertz(50);    // standard 50 hz servo
  door1.attach(servo1Pin, 400, 2600); // attaches the servo on pin 18 to the servo object
  door2.attach(servo2Pin, 400, 2600); // attaches the servo on pin 18 to the servo object

  /* Room Puzzle Stuff Setup */
  pinMode(doorDock1Pin, INPUT_PULLUP);

  pinMode(irPin, INPUT);

  /* Room LED Setup */
  //FastLED.addLeds<NEOPIXEL, doorDataPin>(doorLed, numDoorLed);
  FastLED.addLeds<NEOPIXEL, blockDockDataPin>(dockLed, numBlockDockLed);
  //doorLed[0] = CRGB::Blue;
  dockLed[0] = CRGB::Blue;//startup color

  /* Starts ESP LCD */
  u8g2.begin();
  prepare();
}

/* Sets up LCD */
void prepare(void){
  u8g2.clearBuffer();          // clear the internal memory
  u8g2.setFont(u8g2_font_helvR10_tr); // choose a suitable font
  u8g2.drawStr(22,15,"Current State");  // write something to the internal memory
  u8g2.drawBox(pixel_area_x_pos-1, pixel_area_y_pos-1, pixel_area_width+2, pixel_area_height+2);
  u8g2.sendBuffer();          // transfer internal memory to the display
  u8g2.setFont(u8g2_font_courB18_tr); // set the target font for the text width calculation
  width = u8g2.getUTF8Width(text);    // calculate the pixel width of the text
  offset = width+pixel_area_width;
}

/* Refreshes LCD screen to current state */
void display_lcd(char* state){
  u8g2.clearBuffer();            // clear the complete internal memory
  text = state;
  u8g2.setFont(u8g2_font_courB18_tr);   // set the target font
  u8g2.drawUTF8(pixel_area_x_pos-width+offset, 
    pixel_area_y_pos+pixel_area_height+u8g2.getDescent()-1, 
    text);                // draw the scolling text
  
  // now only update the selected area, the rest of the display content is not changed
  u8g2.updateDisplayArea(tile_area_x_pos, tile_area_y_pos, tile_area_width, tile_area_height);
      
  offset--;               // scroll by one pixel
  if ( offset == 0 )  
    offset = width+pixel_area_width;      // start over again
    
  delay(10);              // do some small delay
}

/* True input opens door, false closes */
void doorControl(bool openDoor) {
  if (openDoor) {
    door1.write(up1);
    door2.write(up2);
  } else {
    door1.write(down1);
    door2.write(down2);
  }
}

/* Return true when a block is detected */
bool checkBlockDock1() {
  if (digitalRead(doorDock1Pin) == LOW) {return true;} 
  else {return false;}
}

/* Return true when a robot is detected in front of door */
bool checkIRDoor() {
  totalIR = 0; //reset total
  for (int i = 0; i < numIRReadings; i++) {
    totalIR = totalIR + analogRead(irPin);
  }
  irDistance = totalIR / numIRReadings;  //find average sensor reading
  //Serial.println(irDistance);
  if (irDistance > doorThreshold) {
    return true;
  } else {
    return false;
  }
}

bool checkCorrectPasscode(){
  return passcodeAccepted;
}

/* Handlers */
void handleBlockDock1() {
  if (state == BlockDock) state = Door;
  dockLed[0] = CRGB::Green; //update led color
}
void handleIRDoor() {
  if (state == Door) state = DoorCode;
}

void handleCorrectPasscode(){
  if(state == DoorCode) state = End;
}

void loop() {
  FastLED.show(); //display current LED state
  check_connection();
  char* state_msg = get_state(state);
  pub(room_state, state_msg);
//  Serial.print("\nState: ");
//  Serial.print(state);
//  Serial.print(" -> ");
//  Serial.println(state_msg);
  
  display_lcd(state_msg);
  
  if (checkBlockDock1())      handleBlockDock1();
  if (checkIRDoor())          handleIRDoor();
  if (checkCorrectPasscode()) handleCorrectPasscode();

  switch (state) {

    case Start:
      doorControl(false);     //close door
      delay(1000);
      state = BlockDock;
      break;

    case BlockDock:
      dockLed[0] = CRGB::Red; //set color to red
      break;

    case Door:

      break;

    case End:
      passcodeAccepted = false; //reset boolean
      doorControl(true); //open door
      break;
  }
}

/************************ MQTT Methods ************************/
void pub(const char* topic, char* msg){
  client.publish(topic, msg);
}
void sub(const char* topic){
  client.subscribe(topic);
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect(ID)) {
      //Write ALL Subscribers
      sub(receive_code);
    } else {
      Serial.println(" try again in 2 seconds");
      // Wait 5 seconds before retrying
      delay(2000);
    }
  }
}

void check_connection(){
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

/* Handles ALL Subscribers */
void callback(char* topic, byte* message, unsigned int length) {
  String messageTemp;
  
  for (int i = 0; i < length; i++) {
    messageTemp += (char)message[i];
  }
  
  if (String(topic) == receive_code) {
    if(messageTemp == "accepted"){
      passcodeAccepted = true;
    }
    else if(messageTemp == "denied"){
      passcodeAccepted = false;
    }
  }
}
/*************************************************************/
