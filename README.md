# Lightning-Detection-AS3935-and-Central-Weather-Bureau


## Introduction
Microcontroller: Raspberry Pi 3b+, Raspberry Pi 4  
Sensor: AS3935, Lightning Detector  
Laguage: Python, Shell  
Protocal: SPI protocal, which is different from others.  
<img width="400" height="400" src="https://www.taiwaniot.com.tw/wp-content/uploads/2019/08/15441-SparkFun_Lightning_Detector_-_AS3935_-01.jpg"/><br />  

## NIU file
In the NIU file, files inculdes: start.sh, rc.local, and crontab these three files can help you schedule the lightning detectiing system (with AS3935) automatically.


## Lightning_catching CWB file
In this file, you can use the code here to automatically download the instantaneous Lightning Detection Data from the CWB.  
The information from the CWB has been interpreted by the code.  
The output data format includes: (1) The detected lightning data by CWB, (2) The distance of the piece of data from the location of you
Note: You can change the value of the "longitude" and l"atitude" in the program to know that each lightning event is kilometers away from the location you entered

## Links
1. I2C protocal: https://github.com/ironsheep/lightning-detector-MQTT2HA-Daemon
1. AS3935 Documentation: https://www.mouser.com/datasheet/2/588/ams_AS3935_Datasheet_EN_v5-1214568.pdf
