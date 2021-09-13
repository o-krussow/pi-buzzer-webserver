# Simple python scripts + webserver used as a production buzzer controller.

- webserver.py is run using a service file (a copy of which is in this folder)

- webserver.py runs a simple http server, which handles the post and get requests

- when a post request is sent to webserver.py, it handles it by activating gpio pins to activate the relays

- webserver.py also keeps a copy (timedb.json) of the buzzer times so they will survive across reboots

- webserver.py syncs and parses the buzzer times from the web interface into pi (the default user's) crontab.

- cron runs buzz.py, which is actually what buzzes the buzzer on a schedule.

- one nice thing about this design is that webserver.py doesn't have to be running for the buzzer to go off, since cron is what runs buzz.py which in turn buzzes the buzzer.

- Keep in mind: If you move webserver.py or this folder out of /home/pi, there will be problems unless you adjust the CONFIGURATION section in the top of webserver.py

- /boot IS MOUNTED AS READ ONLY. Because of this, I've put packages that updated kernels would pull down on hold using apt. apt update & apt upgrade should work fine, the kernel just won't be upgraded.
    - To update the kernel, edit /etc/fstab and (ONLY) omit the ro, part of the /boot line and reboot
    From this
    ```
    PARTUUID=5c2ce0d6-01  /boot           vfat    ro,noatime                0 2
    ```
    To this
    ```
    PARTUUID=5c2ce0d6-01  /boot           vfat    noatime                0 2
    ```

# NGINX + SSL

- nginx is being used as a proxy for webserver.py, so it provides http auth and ssl (https)

I generated an SSL cert using:
```
sudo openssl req -x509 -nodes -days 5475 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt
```

If the IP of this Pi changes, this certificate needs to be regenerated using this command^^

Additionally: 
```
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
```

Following this [guide.](https://www.digitalocean.com/community/tutorials/how-to-create-a-self-signed-ssl-certificate-for-nginx-in-ubuntu-16-04)

to simplify the configuration of nginx, if I were you I would just copy nginx from this folder into /etc/ after installing nginx
```
rm -r /etc/nginx
cp -pr nginx /etc/nginx
```

# NTP

- this raspberry pi is using ntpd to keep the time accurate. (from what i've seen, it keeps it very, very accurate)
- What this means is that the raspberry pi sync its time with an assortment of public ntp servers.