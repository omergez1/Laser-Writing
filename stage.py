import clr
import sys
import time
import math
import serial


from System import Convert

def _netdec_to_float(x):
    try:
        return float(str(x))   # robust across pythonnet versions
    except Exception:
        return Convert.ToDouble(x)



PORT = "COM5"   # adjust for your system
BAUD = 19200    # please check actual boudrate

def send_command(ser, cmd):
    """
    Send a command string to the laser and print the response.
    """
    ser.write((cmd + "\r\n").encode("ascii"))
    resp = ser.read_until(b"\n").decode(errors="ignore").strip()
    print(f"➡ Sent: {cmd} | ⬅ Response: {resp if resp else 'No response'}")
    return resp

# Add Kinesis DLLs path
sys.path.append(r"C:\Program Files\Thorlabs\Kinesis")

# Load Kinesis DLLs
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.GenericMotorCLI")
clr.AddReference("Thorlabs.MotionControl.Benchtop.StepperMotorCLI")

from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.Benchtop.StepperMotorCLI import BenchtopStepperMotor
from Thorlabs.MotionControl.GenericMotorCLI import MotorDirection
from System.Threading import Thread
from System import Decimal



class WaveguideWriter:
    MIN_POSITION = 0.0
    MAX_POSITION = 8000.0
    SAFETY_MARGIN = 0.0

    def __init__(self, serial_no="70506134"):
        self.serial_no = serial_no
        self.device = None
        self.motors = {}
        self.connected = False

    def um_to_controller(self, um):  # µm -> mm
        return um / 1000.0

    def controller_to_um(self, mm):  # mm -> µm
        return mm * 1000.0

    def connect(self):
        try:
            DeviceManagerCLI.BuildDeviceList()
            time.sleep(1)
            self.device = BenchtopStepperMotor.CreateBenchtopStepperMotor(self.serial_no)
            if self.device is None:
                raise Exception("Failed to create device")
            self.device.Connect(self.serial_no)
            Thread.Sleep(3000)

            # Map channels to axes
            for channel, axis in [(1, 'X'), (2, 'Y'), (3, 'Z')]:
                motor = self.device.GetChannel(channel)
                if motor:
                    if not motor.IsSettingsInitialized():
                        motor.WaitForSettingsInitialized(10000)
                    motor.StartPolling(250)
                    Thread.Sleep(500)
                    motor.EnableDevice()
                    Thread.Sleep(1000)
                    try:
                        motor.LoadMotorConfiguration(motor.DeviceID)
                    except:
                        pass
                    self.motors[axis] = motor

            self.connected = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def home_all(self):
        for axis, motor in self.motors.items():
            try:
                print(f"Homing {axis}...")
                motor.Home(60000)
                while motor.IsDeviceBusy:
                    Thread.Sleep(250)
            except Exception as e:
                print(f"Error homing {axis}: {e}")

    def get_position(self, axis):
        try:
            return self.controller_to_um(float(self.motors[axis].Position.ToString()))
        except:
            return 0.0

    def get_all_positions(self):
        return {axis: self.get_position(axis) for axis in self.motors}

    def clamp_position(self, axis, position_um):
        min_safe = self.MIN_POSITION + self.SAFETY_MARGIN
        max_safe = self.MAX_POSITION - self.SAFETY_MARGIN
        if position_um < min_safe:
            print(f"{axis}: Clamping {position_um} → {min_safe} μm")
            return min_safe
        elif position_um > max_safe:
            print(f"{axis}: Clamping {position_um} → {max_safe} μm")
            return max_safe
        return position_um

    # -------------------- Velocity/Accel helpers --------------------

    def set_motion_profile(self, axis, velocity_um_s, accel_um_s2):
        """Set target velocity (µm/s) and acceleration (µm/s²) on an axis."""
        if axis not in self.motors:
            print(f"{axis} not available")
            return False
        motor = self.motors[axis]
        try:
            vp = motor.GetVelocityParams()
            vp.MaxVelocity = Decimal(self.um_to_controller(velocity_um_s))  # mm/s
            vp.Acceleration = Decimal(self.um_to_controller(accel_um_s2))  # mm/s^2
            motor.SetVelocityParams(vp)
            return True
        except Exception as e:
            print(f"Failed to set motion profile on {axis}: {e}")
            return False

    def print_motion_profile(self, axis):
        if axis not in self.motors:
            print(f"{axis} not available")
            return
        try:
            vp = self.motors[axis].GetVelocityParams()
            v_um_s = self.controller_to_um(_netdec_to_float(vp.MaxVelocity))
            a_um_s2 = self.controller_to_um(_netdec_to_float(vp.Acceleration))
            print(f"{axis} profile -> Vmax: {v_um_s:.3f} µm/s, Accel: {a_um_s2:.3f} µm/s²")
        except Exception as e:
            print(f"Failed to read motion profile on {axis}: {e}")

    # -------------------- Move --------------------

    def move_to_position_absolute(self, axis, target_um, tolerance_um=0.5, timeout=120):
        if axis not in self.motors:
            print(f"{axis} not available")
            return False

        target_um = self.clamp_position(axis, target_um)
        target_mm = Decimal(self.um_to_controller(target_um))

        start_pos = self.get_position(axis)
        if abs(start_pos - target_um) < tolerance_um:
            print(f"{axis} already at target")
            return True

        motor = self.motors[axis]
        try:
            motor.MoveTo(target_mm, 30000)  # command timeout (ms), motion monitored below
            start_time = time.time()
            while motor.IsDeviceBusy and (time.time() - start_time) < timeout:
                pos = self.get_position(axis)
                print(f"{axis} moving: {pos:.2f}μm")
                Thread.Sleep(100)

            final_pos = self.get_position(axis)
            error = abs(final_pos - target_um)
            if error <= tolerance_um:
                print(f"{axis} reached target: {final_pos:.2f}μm")
                return True
            else:
                print(f"{axis} error: {error:.2f}μm")
                return error < 2 * tolerance_um

        except Exception as e:
            print(f"Move error on {axis}: {e}")
            return False

    # -------------------- Waveguide --------------------

    def write_waveguide(
        self,
        length,          # µm
        width,           # µm
        step_size,       # µm
        repeat,          # even int
        speed,           # µm/s (scan velocity on length axis)
        length_axis,     # 'X' or 'Y'
        offset,          # (dx, dy, dz) µm
        ser,
        scan_accel=50000, # µm/s² default accel
        return_home=True
    ):

        if repeat <= 0 or repeat % 2 != 0:
            print("Repeat must be even and > 0")
            return False

        # Set scan velocity/accel on the length axis
        if not self.set_motion_profile(length_axis, velocity_um_s=speed, accel_um_s2=scan_accel):
            print("⚠ Could not set motion profile; proceeding with current device settings.")
        self.print_motion_profile(length_axis)

        start_pos = self.get_all_positions()
        start = {
            'X': start_pos['X'] + offset[0],
            'Y': start_pos['Y'] + offset[1],
            'Z': start_pos['Z'] + offset[2],
        }

        num_lines_y = int(width / step_size) + 1
        num_lines_z = int(width / step_size) + 1
        total_lines = num_lines_y * num_lines_z

        print(f"\nWriting waveguide pattern: {total_lines} lines")

        for line_num in range(total_lines):
            z_idx = line_num // num_lines_y
            y_idx = line_num % num_lines_y

            pos = {
                'X': start['X'],
                'Y': start['Y'] + y_idx * step_size,
                'Z': start['Z'] + z_idx * step_size
            }

            if length_axis == 'Y':
                pos['X'] = start['X'] + y_idx * step_size
                pos['Y'] = start['Y']

            # Go to the line start (3-axis positioning)
            for axis in ['X', 'Y', 'Z']:
                if not self.move_to_position_absolute(axis, pos[axis], timeout=120):
                    print(f"Aborted: failed to reach start pos on {axis}")
                    return False

            # Serpentine repeats along the length axis
            for r in range(repeat):
                # Laser ON at the start of each straight scan
                if ser is not None:
                    try:
                        send_command(ser, "S=1")
                        time.sleep(0.5)

                    except Exception as e:
                        print(f"⚠ Shutter open failed: {e}")

                # Forward on even r, return on odd r
                target = pos[length_axis] + length if r % 2 == 0 else pos[length_axis]
                ok = self.move_to_position_absolute(length_axis, target, timeout=120)

                # Laser OFF when line finished (even if move failed we try to close)
                if ser is not None:
                    try:
                        send_command(ser, "S=0")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"⚠ Shutter close failed: {e}")

                if not ok:
                    print("Aborted: scan move failed")
                    return False

        if return_home:
            print("Returning to start")
            for axis in ['X', 'Y', 'Z']:
                self.move_to_position_absolute(axis, start_pos[axis], timeout=120)

        print("Waveguide writing complete")
        return True

    def disconnect(self):
        if self.device:
            for m in self.motors.values():
                try:
                    m.StopPolling()
                    m.DisableDevice()
                except:
                    pass
            try:
                self.device.Disconnect()
            except:
                pass
            print("Disconnected")

