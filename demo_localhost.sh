#!/bin/bash

HEIGHT=15
WIDTH=40
CHOICE_HEIGHT=4
BACKTITLE="Ecosystem Service Web Services (ESWS)"
TITLE="InVEST WY Demo"
MENU="Choose one of the following options:"

OPTIONS=(1 "Clean demo start"
         2 "Stop demo")

CHOICE=$(dialog --clear \
                --backtitle "$BACKTITLE" \
                --title "$TITLE" \
                --menu "$MENU" \
                $HEIGHT $WIDTH $CHOICE_HEIGHT \
                "${OPTIONS[@]}" \
                2>&1 >/dev/tty)

clear
case $CHOICE in
        1)
        #reset WPS client
        rm tools/wpsclient/db.sqlite3
	rm -rf tools/wpsclient/migrations
        python3 tools/wpsclient/manage.py makemigrations wpsclient
	python3 tools/wpsclient/manage.py migrate

        #start servers
        python3 tools/wpsclient/manage.py runserver &
        printf "%s\n" $! > demo.pid
        
        python3 tools/http_server.py &
        printf "%s\n" $! >> demo.pid

        sh run_wps_server.sh &
        printf "%s\n" $! >> demo.pid

        #load client demo
        sleep 5s
        sh tools/wpsclient/investwydata.sh

        #open browser
        google-chrome-stable http://127.0.0.1:8000/test/wy &
        ;;
        2)
        while read p; do kill -SIGTERM $p; done < demo.pid
        ;;
esac
