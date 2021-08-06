import RPi.GPIO as GPIO
import time

def relay_on(pin): #relay on function, if relay gets stuck then it will retry until it gets unstuck. if it tries more than 300 times (30 seconds) it will give up.
    attempt_count = 0
    while GPIO.input(pin) != 1:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.1)
        attempt_count+=1
        if attempt_count > 1:
            print("relay stuck, retrying off")
        if attempt_count > 300:
            break

def relay_off(pin):
    attempt_count = 0
    while GPIO.input(pin) != 0:
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)
        attempt_count+=1
        if attempt_count > 1:
            print("relay stuck, retrying off")
        if attempt_count > 300:
            break


if __name__ == "__main__":
    # GPIO setup
    GPIO_PIN=26
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(GPIO_PIN,GPIO.OUT)

    relay_on(GPIO_PIN)
    time.sleep(1.3)
    relay_off(GPIO_PIN)

    GPIO.cleanup()
