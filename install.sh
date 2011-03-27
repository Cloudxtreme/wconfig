#!/bin/bash
wget https://github.com/webnull/wconfig/raw/master/wconfig.py -O ~/wconfig
chmod +x ~/wconfig
userpath=`cd ~; pwd`

if [ -f /usr/bin/sudo ]
then
	echo "I need your password to copy wconfig to /usr/bin, using sudo"
	sudo cp "$userpath/wconfig" /usr/bin/wconfig
else
        echo "I need your password to copy wconfig to /usr/bin, using su"
	su root -c "cp \"$userpath/wconfig\" /usr/bin/wconfig\""
fi
