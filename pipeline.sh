#!/bin/bash

IMAGE_DIR='/c/Users/nadav/OneDrive/Nadav/Academic/מכללה/תשפו/96504.1.1 סמ ב משלימות עיבוד תמונה/מבחן מועד א הגשות/'
ls -1 "${IMAGE_DIR}"/*.jpg
python pipeline.py "${IMAGE_DIR}"/*.jpg