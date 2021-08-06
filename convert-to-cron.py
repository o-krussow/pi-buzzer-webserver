import os
import json

with open('timedb.json', 'r') as fp:
    times = json.load(fp)

os.popen("crontab -r")

tmpfile = os.popen("mktemp /tmp/cron-clock-XXXXX").read()

print(tmpfile)
for time in times:
    print(time)    
    os.popen(("echo {} {} \* \* 1-5 python3 /home/pi/python/webserver/buzz.py >> "+tmpfile).format(time.split(":")[1], time.split(":")[0])+"\n")
    
os.popen("crontab "+tmpfile) 
os.popen("rm "+tmpfile)
    
