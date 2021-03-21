/**
  NASMon
  Name: NASMon Arduino code
  Purpose: Display system stats dynamically on an OLED and LED bargraph.

  @author Alex Peissel
  @version 0.3 13/01/21
*/

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <USBComposite.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "Adafruit_LEDBackpack.h"
#include <JC_Button.h>

// ####################################
// Pin configuration
// ####################################
#define LED_PIN PB12
#define TRIGGER_PIN PB5

// ####################################
// OLED configuration
// ####################################
#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 32 // OLED display height, in pixels
#define DISPLAY_I2C_ADDRESS 0x3C
#define OLED_RESET 4 // Reset pin # (or -1 if sharing Arduino reset pin)
#define MAX_DISPLAY_ON_TIME 5000

// ####################################
// Bargraph configuration
// ####################################
#define BARGRAPH_I2C_ADDRESS 0x70
#define DEFAULT_BARGRAPH_BRIGHTNESS 10 //0 min - 15 max

// ####################################
// Trigger configuration
// ####################################
#define TRIGGER_DEBOUNCE_TIME 100

// ####################################
// Globals
// ####################################
// Debounce
Button trigger(TRIGGER_PIN, TRIGGER_DEBOUNCE_TIME);

// OLED
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
static uint8_t displayBuffer[(SCREEN_WIDTH * SCREEN_HEIGHT + 7) / 8];
unsigned int maxDisplayOnTime = MAX_DISPLAY_ON_TIME;
unsigned long displayOnTime = 0;

// Bargraph
Adafruit_24bargraph bargraph = Adafruit_24bargraph();
byte bargraph_brightness = DEFAULT_BARGRAPH_BRIGHTNESS;

// USBHID
USBHID HID;
USBCompositeSerial CompositeSerial;

// Buffer
boolean newDataInBuffer = false;

// Next page load
int progress = 0;

// Debug
boolean showDebugScreen = false;

// ####################################
// Structs
// ####################################
struct BargraphData
{
  char command;      // 1 byte
  char bargraph[24]; // 24 bytes
} __attribute__((packed));

struct BMPData
{
  char command;     // 1 byte
  byte x;           // 1 byte
  byte y;           // 1 byte
  byte w;           // 1 byte
  byte h;           // 1 byte
  uint8_t bmp[512]; // 512 bytes
} __attribute__((packed));

struct SettingsData
{
  char command;            // 1 byte
  byte maxDisplayOnTime;   // 1 byte
  byte bargraphBrightness; // 1 byte
} __attribute__((packed));

struct TextData
{
  char command;   // 1 byte
  byte x;         // 1 byte
  byte y;         // 1 byte
  byte size;      // 1 byte
  char text[128]; // 128 bytes
} __attribute__((packed));

// ####################################
// DataConverter union
// ####################################
union DataConverter
{
  BMPData bmpdata;
  BargraphData bargraphdata;
  SettingsData settingsdata;
  TextData textdata;
  char command;
  uint8_t buffer[517];
};

static DataConverter pageDataConverter;

// ####################################
// Functions
// ####################################
void clearBuffer()
{
  memset(pageDataConverter.buffer, 0, sizeof(pageDataConverter.buffer));
}

void displayOLED()
{
  displayOnTime = millis();
  display.display();
}

void initGraph()
{
  bargraph.setBrightness(bargraph_brightness);
  for (byte b = 23; b < 0; b--)
  {
    if ((b % 3) == 0)
      bargraph.setBar(b, LED_RED);
    if ((b % 3) == 1)
      bargraph.setBar(b, LED_YELLOW);
    if ((b % 3) == 2)
      bargraph.setBar(b, LED_GREEN);
  }
  bargraph.writeDisplay();
}

void drawGraph()
{
  for (byte i = 0; i <= 23; i++)
  {
    switch (pageDataConverter.bargraphdata.bargraph[i])
    {
    case 'r':
      bargraph.setBar(i, LED_RED);
      break;
    case 'y':
      bargraph.setBar(i, LED_YELLOW);
      break;
    case 'g':
      bargraph.setBar(i, LED_GREEN);
      break;
    case 'o':
      bargraph.setBar(i, LED_OFF);
      break;
    default:
      bargraph.setBar(i, LED_OFF);
      break;
    }
    bargraph.writeDisplay();
  }
}

void fadeOutGraph()
{
  for (byte i = bargraph_brightness; i > 0; i--)
  {
    bargraph.setBrightness(i);
    bargraph.writeDisplay();
    delay(50);
  }
  bargraph.clear();
}

void debugText(String text)
{
  display.clearDisplay();
  display.setTextSize(1);              // Normal 1:1 pixel scale
  display.setTextColor(SSD1306_WHITE); // Draw white text
  display.setCursor(0, 0);             // Start at top-left corner
  display.println(text);
  displayOLED();
  delay(2000);
}

// https://github.com/lapilipinas/Arduino-progressBAR-OLEDandRotaryEncoder/blob/master/OLEDandRotaryEncoder.ino
void drawProgressbar(int x, int y, int width, int height, int progress)
{

  progress = progress > 100 ? 100 : progress;
  progress = progress < 0 ? 0 : progress;

  float bar = ((float)(width - 1) / 100) * progress;

  display.drawRect(x, y, width, height, WHITE);
  display.fillRect(x + 2, y + 2, bar, height - 4, WHITE);

  // Display progress text
  if (height >= 15)
  {
    display.setCursor((width / 2) - 3, y + 5);
    display.setTextSize(1);
    display.setTextColor(WHITE);
    if (progress >= 50)
      display.setTextColor(BLACK, WHITE); // 'inverted' text

    display.print(progress);
    display.print("%");
  }
}

void handleBuffer()
{
  switch (pageDataConverter.command)
  {
  case 'b':
    display.clearDisplay();
    display.drawBitmap(
        pageDataConverter.bmpdata.x,
        pageDataConverter.bmpdata.y,
        pageDataConverter.bmpdata.bmp,
        pageDataConverter.bmpdata.w,
        pageDataConverter.bmpdata.h,
        WHITE);
    displayOLED();
    CompositeSerial.println(F("msg_bmp_ok"));
    break;
  case 'c':
    display.clearDisplay();
    bargraph.clear();
    CompositeSerial.println(F("msg_clear_ok"));
    break;
  case 'd':
    showDebugScreen = true;
    debugText(F("DEBUG!"));
    CompositeSerial.println(F("msg_debug_ok"));
    break;
  case 'g':
    drawGraph();
    CompositeSerial.println(F("msg_graph_ok"));
    break;
  case 'p':
    debugText("ping");
    CompositeSerial.println(F("msg_ping"));
    break;
  case 's':
    debugText("settings");
    bargraph.setBrightness(pageDataConverter.settingsdata.bargraphBrightness);
    maxDisplayOnTime = pageDataConverter.settingsdata.maxDisplayOnTime;
    CompositeSerial.println(F("msg_settings_ok"));
    break;
  case 't':
    display.clearDisplay();
    display.setTextSize(pageDataConverter.textdata.size);                          // Normal 1:1 pixel scale
    display.setTextColor(SSD1306_WHITE);                                           // Draw white text
    display.setCursor(pageDataConverter.textdata.x, pageDataConverter.textdata.y); // Start at top-left corner
    display.println(pageDataConverter.textdata.text);
    displayOLED();
    CompositeSerial.println(F("msg_text_ok"));
    break;
  default:
    char errorText[128];
    sprintf(errorText, "dafuq\ncommand:%c\nts:%lu", pageDataConverter.command, millis());
    debugText(errorText);
    CompositeSerial.println(F("err_unrecongnised_command"));
    break;
  }
  newDataInBuffer = false;
}

void setup()
{
  // Setup our I/O pins.
  pinMode(TRIGGER_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  // Setup HID and serial coms.
  HID.registerComponent();
  CompositeSerial.registerComponent();
  CompositeSerial.begin(115200);
  CompositeSerial.setTimeout(200);

  // Start display.
  display.begin(SSD1306_SWITCHCAPVCC, DISPLAY_I2C_ADDRESS);

  // Start bargraph and put the test pattern on the bargraph.
  bargraph.begin(BARGRAPH_I2C_ADDRESS);
  initGraph();

  // Zero the buffer for fresh data
  clearBuffer();

  // Tell the host the boot is complete.
  CompositeSerial.print(F("msg_booted_ok"));
}

void loop()
{
  digitalWrite(LED_PIN, HIGH);

  // If data is sat in the CompositeSerial buffer, place in in the pageDataConverter buffer.
  while (CompositeSerial.available() > 0)
  {
    clearBuffer();
    CompositeSerial.readBytes(pageDataConverter.buffer, sizeof(pageDataConverter.buffer));
    newDataInBuffer = true;
  }

  // If we have new data, lets read its command byte and decide how to handle it.
  if (newDataInBuffer)
  {
    handleBuffer();
    clearBuffer();
    memcpy(displayBuffer, display.getBuffer(), sizeof(displayBuffer));
  }

  // Have we hit the display timeout yet?
  if (millis() - displayOnTime > maxDisplayOnTime)
  {
    display.clearDisplay();
    display.display();
    fadeOutGraph();
    displayOnTime = 0;
  }

  // Was the trigger activated?
  trigger.read();
  if (trigger.wasPressed())
  {
    while (!trigger.wasReleased() && progress < 100)
    {
      trigger.read();
      digitalWrite(LED_PIN, LOW);
      progress += 2;

      drawProgressbar(64, 32 / 2 - 4, 64, 16, progress);
      displayOLED();
    }

    display.clearDisplay();

    if (progress == 100)
    {
      CompositeSerial.print(F("msg_data_req"));
    }
    else
    {
      display.drawBitmap(0, 0, displayBuffer, 128, 32, WHITE);
      displayOLED();
    }

    progress = 0;
  }
}