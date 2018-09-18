# Description

Arduino-powered system monitor, powered by a Python backend.  Built for
getting information quickly out of headless hardware, like a NAS.

TODO: Add a picture of the hardware

# Features

Capable of displaying text, images and values on an LED bar-graph.  All
fully configurable from the backend; no extra Arduino code required!

Run system commands/scripts and display their results on the monitor, e.g. :
* CPU usage
* RAM usage
* Current internal/external IP
* Analog meters
* CPU temperature

Configuration is simple and flexible using YAML formatted 'pages'.  To scroll
through all pages, hold your hand up to the the IR sensor.

Communication between the host PC and monitor hardware is using a custom protocol,
facilitated by the [PacketSerial](https://github.com/bakercp/PacketSerial) library.

* Display the current hostname:
```
name: "Current hostname"

commands:
- command: "hostname"
  variable_identifier: "hostname"

text:
  - text: "$hostname"
    x: 0
    y: 0
    size: 1
```

## TODO

Lots of things to do:

* Finish this README.md
* Write install script
* Support running server as daemon
* Fade displays after not receiving any sensor input for 15 seconds
* Make image sizing more efficient

## Getting Started (TODO)

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites (TODO)

What things you need to install the software and how to install them

```
Give examples
```

### Hardware (TODO)

The NASMon hardware is made completely out of off-the-shelf items:
* [Arduino Nano] - Microcontroller
* [Adafruit Bi-Color 24-Bar LED Bargraph] - (https://www.adafruit.com/product/1721) i2c LED bargraph controlled by a MAX7219
* [128 x 32 OLED] - i2c OLED display
* [IR proximity sensor]

TODO: Wiring diagram

The electronics is designed to fit inside a laptop-sized optical bay.

### Installing (TODO)

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Built With (TODO)

* [PacketSerial](https://github.com/bakercp/PacketSerial) - Arduino packet communication library

## Authors

* **Alex Peissel** - *Initial work* - [alexpeissel](https://github.com/alexpeissel)

See also the list of [contributors](https://github.com/alexpeissel/NASMon/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* [Spaceboard] https://github.com/igor47/spaceboard - A project using PacketSerial and Python
