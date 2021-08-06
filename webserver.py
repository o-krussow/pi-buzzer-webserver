import RPi.GPIO as GPIO
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import datetime
import json
import time

host_name = '10.17.56.96'    # Change this to your Raspberry Pi IP address
host_port = 8000

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
            <p>Current temperature is {}</p>
            <form action="/" method="POST">
                Buzz Now (careful):
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

        for d in dates:
            times_html+="<tr>"
            times_html+="   <td>"+d+"</td>"
            times_html+="   <td>"+dates[d]+"</td>"
            times_html+="</tr>"

        temp = os.popen("/opt/vc/bin/vcgencmd measure_temp").read()
        self.do_HEAD()
        print(send_err)
        self.wfile.write(html.format(temp[5:], send_err, times_html).encode("utf-8"))
        send_err = ""


    def do_POST(self):
        """ do_POST() can be tested using curl command 
            'curl -d "submit=On" http://server-ip-address:port' 
        """
        content_length = int(self.headers['Content-Length'])    # Get the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")   # Get the data
        print(post_data)
        post_id = post_data.split('=')[0]
        post_data = post_data.split('=')[1]    # Only keep the value
       
        global send_err

        # GPIO setup
        init_gpio(26)

        if post_id == "submit":
            if post_data == 'Buzz':
                relay_on(26)
                time.sleep(0.5)
                relay_off(26)
            print("Relay is {}".format(post_data))

        #for 12 hour time, use (%I-%M-%S %p)

        if post_id == "add-time":
            try:
                newdate = datetime.datetime.strptime(post_data.replace("%3A", ":"), "%H:%M")
                print(newdate)
                dates[newdate.strftime("%H:%M")] = "default"
            except ValueError:
                send_err = "Invalid Time \""+post_data.replace("%3A", ":")+"\""
                self._redirect('/')

        if post_id == "del-time":
            try:
                deldate = datetime.datetime.strptime(post_data.replace("%3A", ":"), "%H:%M")
                print(deldate.strftime("%H:%M"))
                del dates[deldate.strftime("%H:%M")]
            except (ValueError, KeyError):
                send_err = "Invalid Time \""+post_data.replace("%3A", ":")+"\""
                self._redirect('/')

        with open('timedb.json', 'w+') as fp: # On post, save time db to json to be safe.
            json.dump(dates, fp)
        for d in dates:
            os.popen("(crontab -l; echo {} {} \* \* 1-5 /usr/bin/python3 /home/pi/python/webserver/buzz.py) | crontab -".format(d.split(":")[1], d.split(":")[0]))
        self._redirect('/')    # Redirect back to the root url


def init_gpio(pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(pin, GPIO.OUT)


def relay_on(pin):
    attempt_count = 0
    while GPIO.input(pin) != 1:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)
        attempt_count+=1
        if attempt_count > 1:
            print("relay stuck, retrying off")

def relay_off(pin):
    attempt_count = 0
    while GPIO.input(pin) != 0:
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)
        attempt_count+=1
        if attempt_count > 1:
            print("relay stuck, retrying off")





if __name__ == '__main__':
    try:
        with open('timedb.json', 'r') as fp: #load dates from last session
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
