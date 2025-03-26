# INTERNSHIP_PROJECT

This is an internship project about the title - Realtime Document Scanning using IoT Devices.
In this, when the application is run, the user gets to choose from 3 options
  1. To upload an image containing a document.
  2. To access the webcam and capture an image to scan the document.
  3. To use an ESP32CAM, capture an dimage and send it to the server for scanning.

To run this program, simply run the scanner.py file and if you are using the ESP32CAM, upload the ESP_TO_SERVER.ino code into it first, then copy the IP address shown in the serial monitor of the IDE.
To see the documents, you need to create a trial account in SAP Cockpit and enable "SAP Hana Cloud" and create its instance. There, you will have to create a table named SCANNED_DOCUMENTS with the following fields - 
