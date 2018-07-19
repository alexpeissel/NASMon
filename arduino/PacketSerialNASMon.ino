/*############################
  # Libraries
  ############################*/
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "Adafruit_LEDBackpack.h"
#include <PacketSerial.h>
#include <Wire.h>

/*############################
  # Globals
  ############################*/
// Packet structs
// All packets are 136 bytes
struct TextData {
  byte dataType;   // 1 byte
  byte textSize;   // 1 byte
  byte cursorX;    // 1 byte
  byte cursorY;    // 1 byte
  char text[128];  // 128 bytes
} __attribute__((packed));

struct BMPData {
  byte dataType;           // 1 byte
  byte bmpWidth;           // 1 byte
  byte bmpHeight;          // 1 byte
  byte bmpX;               // 1 byte
  byte bmpY;               // 1 byte
  unsigned char bmp[128];  // 128 bytes
} __attribute__((packed));

struct BargraphData {
  byte dataType;      // 1 byte
  char bargraph[24];  // 24 bytes
} __attribute__((packed));

// PageDataConverter union
union PageDataConverter {
  TextData textdata;
  BMPData bmpdata;
  BargraphData bargraphdata;
  byte raw[136];
};

//PageDataConverter union
static PageDataConverter pageDataConverter;

// PacketSerial
PacketSerial myPacketSerial;

// Display
#define OLED_RESET 4
#define DISPLAY_I2C_ADDRESS 0x3C
Adafruit_SSD1306 display(OLED_RESET);

// Bargraph
#define BARGRAPH_LENGTH 23
#define BARGRAPH_I2C_ADDRESS 0x70
Adafruit_24bargraph bargraph = Adafruit_24bargraph();

// Sensor
#define SENSOR_PIN 2
boolean waveHappened = false;

/*############################
  # Methods
  ############################*/
void onPacketReceived(const uint8_t* buffer, size_t size)
{
  // Zero the converter buffer
  resetRaw();

  // Handle the data now in buffer
  switch (buffer[0]) {
    case 1:
      // Clear
      clearDisplay();
      clearBargraph();
      sendAck("clr");
      break;
    case 2:
      // Reply to ping
      sendPong();
      break;
    case 3:
      // Reply with wave status
      sendWaveStatus();
    case 4:
      //Copy the buffer to the converter
      memcpy(pageDataConverter.raw, buffer, sizeof(pageDataConverter.raw));
      // Text
      drawText(
        pageDataConverter.textdata.textSize,
        pageDataConverter.textdata.cursorX,
        pageDataConverter.textdata.cursorY,
        pageDataConverter.textdata.text,
        sizeof(pageDataConverter.textdata.textSize)
      );
      sendAck("txt");
      break;
    case 5:
      // BMP
      memcpy(pageDataConverter.raw, buffer, sizeof(pageDataConverter.raw));
      drawBMP(
        pageDataConverter.bmpdata.bmpWidth,
        pageDataConverter.bmpdata.bmpHeight,
        pageDataConverter.bmpdata.bmpX,
        pageDataConverter.bmpdata.bmpY,
        pageDataConverter.bmpdata.bmp
      );
      sendAck("bmp");
      break;
    case 6:
      // Bargraph
      memcpy(pageDataConverter.raw, buffer, sizeof(pageDataConverter.raw));
      drawGraph(pageDataConverter.bargraphdata.bargraph);
      sendAck("bar");
      break;
    case 7:
      // Echo
      myPacketSerial.send(buffer, size);
      break;
    default:
      // Error
      memcpy(pageDataConverter.raw, buffer, sizeof(pageDataConverter.raw));
      char error_response[] = "error";
      myPacketSerial.send("error", sizeof(error_response));
      break;
  }

  //
  //  char returnBuffer[136];
  //
  //  String dataType(pageDataConverter.textdata.dataType, DEC);
  //  String textSize(pageDataConverter.textdata.textSize, DEC);
  //  String cursorX(pageDataConverter.textdata.cursorX, DEC);
  //  String cursorY(pageDataConverter.textdata.cursorY, DEC);
  //  String text(pageDataConverter.textdata.text);
  //  String returnString(dataType + textSize + cursorX + cursorY + text);
  //  //myPacketSerial.send(pageDataConverter.textdata.text, 256);
  //  returnString.toCharArray(returnBuffer, 136);
  //  //myPacketSerial.send(returnBuffer, 256);
}

void resetRaw()
{
  memset(pageDataConverter.raw, 0, sizeof(pageDataConverter.raw));
}

void sendPong()
{
  const char responseString[] = "pong";
  myPacketSerial.send(responseString, sizeof(responseString));
}

void sendAck(char idString[])
{
  char responseString[7];
  
  sprintf(responseString, "ack_%s", idString);
  myPacketSerial.send(responseString, sizeof(responseString));
}

void sendWaveStatus()
{
  //const char waveTrueString[] = "wav_y";
  //const char waveFalseString[] = "wav_n";
  
  if (waveHappened) {
    myPacketSerial.send(1, sizeof(byte));
    bargraph.setBar(1, LED_GREEN);
    bargraph.writeDisplay();
  } else {
    myPacketSerial.send(0, sizeof(byte));
    bargraph.setBar(1, LED_RED);
    bargraph.writeDisplay();
  }
  waveHappened = false;
}

void drawInitialGraph()
{
  for (int b = 0; b < 24; b++ ) {
    if ((b % 3) == 0)  bargraph.setBar(b, LED_RED);
    if ((b % 3) == 1)  bargraph.setBar(b, LED_YELLOW);
    if ((b % 3) == 2)  bargraph.setBar(b, LED_GREEN);
  }
  bargraph.writeDisplay();
}

void drawText(byte* textSize, byte* cursorX, byte* cursorY, char text[], byte textLength)
{
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println(pageDataConverter.textdata.text);
  display.display();
}

void drawBMP(byte bmpWidth, byte bmpHeight, byte bmpX, byte bmpY, byte bmp[])
{
  for (byte x = 0; x <= bmpWidth; x++) {
    display.drawPixel(10, 10, WHITE);
  }
  myPacketSerial.send(bmp, sizeof(pageDataConverter.bmpdata.bmp));
}

void drawGraph(char bargraphData[])
{
  for (byte i = 0; i <= 24; i++) {
    switch (bargraphData[i]) {
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

void clearDisplay()
{
  display.clearDisplay();
  display.display();
}

void clearBargraph()
{
  bargraph.clear();
  bargraph.writeDisplay();
}

/*############################
  # Setup
  ############################*/
void setup()
{
  // Start PacketSerial
  myPacketSerial.begin(115200);
  myPacketSerial.setPacketHandler(&onPacketReceived);
  resetRaw();

  // Start display
  display.begin(SSD1306_SWITCHCAPVCC, DISPLAY_I2C_ADDRESS);
  display.setTextColor(WHITE);
  display.display();

  // Start bargraph
  bargraph.begin(BARGRAPH_I2C_ADDRESS);
  drawInitialGraph();

  // Start sensor
  pinMode(SENSOR_PIN, INPUT);

  // Clear displays
  delay(2000);
  clearDisplay();
  clearBargraph();
}

/*############################
  # Loop
  ############################*/
void loop()
{
  // Get the wave status
  if (digitalRead(SENSOR_PIN) == LOW) {
    waveHappened = true;
  }

  // Get latest packet
  myPacketSerial.update();
}

