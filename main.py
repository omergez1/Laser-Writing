from servo_control import start_servo_spin, stop_servo_spin
from stage import WaveguideWriter
import serial

PORT = "COM5"  # adjust to your COM
BAUD = 19200   # please check your acctual boudrte

# waits until spinning

# 1) Connect the stage FIRST
wg = WaveguideWriter()
if not wg.connect():
    print("❌ Failed to connect to stage")
    raise SystemExit(1)

# 2) Home
wg.home_all()

# 3) Open laser serial ONCE
ser = serial.Serial(
    port=PORT, baudrate=BAUD,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=2
)

# 4) (optional) quick move test
start = wg.get_position('X')
wg.move_to_position_absolute('X', start + 50)
wg.move_to_position_absolute('X', start)

# 5) Write waveguide (PASS ser)  - here is the actul writing with the parameters defined
wg.write_waveguide(
    length=1000, width=500, step_size=100, repeat=6,
    speed=100, length_axis='X', offset=(100, 100, 100),
    ser=ser, scan_accel=5000, return_home=True
)

# 6) Cleanup
wg.disconnect()
ser.close()
# servo stop spin
print("🏁 Laser writing complete.")
