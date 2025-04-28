import yaml
import numpy as np
import cv2
import mediapipe as mp
from math import dist
import subprocess
import samsungctl
from samsungtvws import SamsungTVWS
import time

# TV IP
TV_IP = "10.0.0.191"

#command_path = 'C:\\Leandro\\Atrax Automation LLC\\Entrenamientos\\Python\\IngeLearn\\Projects\\TV control\\platform-tools-latest-windows\\platform-tools\\adb.exe'

#def adb_command(command):
#    try:
#        result = subprocess.run([command_path, 'shell'] + command.split(), capture_output=True, text=True)
#        if result.returncode == 0:
#            print(f"Success: {result.stdout}")
#        else:
#            print(f"Error: {result.stderr}")
#    except Exception as e:
#        print(f"An error occurred: {str(e)}")

config = {
    "name": "My Remote",
    "description": "Samsung TV Remote",
    "id": "",
    "host": "10.0.0.191",
    "port": 55000, # Default port for newer TVs
    "method": "legacy",
    "timeout": 10,
}

def send_key(key):
    try:
        with samsungctl.Remote(config) as remote:
            for i in range(10):
                remote.control(key)
                print(f"Sent key: {key}")
                time.sleep(0.5)
    except Exception as e:
        print(f"Failed to send key {key}: {e}")

def selectpad():
    send_key("KEY_ENTER")
    print("Select pad")

def leftpad():
    send_key("KEY_LEFT")
    print("Left pad")

def rightpad():
    send_key("KEY_RIGHT")
    print("Right pad")

def uppad():
    send_key("KEY_UP")
    print("Up pad")

def downpad():
    send_key("KEY_DOWN")
    print("Down pad")

def volumeup():
    send_key("KEY_VOLUP")
    print("Volume Up")

def volumedown():
    send_key("KEY_VOLDOWN")
    print("Volume Down")

def backKey():
    send_key("KEY_RETURN")
    print("Back key")

def homeKey():
    #adb_command("input keyevent 3")
    print("Home key")

def powerKey():
    #adb_command("input keyevent 26")
    print("Power Key")

# Hands detection
mpHands = mp.solutions.hands
hands = mpHands.Hands(static_image_mode=False, max_num_hands = 2, min_detection_confidence=0.7,min_tracking_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

# Identifiers for points in each finger
fingers = {
    #"thumb":[2,4],
    "index":[6,8],
    "middle":[10,12],
    "ring":[14,16],
    "little":[18,20],
}

areas_color = [(0,0,255)]*5
area_buffer = [None]*5
area_status = [False]*5


def coord_x(marker):
    return float(str(results.multi_hand_landmarks[-1].landmark[int(marker)]).split('\n')[0].split(" ")[1])

def coord_y(marker):
    return float(str(results.multi_hand_landmarks[-1].landmark[int(marker)]).split('\n')[1].split(" ")[1])

def fingerDetection():
    if results.multi_hand_landmarks is not None:
        try:
        # Calculate the distance between finger tip and hand palm.
        # and finger middle and hand palm.
        # if finger tip-palm distance < finger middle-palm distance
        # finger is closed
            x_palm = coord_x(0)
            y_palm = coord_y(0)
            closed = []
            for middle,tip in fingers.values():
                x_middle = coord_x(middle)
                y_middle = coord_y(middle)
                x_tip = coord_x(tip)
                y_tip = coord_y(tip)
                distance_middle = dist([x_palm, y_palm], [x_middle, y_middle])
                distance_tip = dist([x_palm, y_palm], [x_tip, y_tip])
                if distance_middle < distance_tip:
                    closed.append(1)
                else:
                    closed.append(0)
            return closed
        except:
            pass

area = 5
fn_yaml = r"C:\Leandro\Atrax Automation LLC\Entrenamientos\Python\IngeLearn\Projects\TV control\areas.yml"
config = {'buffer_4_functions': 0.5,
          'interaction_detection': True,
          'text_overlay': True,
          'hands_identification': True,
          }

# Set capture device 0 for webcam
cap = cv2.VideoCapture(0)

# Read YAML data (polygons for areas)
with open(fn_yaml, 'r') as stream:
    areas_data = yaml.safe_load(stream)
areas_contours = []

while cap.isOpened():
    # Read frame-by-frame
    video_current_position = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 # Current psoition of the video file in seconds
    ret, frame = cap.read()
    if ret == False:
        print("Capture Error")
        break

    

    # Create a clean copy of the fram for finger detection
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    contour_canvas = frame.copy()
    if config['text_overlay']:
        h, w, c = frame.shape
        for ind, area in enumerate(areas_data):
            points = np.array(area['points'])
            #points = np.array([[int(pt[0] * w / 960), int(pt[1] * h / 720)] for pt in area['points']])

            if area_status[ind]:
                color = (0,255,0)
                cv2.fillPoly(contour_canvas, [points], color=color)
            else:
                color = (0,0,255)
                cv2.drawContours(contour_canvas, [points], contourIdx=-1, color=color, thickness=2, lineType=cv2.LINE_8)
    
    if config['hands_identification']:
        # Detection
        results = hands.process(frame_rgb)

        # Draw detection
        if results.multi_hand_landmarks:
            for handLms in results.multi_hand_landmarks:
                for id, lm in enumerate(handLms.landmark):
                    h, w, c = frame.shape
                    cx, cy = int(lm.x*w), int(lm.y*h)
                    d = [8,12,16,20]
                    detection = fingerDetection()
                    # Green tip for finger extended, red for finger closed
                    if id in d:
                        if detection[d.index(id)] == 1:
                            cv2.circle(frame, (cx,cy), 10,(0,255,0), -1)
                        else:
                            cv2.circle(frame, (cx,cy), 10,(0,0,255), -1)
                    if id == d[0] and detection[d.index(id)] == 1:
                        for ind, area in enumerate(areas_data):
                            points = np.array(area['points'])
                            #points = np.array([[int(pt[0] * w / 960), int(pt[1] * h / 720)] for pt in area['points']])
                            min_x = min(points[:,0])
                            max_x = max(points[:,0])
                            min_y = min(points[:,1])
                            max_y = max(points[:,1])
                            curr_status = min_x <= cx <= max_x and min_y <= cy <= max_y

                            if curr_status != area_status[ind] and area_buffer[ind]==None:
                                area_buffer[ind] = video_current_position

                            elif curr_status != area_status[ind] and area_buffer[ind]!=None:
                                if video_current_position - area_buffer[ind] > config['buffer_4_functions']:
                                    area_status[ind] = curr_status
                                    area_buffer[ind] = None

                            #print(f"Area: {ind}, min x: {min_x}, max x: {max_x}, min y: {min_y}, max y: {max_y}, cx: {cx}, cy: {cy}")
                            print(f"Height: {h}, Width: {w}")
                    elif id==d[1] and detection[d.index(id)] == 1:
                        backKey()
                    elif id==d[3] and detection[d.index(id)] == 1:
                        homeKey()
                    elif id==d[0]:
                        area_status = [None]*5
                mpDraw.draw_landmarks(frame, handLms, mpHands.HAND_CONNECTIONS)
                

    if config['interaction_detection']:
        for ind,status in enumerate(area_status):
            if status:
                if ind == 1:
                    uppad()
                elif ind == 2:
                    leftpad()
                elif ind == 3:
                    downpad()
                elif ind == 4:
                    selectpad()
                elif ind == 0:
                    rightpad()
                

    # Display video
    frame = cv2.addWeighted(frame, 0.8, contour_canvas, 0.2, 0)
    mirrored_frame = cv2.flip(frame, 1)
    imS = cv2.resize(mirrored_frame, (960,720))
    cv2.imshow('Parking detection', imS)
    cv2.waitKey(40)
    k = cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()