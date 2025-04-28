from samsungtvws import SamsungTVWS

TV_IP = "10.0.0.191"

try:
    tv = SamsungTVWS(host=TV_IP, port=8001)
    tv.open()
    print("Paring successful")

    tv.send_key("KEY_VOLUMEUP")
    print("Volume up command sent successfully!")
except Exception as e:
    print(f"Failed to connect or send key: {e}")