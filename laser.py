import serial
import time






def send_command(ser, cmd):
    """
    Send a command string to the laser and print the response.
    No retries, no infinite loop.
    """
    ser.write((cmd + "\r\n").encode("ascii"))
    resp = ser.read_until(b"\n").decode(errors="ignore").strip()
    print(f"➡ Sent: {cmd} | ⬅ Response: {resp if resp else 'No response'}")
    return resp

