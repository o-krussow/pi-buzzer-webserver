import RPi.GPIO as GPIO
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
import json
import time



#
#   PATHS ARE IMPORTANT, MAKE SURE EVERYTHING IN HERE IS POINTING TO THE RIGHT PLACE
#

#---------Configuration----------
host_name = '127.0.0.1'    # Leave this if using nginx
host_port = 8000           # this too
GPIO_PIN = 26
timedb_path = "/home/pi/webserver/timedb.json"
this_file_path="/home/pi/webserver"  #This is the folder this program is kept in. Keep this program in the same folder as the other programs, and change this entry if this program is moved.
#--------------------------------

dates = {}
send_err = ""


class MyServer(BaseHTTPRequestHandler):
    """ A special implementation of BaseHTTPRequestHander for reading data from
        and control GPIO of a Raspberry Pi
    """

    def do_HEAD(self):
        """ do_HEAD() can be tested use curl command 
            'curl -I http://server-ip-address:port' 
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_GET(self):
        """ do_GET() can be tested using curl command 
            'curl http://server-ip-address:port' 
        """
        global send_err
        html = '''
            <html>
            <body style="width:960px; margin: 20px auto;">
            <h1>Buzzer Controls</h1>
            <br>
            <p>Current uptime: {}</p>
            <form action="/" method="POST">
                Reboot Pi (careful):
                <input type="submit" name="restart" value="Restart">
            </form>
            <p>Time and Temperature update on refresh.</p>
            <p>Current temperature is {}</p>
            <p>Current time is {}</p>
            <br>
            <form action="/" method="POST">
                Cycle Relay (careful):
                <input type="submit" name="submit" value="Buzz">
            </form>
            <form action="/" accept-charset="utf-8" method="POST">
                <label for="add-time">Add time (syntax hh:mm, use 24 hour time):</label>
                <input type="text" id="add-time" name="add-time"><br>
            </form>
            <form action="/" accept-charset="utf-8" method="POST">
                <label for="del-time">Delete time (syntax hh:mm, use 24 hour time):</label>
                <input type="text" id="del-time" name="del-time"><br>
            </form>
           
            <b>{}</b>
            <br>
            <table style="width:50%">
                <tr>
                    <th>Time</th>
                    <th>Belltype</th>
                </tr>
                {}
            </body>
            </html>
        '''

        times_html = ""
                        #Adding times as table into html
        for d in dates: #what a great way of doing this!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            times_html+="<tr>"
            times_html+="   <td>"+d+"</td>"
            times_html+="   <td>"+dates[d]+"</td>"
            times_html+="</tr>"

        temp = os.popen("/opt/vc/bin/vcgencmd measure_temp").read()
        uptime = os.popen("uptime").read()
        self.do_HEAD()
        print(send_err)
        self.wfile.write(html.format(uptime, temp[5:], datetime.datetime.now().strftime("%H:%M:%S"), send_err, times_html).encode("utf-8"))
        send_err = ""


    def do_POST(self): #everytime the server recieves a post, this is run. same concept applies to the other do_whatever functions
        """ do_POST() can be tested using curl command 
            'curl -d "submit=On" http://server-ip-address:port' 
        """
        content_length = int(self.headers['Content-Length'])    # Get the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")   # Get the data
        post_id = post_data.split('=')[0]
        post_data = post_data.split('=')[1]    # Only keep the value
       
        global send_err

        # GPIO setup
        init_gpio(GPIO_PIN)

        if post_id == "submit":     #this is the "backend" stuff for when a browser posts the buzz button being pressed.
            print("Relay will {}".format(post_data))
            if post_data == 'Buzz':
                relay_on(GPIO_PIN)
                time.sleep(2)
                relay_off(GPIO_PIN)

        if post_id == "restart": 
            print("Relay will {}".format(post_data))
            os.popen("sudo reboot")
        
        if post_id == "add-time": #add time to db
            try:
                newdate = datetime.datetime.strptime(post_data.replace("%3A", ":"), "%H:%M") #using datetime is an easy way of parsing dates so i dont need to regex things myself
                dates[newdate.strftime("%H:%M")] = "default"
            except ValueError:  #if not a valid date then it will complain
                send_err += "Invalid Time \""+post_data.replace("%3A", ":")+"\" Example: 6:15\n"
                self._redirect('/')

        if post_id == "del-time": #rm time from db
            try:
                deldate = datetime.datetime.strptime(post_data.replace("%3A", ":"), "%H:%M")
                del dates[deldate.strftime("%H:%M")]
            except (ValueError, KeyError): #if not valid date or date not listed in db then it will complain
                send_err += "Invalid Time \""+post_data.replace("%3A", ":")+"\" Example: 6:15\n"
                self._redirect('/')

        with open(timedb_path, 'w+') as fp: # On post, save time db to json to be safe.
            json.dump(dates, fp)
        
        submit_crontab()
        
        self._redirect('/')    # Redirect back to the root url

def submit_crontab():
    os.popen("crontab -r")

    tmpfile = os.popen("mktemp /tmp/cron-clock-XXXXX").read() #make a temporary file in a tmpfs that we can write our cron stuff to

    for date in dates:
        os.popen(("echo {} {} \* \* 1-5 /usr/bin/python3 "+this_file_path+"/buzz.py >> "+tmpfile).format(date.split(":")[1], date.split(":")[0])+"\n") #write times to file

    os.popen("crontab "+tmpfile) #install crontab
    os.popen("rm "+tmpfile) #remove tmpfile


def init_gpio(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(pin, GPIO.OUT)


def relay_on(pin): #relay on function, if relay gets stuck then it will retry until it gets unstuck. if it tries more than 100 times (30 seconds) it will give up.
    global send_err
    attempt_count = 0
    while GPIO.input(pin) != 1:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)
        attempt_count+=1
        if attempt_count > 1:
            print("relay stuck, retrying off")
        if attempt_count > 100:
            send_err+=("Could not turn on relay on pin "+str(pin)+"\n")   
            break

def relay_off(pin):
    global send_err
    attempt_count = 0
    while GPIO.input(pin) != 0:
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)
        attempt_count+=1
        if attempt_count > 1:
            print("relay stuck, retrying off")
        if attempt_count > 100:
            send_err+=("Could not turn off relay on pin "+str(pin)+"\n")   
            break


if __name__ == '__main__':
    try:
        with open(timedb_path, 'r') as fp: #load dates from last session
            dates = json.load(fp)
    except FileNotFoundError:
        print(".json from last session not found, making a new one")

    http_server = HTTPServer((host_name, host_port), MyServer)
    print("Server Starts - %s:%s" % (host_name, host_port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
        GPIO.cleanup()
