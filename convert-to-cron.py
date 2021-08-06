import os
import json

with open('timedb.json', 'r') as fp:
    times = json.load(fp)

for time in times:
    os.popen("(crontab -l; echo {} {} \* \* 1-5 python3 /home/pi/python/webserver/buzz.py) | crontab -".format(time.split(":")[1], time.split(":")[0]))


