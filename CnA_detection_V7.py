# backend
import cv2
import time
import numpy as np
import io
import os
from datetime import datetime
import pytz

from flask import Flask, Response, render_template, jsonify, send_file
from sklearn.cluster import DBSCAN
from pymongo import MongoClient
from gridfs import GridFS
from ultralytics import YOLO
from bson import ObjectId
from dotenv import load_dotenv

# Optional Windows beep
try:
    import winsound
    HAS_WINSOUND = True
except:
    HAS_WINSOUND = False

# Optional Twilio
try:
    from twilio.rest import Client
    HAS_TWILIO = True
except:
    HAS_TWILIO = False

load_dotenv()

# ==================================================
# CONFIG
# ==================================================
MONGO_URI = os.getenv("MONGO_URI")
CAMERA_ID = "CAM01"

# VIDEO_PATH = "test_video.mp4"
STREAM_URL = "http://172.20.10.2:8000/video"

IST = pytz.timezone("Asia/Kolkata")

EPS_DISTANCE = 80
MIN_CLUSTER_SIZE = 3
CROWD_TIME_THRESHOLD = 2

SMS_COOLDOWN = 30
EVENT_COOLDOWN = 15

# ==================================================
# APP
# ==================================================
app = Flask(__name__)

# ==================================================
# DATABASE
# ==================================================
DB_CONNECTED = False

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    client.server_info()

    db = client["smart_city"]
    crowd_collection = db["crowd_events"]
    accident_collection = db["accident_events"]
    fs = GridFS(db)

    DB_CONNECTED = True
    print("MongoDB Connected")

except:
    print("MongoDB Not Connected")

# ==================================================
# MODELS
# ==================================================
model = YOLO("yolov8n.pt")
accident_model = YOLO("best.pt")

# ==================================================
# VIDEO
# ==================================================

cap = cv2.VideoCapture(STREAM_URL)

# cap = cv2.VideoCapture(VIDEO_PATH)

# ==================================================
# GLOBALS
# ==================================================
crowd_start_time = None
crowd_logged = False

accident_start_time = None
accident_logged = False

last_sound_time = 0
last_sms_time = 0

LAST_EVENT_TIME = {
    "crowd": 0,
    "accident": 0
}

last_crowd_signature = None
last_accident_signature = None

# ==================================================
# HELPERS
# ==================================================
def beep(freq=1500, dur=500):
    if HAS_WINSOUND:
        winsound.Beep(freq, dur)

def send_sms_alert(message):
    global last_sms_time

    if not HAS_TWILIO:
        return

    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        client = Client(account_sid, auth_token)

        client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_PHONE"),
            to=os.getenv("USER_PHONE")
        )

        last_sms_time = time.time()

    except Exception as e:
        print("SMS Error:", e)

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter = max(0, xB - xA) * max(0, yB - yA)

    areaA = (boxA[2]-boxA[0]) * (boxA[3]-boxA[1])
    areaB = (boxB[2]-boxB[0]) * (boxB[3]-boxB[1])

    return inter / float(areaA + areaB - inter + 1e-6)

def get_crowd_severity(cluster_size, person_count):
    if cluster_size >= 10 or person_count >= 25:
        return "CRITICAL"
    elif cluster_size >= 7:
        return "HIGH"
    elif cluster_size >= 4:
        return "MEDIUM"
    return "LOW"

def get_accident_severity(vehicle_boxes, person_boxes, animal_boxes):

    for v in vehicle_boxes:
        for p in person_boxes:
            if calculate_iou(v, p) > 0.2:
                return "HIGH"

    for v in vehicle_boxes:
        for a in animal_boxes:
            if calculate_iou(v, a) > 0.2:
                return "HIGH"

    if len(vehicle_boxes) >= 3:
        return "HIGH"

    if len(vehicle_boxes) == 2:
        return "MEDIUM"

    return "LOW"

# ==================================================
# FRAME GENERATOR
# ==================================================
def generate_frames():
    global crowd_start_time, crowd_logged
    global accident_start_time, accident_logged
    global last_sound_time
    global last_crowd_signature, last_accident_signature

    while True:
        success, frame = cap.read()

        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        now = time.time()

        results = model(frame, verbose=False)

        person_boxes = []
        vehicle_boxes = []
        animal_boxes = []

        # ---------------- Object Detection ----------------
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])

            if conf < 0.5:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if label == "person":
                person_boxes.append([x1, y1, x2, y2])
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,255), 2)

            elif label in ["car","bus","truck","motorbike","bicycle"]:
                vehicle_boxes.append([x1,y1,x2,y2])
                cv2.rectangle(frame, (x1,y1), (x2,y2), (255,0,0), 2)

            elif label in ["dog","cow","horse","sheep"]:
                animal_boxes.append([x1,y1,x2,y2])
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)

        person_count = len(person_boxes)

        cv2.putText(frame, f"Persons: {person_count}",
                    (20,40), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0,255,255), 2)

        # ==================================================
        # CROWD DETECTION
        # ==================================================
        if person_count > 0:

            centroids = []

            for box in person_boxes:
                x1,y1,x2,y2 = box
                cx = (x1+x2)//2
                cy = (y1+y2)//2
                centroids.append([cx,cy])

            centroids = np.array(centroids)

            clustering = DBSCAN(
                eps=EPS_DISTANCE,
                min_samples=3
            ).fit(centroids)

            labels = clustering.labels_
            unique = set(labels)

            crowd_detected = False
            largest_cluster = 0

            for lb in unique:
                if lb == -1:
                    continue

                pts = centroids[labels == lb]
                size = len(pts)

                largest_cluster = max(largest_cluster, size)

                x_min = int(min(pts[:,0]))
                y_min = int(min(pts[:,1]))
                x_max = int(max(pts[:,0]))
                y_max = int(max(pts[:,1]))

                cv2.rectangle(frame,
                              (x_min,y_min),
                              (x_max,y_max),
                              (0,0,255),2)

                if size >= MIN_CLUSTER_SIZE:
                    crowd_detected = True

            if crowd_detected:
                if crowd_start_time is None:
                    crowd_start_time = now

                if now - crowd_start_time >= CROWD_TIME_THRESHOLD:

                    cv2.putText(frame, "CROWD ALERT!",
                                (20,90),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0,0,255), 3)

                    if now - last_sound_time > 4:
                        beep()
                        last_sound_time = now

                    signature = (person_count, largest_cluster)

                    if (not crowd_logged and
                        now - LAST_EVENT_TIME["crowd"] > EVENT_COOLDOWN and
                        signature != last_crowd_signature):

                        severity = get_crowd_severity(
                            largest_cluster,
                            person_count
                        )

                        if DB_CONNECTED:
                            _, buffer = cv2.imencode(".jpg", frame)

                            file_id = fs.put(
                                buffer.tobytes(),
                                filename="crowd.jpg"
                            )

                            crowd_collection.insert_one({
                                "camera_id": CAMERA_ID,
                                "event_type": "crowd",
                                "person_count": person_count,
                                "cluster_size": largest_cluster,
                                "severity": severity,
                                "image_file_id": file_id,
                                "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                            })

                        if severity in ["HIGH","CRITICAL"]:
                            if now - last_sms_time > SMS_COOLDOWN:
                                send_sms_alert(
                                    f"CROWD ALERT\nCamera:{CAMERA_ID}\nCount:{person_count}\nSeverity:{severity}"
                                )

                        LAST_EVENT_TIME["crowd"] = now
                        last_crowd_signature = signature
                        crowd_logged = True

            else:
                crowd_start_time = None
                crowd_logged = False

        # ==================================================
        # ACCIDENT DETECTION
        # ==================================================
        accident_detected = False
        accident_type = "Accident"

        if len(vehicle_boxes) >= 2:

            results2 = accident_model(frame, verbose=False)

            for box in results2[0].boxes:

                conf = float(box.conf[0])

                if conf < 0.6:
                    continue

                x1,y1,x2,y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame,
                              (x1,y1),(x2,y2),
                              (0,0,255),3)

                accident_detected = True

                if len(vehicle_boxes) >= 2:
                    accident_type = "Vehicle-Vehicle"

                for v in vehicle_boxes:
                    for p in person_boxes:
                        if calculate_iou(v,p) > 0.2:
                            accident_type = "Vehicle-Person"

                for v in vehicle_boxes:
                    for a in animal_boxes:
                        if calculate_iou(v,a) > 0.2:
                            accident_type = "Vehicle-Animal"

        if accident_detected:

            if accident_start_time is None:
                accident_start_time = now

            if now - accident_start_time >= 0.5:

                cv2.putText(frame, "ACCIDENT DETECTED!",
                            (20,140),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,(0,0,255),3)

                if now - last_sound_time > 4:
                    beep(2000,700)
                    last_sound_time = now

                signature = (accident_type, len(vehicle_boxes))

                if (not accident_logged and
                    now - LAST_EVENT_TIME["accident"] > EVENT_COOLDOWN and
                    signature != last_accident_signature):

                    severity = get_accident_severity(
                        vehicle_boxes,
                        person_boxes,
                        animal_boxes
                    )

                    if DB_CONNECTED:
                        _, buffer = cv2.imencode(".jpg", frame)

                        file_id = fs.put(
                            buffer.tobytes(),
                            filename="accident.jpg"
                        )

                        accident_collection.insert_one({
                            "camera_id": CAMERA_ID,
                            "event_type": "accident",
                            "accident_type": accident_type,
                            "severity": severity,
                            "image_file_id": file_id,
                            "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                        })

                    if severity in ["MEDIUM","HIGH"]:
                        if now - last_sms_time > SMS_COOLDOWN:
                            send_sms_alert(
                                f"ACCIDENT ALERT\nType:{accident_type}\nSeverity:{severity}"
                            )

                    LAST_EVENT_TIME["accident"] = now
                    last_accident_signature = signature
                    accident_logged = True

        else:
            accident_start_time = None
            accident_logged = False

        # ==================================================
        # STREAM
        # ==================================================
        ret, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               frame_bytes + b"\r\n")

# ==================================================
# ROUTES
# ==================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/logs")
def logs():
    if not DB_CONNECTED:
        return jsonify({"crowd": [], "accident": []})

    crowd_events = list(crowd_collection.find().sort("_id",-1).limit(50))
    accident_events = list(accident_collection.find().sort("_id",-1).limit(50))

    for e in crowd_events:
        e["_id"] = str(e["_id"])
        e["image_file_id"] = str(e["image_file_id"])

    for e in accident_events:
        e["_id"] = str(e["_id"])
        e["image_file_id"] = str(e["image_file_id"])

    return jsonify({
        "crowd": crowd_events,
        "accident": accident_events
    })

@app.route("/image/<file_id>")
def image(file_id):
    if not DB_CONNECTED:
        return "DB Not Connected"

    img = fs.get(ObjectId(file_id))

    return send_file(
        io.BytesIO(img.read()),
        mimetype="image/jpeg"
    )

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)