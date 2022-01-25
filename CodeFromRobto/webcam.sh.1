#!/bin/bash
cd ~
wget  http://osoyoo.com/driver/mjpg-streamer.tar.gz
tar  -xzvf   mjpg-streamer.tar.gz
sudo apt-get install libv4l-dev libjpeg8-dev -y
sudo apt-get install subversion -y
if !  grep -q "bcm2835-v4l2" /etc/modules
then
	sudo sed -i -e "\$abcm2835-v4l2" /etc/modules
fi
if ! grep -q "i2c-bcm2708" /etc/modules
then
	sudo sed -i -e "\$ai2c-bcm2708" /etc/modules
fi

sudo sed -i 's/V4L2_PIX_FMT_MJPEG/V4L2_PIX_FMT_YUYV/g' ~/mjpg-streamer/plugins/input_uvc/input_uvc.c
cd /usr/include/arm-linux-gnueabihf/bits
sudo rm statx.h
sudo wget http://osoyoo.com/driver/statx.h
cd  ~/mjpg-streamer && sudo make all
