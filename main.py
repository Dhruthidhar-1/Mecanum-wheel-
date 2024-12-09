import network
import socket
import time
from machine import Pin

# Define motor pins
motor_front_left_forward = Pin(18, Pin.OUT)
motor_front_left_backward = Pin(19, Pin.OUT)
motor_front_right_forward = Pin(20, Pin.OUT)
motor_front_right_backward = Pin(21, Pin.OUT)
motor_back_left_forward = Pin(22, Pin.OUT)
motor_back_left_backward = Pin(23, Pin.OUT)
motor_back_right_forward = Pin(24, Pin.OUT)
motor_back_right_backward = Pin(25, Pin.OUT)

# Wi-Fi credentials
ssid = 'robosoccer'
password = 'iitmadras'

# Motor control functions
def move_forward():
    motor_front_left_forward.value(1)
    motor_front_right_forward.value(1)
    motor_back_left_forward.value(1)
    motor_back_right_forward.value(1)

    motor_front_left_backward.value(0)
    motor_front_right_backward.value(0)
    motor_back_left_backward.value(0)
    motor_back_right_backward.value(0)

def move_backward():
    motor_front_left_forward.value(0)
    motor_front_right_forward.value(0)
    motor_back_left_forward.value(0)
    motor_back_right_forward.value(0)

    motor_front_left_backward.value(1)
    motor_front_right_backward.value(1)
    motor_back_left_backward.value(1)
    motor_back_right_backward.value(1)

def move_left():
    motor_front_left_forward.value(0)
    motor_front_right_forward.value(1)
    motor_back_left_forward.value(0)
    motor_back_right_forward.value(1)

    motor_front_left_backward.value(1)
    motor_front_right_backward.value(0)
    motor_back_left_backward.value(1)
    motor_back_right_backward.value(0)

def move_right():
    motor_front_left_forward.value(1)
    motor_front_right_forward.value(0)
    motor_back_left_forward.value(1)
    motor_back_right_forward.value(0)

    motor_front_left_backward.value(0)
    motor_front_right_backward.value(1)
    motor_back_left_backward.value(0)
    motor_back_right_backward.value(1)

def move_stop():
    motor_front_left_forward.value(0)
    motor_front_right_forward.value(0)
    motor_back_left_forward.value(0)
    motor_back_right_forward.value(0)

    motor_front_left_backward.value(0)
    motor_front_right_backward.value(0)
    motor_back_left_backward.value(0)
    motor_back_right_backward.value(0)

move_stop()

# HTML template for joystick control
def webpage():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Joystick Controlled Robot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            #joystick-container {
                position: absolute;
                bottom: 20px;
                right: 20px;
                width: 150px;
                height: 150px;
            }

            #joystick {
                width: 100%;
                height: 100%;
                background: lightgray;
                border-radius: 50%;
                position: relative;
                touch-action: none;
            }

            #handle {
                width: 40px;
                height: 40px;
                background: gray;
                border-radius: 50%;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }
        </style>
    </head>
    <body>
        <h1>Robot Wi-Fi Control</h1>
        <div id="joystick-container">
            <div id="joystick">
                <div id="handle"></div>
            </div>
        </div>
        <script>
            const joystick = document.getElementById('joystick');
            const handle = document.getElementById('handle');
            const radius = joystick.offsetWidth / 2;

            let centerX = joystick.offsetWidth / 2;
            let centerY = joystick.offsetHeight / 2;
            let dragging = false;

            joystick.addEventListener('pointerdown', startDrag);
            joystick.addEventListener('pointermove', moveDrag);
            joystick.addEventListener('pointerup', stopDrag);
            joystick.addEventListener('pointerleave', stopDrag);

            function startDrag(event) {
                dragging = true;
                moveDrag(event);
            }

            function moveDrag(event) {
                if (!dragging) return;

                const rect = joystick.getBoundingClientRect();
                const dx = event.clientX - rect.left - centerX;
                const dy = event.clientY - rect.top - centerY;

                const distance = Math.min(Math.sqrt(dx * dx + dy * dy), radius - 20);
                const angle = Math.atan2(dy, dx);

                const adjustedX = distance * Math.cos(angle);
                const adjustedY = distance * Math.sin(angle);

                handle.style.transform = `translate(${adjustedX}px, ${adjustedY}px)`;

                fetch(`/joystick?dx=${Math.round(adjustedX)}&dy=${Math.round(adjustedY)}`);
            }

            function stopDrag() {
                dragging = false;
                handle.style.transform = 'translate(-50%, -50%)';
                fetch('/joystick?dx=0&dy=0');
            }
        </script>
    </body>
    </html>
    """
    return html

# Network setup
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

while wlan.status() != 3:
    print("Connecting to Wi-Fi...")
    time.sleep(1)

print("Connected to Wi-Fi!")
print("IP Address:", wlan.ifconfig()[0])

# Socket setup
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print("Listening on", addr)

while True:
    conn, addr = s.accept()
    print("Connection from", addr)
    request = conn.recv(1024).decode()

    if '/joystick?' in request:
        query = request.split(' ')[1]
        params = query.split('?')[1].split('&')
        dx = int(params[0].split('=')[1])
        dy = int(params[1].split('=')[1])

        if dy < -50:
            move_forward()
        elif dy > 50:
            move_backward()
        elif dx < -50:
            move_left()
        elif dx > 50:
            move_right()
        else:
            move_stop()

    response = webpage()
    conn.sendall('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n' + response)
    conn.close()
