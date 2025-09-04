import clr
import sys
import threading
import time
from System import Decimal

# ==== Load Kinesis DLLs ====
kinesis_path = r"C:\Program Files\Thorlabs\Kinesis"
sys.path.append(kinesis_path)
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.KCube.DCServoCLI")
clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo
from Thorlabs.MotionControl.GenericMotorCLI import MotorDirection

# ==== Fixed Hardware Configuration ====
SERIAL_NO = "27270740"           # 🧩 Fixed serial number of your KDC101 controller
MAX_VELOCITY = Decimal(5)        # 🌀 Spin speed in degrees/sec (for PRM1Z8)
ACCELERATION = Decimal(2)        # 🌀 Acceleration in degrees/sec²

# ==== Internal control ====
_servo_thread = None
_servo_ready = threading.Event()
_servo_device = None
_thread_lock = threading.Lock()

def _spin_servo_thread():
    global _servo_device

    try:
        print("🔌 Connecting to KDC101...")

        DeviceManagerCLI.BuildDeviceList()
        device = KCubeDCServo.CreateKCubeDCServo(SERIAL_NO)
        device.Connect(SERIAL_NO)

        if not device.IsSettingsInitialized():
            print("⏳ Waiting for settings to initialize...")
            device.WaitForSettingsInitialized(5000)

        print("🔧 Loading motor configuration for PRM1Z8...")
        device.LoadMotorConfiguration(SERIAL_NO)

        device.StartPolling(100)
        time.sleep(1)
        device.EnableDevice()
        time.sleep(0.5)

        vel_params = device.GetVelocityParams()
        vel_params.MaxVelocity = MAX_VELOCITY
        vel_params.Acceleration = ACCELERATION
        device.SetVelocityParams(vel_params)

        device.MoveContinuous(MotorDirection.Forward)
        print("✅ PRM1Z8 is now spinning continuously!")

        _servo_device = device
        _servo_ready.set()

        while True:
            time.sleep(1)

    except Exception as e:
        print(f"❌ Servo thread error: {e}")
        _servo_ready.set()  # prevent blocking forever in case of error

def start_servo_spin():
    """Start the PRM1Z8 rotation stage spinning in a background thread."""
    global _servo_thread

    with _thread_lock:
        if _servo_thread and _servo_thread.is_alive():
            print("⚠️ Servo is already spinning.")
            return

        _servo_ready.clear()
        _servo_thread = threading.Thread(target=_spin_servo_thread, daemon=True)
        _servo_thread.start()

    # Wait until the servo confirms it's spinning
    _servo_ready.wait()
    print("🧵 Servo spin confirmed — continuing main code.")

def stop_servo_spin():
    """Stop the spinning servo gracefully and clean up."""
    global _servo_device

    if _servo_device:
        print("🛑 Stopping PRM1Z8 servo...")
        _servo_device.Stop(0)  # 0 = normal stop
        _servo_device.StopPolling()
        _servo_device.Disconnect()
        _servo_device = None
        print("✅ Servo stopped and disconnected.")
    else:
        print("⚠️ Servo was not started or already stopped.")
