import cv2
import time
import numpy as np
import winsound
from datetime import datetime
import pytz
from flask import Flask, Response, render_template_string, jsonify, send_file
from sklearn.cluster import DBSCAN
from pymongo import MongoClient
from gridfs import GridFS
from ultralytics import YOLO
from bson import ObjectId
from twilio.rest import Client
from dotenv import load_dotenv
import os

load_dotenv()
import io

# =============================
# CONFIGURATION
# =============================

MONGO_URI = os.getenv("MONGO_URI")
CAMERA_ID = "CAM01"
# STREAM_URL = "http://172.20.10.4:5000/video"

VIDEO_PATH = "test_video.mp4"

# DBSCAN PARAMETERS 
EPS_DISTANCE = 80          # pixel distance threshold
MIN_CLUSTER_SIZE = 3       # people required in cluster
CROWD_TIME_THRESHOLD = 2   # seconds
last_sms_time = 0


IST = pytz.timezone('Asia/Kolkata')

# =============================
# ANTI-SPAM + DUPLICATE CONTROL
# =============================

SMS_COOLDOWN = 30
EVENT_COOLDOWN = 15

LAST_EVENT_TIME = {
    "crowd": 0,
    "accident": 0
}

last_crowd_signature = None
last_accident_signature = None

# =============================
# INITIALIZE
# =============================

app = Flask(__name__)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    client.server_info()

    db = client["smart_city"]
    crowd_collection = db["crowd_events"]
    accident_collection = db["accident_events"]
    fs = GridFS(db)

    DB_CONNECTED = True
    print("✅ MongoDB Connected")

except:
    print("⚠️ MongoDB NOT connected. Running without DB.")
    DB_CONNECTED = False

model = YOLO("yolov8n.pt")        # general detection
accident_model = YOLO("best.pt")  # accident model

print(accident_model.names)
# cap = cv2.VideoCapture(STREAM_URL)
cap = cv2.VideoCapture(VIDEO_PATH)

crowd_start_time = None
crowd_logged = False
accident_start_time = None
accident_logged = False
last_sound_time = 0


def check_overlap(a, b):
    return (a[0] < b[2] and a[2] > b[0] and
            a[1] < b[3] and a[3] > b[1])


def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)

    boxAArea = (boxA[2]-boxA[0]) * (boxA[3]-boxA[1])
    boxBArea = (boxB[2]-boxB[0]) * (boxB[3]-boxB[1])

    return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

def send_sms_alert(message):

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_=os.getenv("TWILIO_PHONE"),
        to=os.getenv("USER_PHONE")
    )
def get_crowd_severity(cluster_size, person_count):

    if cluster_size >= 10 or person_count >= 25:
        return "CRITICAL"
    elif cluster_size >= 7:
        return "HIGH"
    elif cluster_size >= 4:
        return "MEDIUM"
    else:
        return "LOW"


def get_accident_severity(vehicle_boxes, person_boxes, animal_boxes):

    #Vehicle vs Person → HIGH
    for v in vehicle_boxes:
        for p in person_boxes:
            if calculate_iou(v, p) > 0.2:
                return "HIGH"

    #Vehicle vs Animal → HIGH
    for v in vehicle_boxes:
        for a in animal_boxes:
            if calculate_iou(v, a) > 0.2:
                return "HIGH"

    #Multiple vehicles (3 or more) → HIGH
    if len(vehicle_boxes) >= 3:
        return "HIGH"

    #Two vehicles → MEDIUM
    if len(vehicle_boxes) == 2:
        return "MEDIUM"

    #Default → LOW
    return "LOW"

def generate_frames():
    global crowd_start_time, crowd_logged
    global accident_start_time, accident_logged
    global last_sound_time
    global last_sms_time
    global last_crowd_signature, last_accident_signature

    while True:
        success, frame = cap.read()
        # if not success:
        #     break

        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # restart video
            continue

        results = model(frame, verbose=False)

        person_boxes = []
        vehicle_boxes = []
        animal_boxes = []

        # =============================
        # YOLO OBJECT DETECTION
        # =============================

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])

            if conf < 0.5:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if label == "person":
                person_boxes.append([x1, y1, x2, y2])
                cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,255),2)

            elif label in ["car","bus","truck","motorbike","bicycle"]:
                vehicle_boxes.append([x1,y1,x2,y2])
                cv2.rectangle(frame,(x1,y1),(x2,y2),(255,0,0),2)

            elif label in ["dog","cow","horse","sheep"]:
                animal_boxes.append([x1,y1,x2,y2])
                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)

        person_count = len(person_boxes)

        cv2.rectangle(frame,(10,10),(260,70),(0,0,0),-1)
        cv2.putText(frame,f"Persons: {person_count}",
                    (20,50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,(0,255,255),2)

        now = time.time()

        # =============================
        # CROWD DETECTION (DBSCAN)
        # =============================

        if person_count > 0:

            centroids = []
            for box in person_boxes:
                x1, y1, x2, y2 = box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                centroids.append([cx, cy])

                cv2.circle(frame, (cx, cy), 4, (255, 0, 255), -1)

            centroids = np.array(centroids)

            clustering = DBSCAN(eps=EPS_DISTANCE,
                                min_samples=3).fit(centroids)

            labels = clustering.labels_
            unique_labels = set(labels)

            crowd_detected = False
            largest_cluster = 0

            for label in unique_labels:

                if label == -1:
                    continue

                cluster_points = centroids[labels == label]
                cluster_size = len(cluster_points)

                if cluster_size > largest_cluster:
                    largest_cluster = cluster_size

                x_min = int(min(cluster_points[:,0]))
                y_min = int(min(cluster_points[:,1]))
                x_max = int(max(cluster_points[:,0]))
                y_max = int(max(cluster_points[:,1]))

                cv2.rectangle(frame,
                              (x_min,y_min),
                              (x_max,y_max),
                              (0,0,255),2)

                if cluster_size >= MIN_CLUSTER_SIZE:
                    crowd_detected = True

            if crowd_detected:

                if crowd_start_time is None:
                    crowd_start_time = now

                if now - crowd_start_time >= CROWD_TIME_THRESHOLD:

                    cv2.putText(frame,"CROWD ALERT!",
                                (20,110),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1,(0,0,255),3)

                    if now - last_sound_time > 4:
                        winsound.Beep(1500,500)
                        last_sound_time = now

                    current_signature = (person_count, largest_cluster)

                    if (not crowd_logged and
                        (time.time() - LAST_EVENT_TIME["crowd"] > EVENT_COOLDOWN) and
                        current_signature != last_crowd_signature):
                        severity = get_crowd_severity(largest_cluster, person_count)
                        if DB_CONNECTED:
                            _, buffer = cv2.imencode(".jpg", frame)

                            file_id = fs.put(
                                buffer.tobytes(),
                                filename="crowd_dbscan.jpg",
                                camera_id=CAMERA_ID,
                                timestamp=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                            )

                            

                            crowd_collection.insert_one({
                                "camera_id": CAMERA_ID,
                                "event_type": "crowd",
                                "person_count": person_count,
                                "cluster_size": largest_cluster,
                                "severity": severity,   # ✅ ADDED
                                "image_file_id": file_id,
                                "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                            })
                        if severity in ["HIGH", "CRITICAL"]:
                            if time.time() - last_sms_time > SMS_COOLDOWN:
                                send_sms_alert(f"""
                                CROWD ALERT
                                Camera: {CAMERA_ID}
                                Count: {person_count}
                                Cluster: {largest_cluster}
                                Severity: {severity}
                                """)
                                last_sms_time = time.time()
                                    
                        LAST_EVENT_TIME["crowd"] = time.time()
                        last_crowd_signature = current_signature            
                        crowd_logged = True
            else:
                crowd_start_time = None
                crowd_logged = False
        else:
            crowd_start_time = None
            crowd_logged = False

        
        # =============================
        # ACCIDENT DETECTION (MODEL BASED)
        # =============================

        accident_detected = False
        accident_label = ""

        # OPTIONAL OPTIMIZATION:
        # Run accident model only if vehicles present
        if len(vehicle_boxes) >= 2:

            accident_results = accident_model(frame, verbose=False)

            for box in accident_results[0].boxes:

                cls_id = int(box.cls[0])
                label = accident_model.names[cls_id]
                confidence = float(box.conf[0])

                if confidence > 0.6:

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Draw bounding box
                    cv2.rectangle(frame,
                                (x1, y1),
                                (x2, y2),
                                (0, 0, 255), 3)

                    # Label
                    cv2.putText(frame,
                                f"{label} {confidence:.2f}",
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (0, 0, 255),
                                2)

                    accident_detected = True
                    # accident_label = label
                    # Default
                    accident_type = "Accident"

                    # Vehicle vs Vehicle
                    if len(vehicle_boxes) >= 2:
                        accident_type = "Vehicle-Vehicle"

                    # Vehicle vs Person
                    for v in vehicle_boxes:
                        for p in person_boxes:
                            if calculate_iou(v, p) > 0.2:
                                accident_type = "Vehicle-Person"

                    # Vehicle vs Animal
                    for v in vehicle_boxes:
                        for a in animal_boxes:
                            if calculate_iou(v, a) > 0.2:
                                accident_type = "Vehicle-Animal"


        # =============================
        # ACCIDENT CONFIRMATION + LOGGING
        # =============================

        if accident_detected:

            if accident_start_time is None:
                accident_start_time = now

            if now - accident_start_time >= 0.5:

                cv2.putText(frame,
                            "ACCIDENT DETECTED!",
                            (20,160),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0,0,255),
                            3)

                if now - last_sound_time > 4:
                    winsound.Beep(2000,700)
                    last_sound_time = now

                current_signature = (accident_type, len(vehicle_boxes))

                if (not accident_logged and
                    (time.time() - LAST_EVENT_TIME["accident"] > EVENT_COOLDOWN) and
                    current_signature != last_accident_signature):
                    severity = get_accident_severity(vehicle_boxes, person_boxes, animal_boxes)

                    if DB_CONNECTED:
                        _, buffer = cv2.imencode(".jpg", frame)

                        file_id = fs.put(
                            buffer.tobytes(),
                            filename="accident.jpg",
                            camera_id=CAMERA_ID,
                            timestamp=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                        )

                        

                        accident_collection.insert_one({
                            "camera_id": CAMERA_ID,
                            "event_type": "accident",
                            "accident_type": accident_type,
                            "severity": severity,   # ✅ ADDED
                            "image_file_id": file_id,
                            "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
                        })
                    if severity in ["HIGH", "MEDIUM"]:
                        if time.time() - last_sms_time > SMS_COOLDOWN:
                            send_sms_alert(f"""
                            ACCIDENT ALERT
                            Camera: {CAMERA_ID}
                            Type: {accident_type}
                            Severity: {severity}
                            Time: {datetime.now(IST).strftime("%H:%M:%S")}
                            """)
                            last_sms_time = time.time()
                    LAST_EVENT_TIME["accident"] = time.time()
                    last_accident_signature = current_signature        
                    accident_logged = True

        else:
            accident_start_time = None
            accident_logged = False
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame_bytes + b'\r\n')
    

# =============================
# ROUTES
# =============================

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Crowd and Accident Monitoring</title>

<style>

body {
    font-family: 'Segoe UI', sans-serif;
    background: #0f172a;
    color: white;
    margin: 0;
    padding: 0;
}

/* HEADER */
.header {
    background: #020617;
    padding: 15px;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    border-bottom: 2px solid #1e293b;
}

/* MAIN GRID */
.container {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    padding: 20px;
}

/* VIDEO CARD */
.video-card {
    background: #1e293b;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
}

/* LOG CARD */
.card {
    background: #1e293b;
    padding: 15px;
    border-radius: 12px;
    height: 400px;
    overflow-y: auto;
}

/* TABLE */
table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background: #334155;
    padding: 10px;
}

td {
    padding: 8px;
    border-bottom: 1px solid #475569;
}

/* BADGES */
.badge {
    padding: 5px 10px;
    border-radius: 8px;
    font-weight: bold;
}

.low { background: green; }
.medium { background: blue; }
.high { background: orange; }
.critical { background: red; }

/* BUTTON */
button {
    margin: 10px;
    padding: 10px 20px;
    border: none;
    background: #3b82f6;
    color: white;
    border-radius: 8px;
    cursor: pointer;
}

button:hover {
    background: #2563eb;
}

</style>
</head>

<body>

<div class="header">
🚦 Crowd and Accident Monitoring
</div>

<div class="container">

    <!-- VIDEO -->
    <div class="video-card">
        <h2>Live Camera Feed</h2>
        <img src="/video_feed" width="100%" style="border-radius:10px;">
    </div>

    <!-- BUTTON -->
    <div>
        <button onclick="toggleLogs()">Show / Hide Logs</button>

        <div id="logs" style="display:none;"></div>
    </div>

</div>

<script>

let logsVisible = false;
let intervalId = null;

function toggleLogs(){
    const logsDiv = document.getElementById("logs");

    logsVisible = !logsVisible;

    if(logsVisible){
        logsDiv.style.display = "block";
        loadLogs();
        intervalId = setInterval(loadLogs, 3000);
    } else {
        logsDiv.style.display = "none";
        clearInterval(intervalId);
    }
}

function getBadgeClass(severity){
    return severity.toLowerCase();
}

function loadLogs(){
    fetch('/logs')
    .then(res => res.json())
    .then(data => {

        let crowdHtml = `
        <div class="card">
        <h3>👥 Crowd Events</h3>
        <table>
        <tr>
            <th>Camera</th>
            <th>Count</th>
            <th>Cluster</th>
            <th>Severity</th>
            <th>Time</th>
            <th>Image</th>
        </tr>
        `;

        data.crowd.slice(0,10).forEach(e => {
            crowdHtml += `
            <tr>
                <td>${e.camera_id}</td>
                <td>${e.person_count}</td>
                <td>${e.cluster_size}</td>
                <td><span class="badge ${getBadgeClass(e.severity)}">${e.severity}</span></td>
                <td>${e.timestamp}</td>
                <td>
                    <a href="/image/${e.image_file_id}" target="_blank">View</a>
                </td>
            </tr>`;
        });

        crowdHtml += "</table></div>";


        let accidentHtml = `
        <div class="card">
        <h3>🚨 Accident Events</h3>
        <table>
        <tr>
            <th>Camera</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Time</th>
            <th>Image</th>
        </tr>
        `;

        data.accident.slice(0,10).forEach(e => {
            accidentHtml += `
            <tr>
                <td>${e.camera_id}</td>
                <td>${e.accident_type}</td>
                <td><span class="badge ${getBadgeClass(e.severity)}">${e.severity}</span></td>
                <td>${e.timestamp}</td>
                <td>
                    <a href="/image/${e.image_file_id}" target="_blank">View</a>
                </td>
            </tr>`;
        });

        accidentHtml += "</table></div>";

        document.getElementById("logs").innerHTML = crowdHtml + accidentHtml;
    });
}

</script>

</body>
</html>
""")
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/logs')
def logs():
    if not DB_CONNECTED:
        return jsonify({"crowd": [], "accident": []})
    crowd_events = list(crowd_collection.find().sort("_id", -1).limit(50))
    accident_events = list(accident_collection.find().sort("_id", -1).limit(50))

    for e in crowd_events:
        e["_id"] = str(e["_id"])
        e["image_file_id"] = str(e["image_file_id"])
        e["timestamp"] = str(e["timestamp"])

    for e in accident_events:
        e["_id"] = str(e["_id"])
        e["image_file_id"] = str(e["image_file_id"])
        e["timestamp"] = str(e["timestamp"])

    return jsonify({
        "crowd": crowd_events,
        "accident": accident_events
    })


@app.route('/image/<file_id>')
def get_image(file_id):
    image = fs.get(ObjectId(file_id))
    return send_file(io.BytesIO(image.read()),
                     mimetype='image/jpeg')


if __name__ == "__main__":
    app.run(debug=True)