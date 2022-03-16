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

//LED stuff
//#define numDoorLed 1
#define numBlockDockLed 1
//#define doorDataPin 32
#define blockDockDataPin 5
//CRGB doorLed[numDoorLed];
CRGB dockLed[numBlockDockLed];

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

Servo door1;
Servo door2;

int pos = 0;
const int servo1Pin = 14;
const int servo2Pin = 12;

int up1 = 40;
int down1 = 150;
int up2 = 160;
int down2 = 40;

const int doorDock1Pin = 27;

const int irPin = 25; // 1100 no robot, < 1400 robot detected
float doorThreshold = 2000;
float irDistance;
const int numIRReadings = 50;
int totalIR = 0;

enum Room {Start, BlockDock, Door, End};
static unsigned int state = Start;

void setup() {
  Serial.begin(115200);
  door1.setPeriodHertz(50);    // standard 50 hz servo
  door2.setPeriodHertz(50);    // standard 50 hz servo
  door1.attach(servo1Pin, 400, 2600); // attaches the servo on pin 18 to the servo object
  door2.attach(servo2Pin, 400, 2600); // attaches the servo on pin 18 to the servo object

  pinMode(doorDock1Pin, INPUT_PULLUP);

  pinMode(irPin, INPUT);

  //FastLED.addLeds<NEOPIXEL, doorDataPin>(doorLed, numDoorLed);
  FastLED.addLeds<NEOPIXEL, blockDockDataPin>(dockLed, numBlockDockLed);
  //doorLed[0] = CRGB::Blue;
  dockLed[0] = CRGB::Blue;//startup color

  u8g2.begin();
  prepare();
}

void prepare(void) {
  u8g2.clearBuffer();          // clear the internal memory
  u8g2.setFont(u8g2_font_helvR10_tr); // choose a suitable font
  u8g2.drawStr(22, 15, "Current State"); // write something to the internal memory

  // draw a frame, only the content within the frame will be updated
  // the frame is never drawn again, but will stay on the display
  u8g2.drawBox(pixel_area_x_pos - 1, pixel_area_y_pos - 1, pixel_area_width + 2, pixel_area_height + 2);

  u8g2.sendBuffer();          // transfer internal memory to the display

  u8g2.setFont(u8g2_font_courB18_tr); // set the target font for the text width calculation
  width = u8g2.getUTF8Width(text);    // calculate the pixel width of the text
  offset = width + pixel_area_width;
}

void display_lcd(char* state) {
  u8g2.clearBuffer();            // clear the complete internal memory
  text = state;
  // draw the scrolling text at current offset
  u8g2.setFont(u8g2_font_courB18_tr);   // set the target font
  u8g2.drawUTF8(
    pixel_area_x_pos - width + offset,
    pixel_area_y_pos + pixel_area_height + u8g2.getDescent() - 1,
    text);                // draw the scolling text

  // now only update the selected area, the rest of the display content is not changed
  u8g2.updateDisplayArea(tile_area_x_pos, tile_area_y_pos, tile_area_width, tile_area_height);

  offset--;               // scroll by one pixel
  if ( offset == 0 )
    offset = width + pixel_area_width;    // start over again

  delay(10);              // do some small delay
}

/* Turns enumerated state into string; to display to esp */
char* get_state(unsigned int state) {
  char* retState[] = {"Start", "Block Dock", "Door", "End"};
  //add more states...
  return retState[state];
}

void doorControl(bool openDoor) { //true input opens door, false closes
  if (openDoor) {
    door1.write(up1);
    door2.write(up2);
  } else {
    door1.write(down1);
    door2.write(down2);
  }
}

bool checkBlockDock1() { //return true when a block is detected
  if (digitalRead(doorDock1Pin) == LOW) {
    return true;
  } else {
    return false;
  }
}

bool checkIRDoor() {   //return true when a robot is detected in front of door

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

void handleBlockDock1() {
  if (state == BlockDock) state = Door;
  dockLed[0] = CRGB::Green; //update led color
}

void handleIRDoor() {
  if (state == Door) state = End;
}

void loop() {
  FastLED.show(); //display current LED state
  char* state_msg = get_state(state);
  display_lcd(state_msg);
  if (checkBlockDock1())  handleBlockDock1();
  if (checkIRDoor())      handleIRDoor();

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
      doorControl(true); //open door
      break;
  }



}
