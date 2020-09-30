# Lightning-Detection-AS3935-and-Central-Weather-Bureau


## Introduction
Microcontroller: Raspberry Pi 3b+, Raspberry Pi 4
Sensor: AS3935, Lightning Detector
![image](data:image/jpeg;base64,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)

