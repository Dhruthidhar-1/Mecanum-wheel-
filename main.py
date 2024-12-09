import network
import socket
import time
from machine import Pin

# Create an LED object on pin 'LED'
led = Pin('LED', Pin.OUT)
# Create four motor driver objects
motor_a_forward = Pin(18, Pin.OUT)
motor_a_backward = Pin(19, Pin.OUT)
motor_b_forward = Pin(20, Pin.OUT)
motor_b_backward = Pin(21, Pin.OUT)

# Wi-Fi credentials
ssid = 'robosoccer'
password = 'iitmadras'

def move_forward():
    motor_a_forward.value(1)
    motor_b_forward.value(1)
    motor_a_backward.value(0)
    motor_b_backward.value(0)

def move_backward():
    motor_a_forward.value(0)
    motor_b_forward.value(0)
    motor_a_backward.value(1)
    motor_b_backward.value(1)

def move_stop():
    motor_a_forward.value(0)
    motor_b_forward.value(0)
    motor_a_backward.value(0)
    motor_b_backward.value(0)
    
def move_left():
    motor_a_forward.value(1)
    motor_b_forward.value(0)
    motor_a_backward.value(0)
    motor_b_backward.value(1)

def move_right():
    motor_a_forward.value(0)
    motor_b_forward.value(1)
    motor_a_backward.value(1)
    motor_b_backward.value(0)

move_stop()

# HTML template for the webpage
def webpage():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Joystick Controlled Robot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            /* Style for the joystick container to position it in the bottom-right corner */
            body {
                margin: 0;
                padding: 0;
            }

            #joystick-container {
                position: absolute;
                bottom: 20px;  /* Distance from bottom */
                right: 20px;   /* Distance from right */
                width: 100px;  /* Set size of joystick area */
                height: 100px; /* Set size of joystick area */
                pointer-events: auto; /* Allow joystick interactions */
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
                width: 40px; /* Size of the joystick handle */
                height: 40px; /* Size of the joystick handle */
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

        <!-- Joystick Container in the bottom-right corner -->
        <div id="joystick-container">
            <div id="joystick">
                <div id="handle"></div>
            </div>
        </div>

        <script>
            const joystick = document.getElementById('joystick');
            const handle = document.getElementById('handle');
            let centerX = joystick.offsetWidth / 2;
            let centerY = joystick.offsetHeight / 2;

            joystick.addEventListener('pointerdown', startDrag);
            joystick.addEventListener('pointermove', moveDrag);
            joystick.addEventListener('pointerup', stopDrag);
            joystick.addEventListener('pointerleave', stopDrag);

            let dragging = false;

            function startDrag(event) {
                dragging = true;
                moveDrag(event);
            }

            function moveDrag(event) {
                if (!dragging) return;

                const rect = joystick.getBoundingClientRect();
                const dx = event.clientX - rect.left - centerX;
                const dy = event.clientY - rect.top - centerY;

                // Limit the movement to within the circle (the joystick boundary)
                const distance = Math.min(Math.sqrt(dx * dx + dy * dy), centerX - 20);
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
    return str(html)

# Connect to WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Wait for Wi-Fi connection
connection_timeout = 10
while connection_timeout > 0:
    if wlan.status() >= 3:
        break
    connection_timeout -= 1
    print('Waiting for RoboSoccer Wi-Fi connection...')
    time.sleep(1)

# Check if connection is successful
if wlan.status() != 3:
    raise RuntimeError('Failed to establish a network connection with RoboSoccer WiFi')
else:
    print('Connection to RoboSoccer network successful!')
    network_info = wlan.ifconfig()
    print('IP address:', network_info[0])

# Set up socket and start listening
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen()

print('Listening on', addr)

# Main loop to listen for connections
while True:
    try:
        conn, addr = s.accept()
        print('Got a connection from', addr)

        # Receive and parse the request
        request = conn.recv(1024)
        request = str(request)
        print('Request content = %s' % request)

        try:
            request = request.split()[1]
            print('Request:', request)
        except IndexError:
            pass

        # Process the joystick input
        if request.startswith('/joystick?'):
            params = request.split('?')[1]
            param_dict = dict(param.split('=') for param in params.split('&'))

            dx = int(param_dict.get('dx', 0))
            dy = int(param_dict.get('dy', 0))

            print(f"Joystick moved: dx={dx}, dy={dy}")

            if dy < -50:  # Forward
                move_forward()
            elif dy > 50:  # Backward
                move_backward()
            elif dx < -50:  # Left
                move_left()
            elif dx > 50:  # Right
                move_right()
            else:  # Stop
                move_stop()

        # Generate HTML response
        response = webpage()

        # Send the HTTP response and close the connection
        conn.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        conn.send(response)
        conn.close()

    except OSError as e:
        conn.close()
        print('Connection closed')
