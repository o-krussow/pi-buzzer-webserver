import RPi.GPIO as GPIO
import time

# GPIO setup
GPIO_PIN=26
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(GPIO_PIN,GPIO.OUT)

GPIO.output(GPIO_PIN,GPIO.HIGH)
time.sleep(0.1)
GPIO.output(GPIO_PIN,GPIO.LOW)

GPIO.cleanup()
