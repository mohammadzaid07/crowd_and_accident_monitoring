# 🚦 Crowd & Accident Monitoring System

## 📌 Overview

This project presents a **real-time intelligent monitoring system** designed for smart city environments. It automatically detects:

* 👥 **Crowd formation & density**
* 🚨 **Road accidents**

The system performs  **live video analysis** , generates  **alerts** , stores events, and provides a  **dashboard for monitoring and analytics** .

---

## 🎯 Key Features

### 🔹 Real-Time Detection

* Object detection using **YOLO (Ultralytics)**
* Crowd clustering using **DBSCAN**
* Accident detection using a **custom-trained model**

---

### 🔹 Smart Event Analysis

* Crowd size estimation
* Accident classification (Vehicle–Vehicle, Vehicle–Person, etc.)
* Severity levels:
* 🟢 LOW
* 🔵 MEDIUM
* 🟠 HIGH
* 🔴 CRITICAL

---

### 🔹 Live Dashboard

* 📺 Live video stream
* 📋 Event logs (Crowd & Accident)
* 🏷 Severity badges
* 🖼 Screenshot preview for each event

---

### 🔹 Alerts System

* 📲 SMS alerts via **Twilio API**
* Intelligent alert control:
* Cooldown-based filtering
* Duplicate event prevention

---

### 🔹 Database Integration

* ☁ **MongoDB Atlas**
* 🗂 Stores:
* Crowd events
* Accident events
* 🖼 Image storage using **GridFS**

---

### 🔹 Security

* Sensitive credentials managed using **.env file**
* No hardcoded secrets

---

## 🧠 System Workflow

1. 🎥 Capture video input (camera/video file)
2. 🔍 Detect objects using YOLO
3. 👥 Analyze crowd using DBSCAN clustering
4. 🚨 Detect accidents using trained model
5. ⚖ Assign severity level
6. 💾 Store event in MongoDB
7. 📊 Display on dashboard
8. 📲 Send alerts (if required)

---

## 🛠️ Tech Stack

| Category        | Technology            |
| --------------- | --------------------- |
| Language        | Python                |
| Backend         | Flask                 |
| Computer Vision | OpenCV                |
| AI Models       | YOLO (Ultralytics)    |
| Clustering      | DBSCAN                |
| Database        | MongoDB Atlas         |
| Alerts          | Twilio API            |
| Frontend        | HTML, CSS, JavaScript |
| Charts          | Chart.js              |

---

## 📁 Project Structure

<pre class="overflow-visible! px-0!" data-start="2206" data-end="2521"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="w-full overflow-x-hidden overflow-y-auto pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼk ͼy"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>project/</span><br/><span>│</span><br/><span>├── CnA_detection_V6_testing.py   # Main detection system</span><br/><span>├── pi_stream.py                  # Camera stream handling</span><br/><span>├── templates/                   # HTML files</span><br/><span>├── static/                      # CSS/JS assets</span><br/><span>├── requirements.txt</span><br/><span>├── README.md</span><br/><span>├── .env                         # (Not uploaded)</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

<pre class="overflow-visible! px-0!" data-start="2580" data-end="2702"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="w-full overflow-x-hidden overflow-y-auto"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼk ͼy"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span class="ͼs">git</span><span> clone https://github.com/mohammadzaid07/crowd_and_accident_monitoring.git</span><br/><span class="ͼs">cd</span><span> crowd_and_accident_monitoring</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

### 2️⃣ Install Dependencies

<pre class="overflow-visible! px-0!" data-start="2739" data-end="2782"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="w-full overflow-x-hidden overflow-y-auto"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼk ͼy"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>pip install </span><span class="ͼu">-r</span><span> requirements.txt</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

### 3️⃣ Create `.env` File

<pre class="overflow-visible! px-0!" data-start="2817" data-end="2973"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="w-full overflow-x-hidden overflow-y-auto"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼk ͼy"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>MONGO_URI=your_mongodb_uri</span><br/><span>TWILIO_ACCOUNT_SID=your_sid</span><br/><span>TWILIO_AUTH_TOKEN=your_token</span><br/><span>TWILIO_PHONE=your_twilio_number</span><br/><span>USER_PHONE=your_mobile_number</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

### 4️⃣ Run the Application

<pre class="overflow-visible! px-0!" data-start="3009" data-end="3055"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="w-full overflow-x-hidden overflow-y-auto"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼk ͼy"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>python CnA_detection_V6_testing.py</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

### 5️⃣ Open Dashboard

<pre class="overflow-visible! px-0!" data-start="3086" data-end="3115"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="w-full overflow-x-hidden overflow-y-auto pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼk ͼy"><div class="cm-scroller"><div class="cm-content q9tKkq_readonly"><span>http://127.0.0.1:5000</span></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## 📊 Dashboard Features

* 📺 Live video monitoring
* 📋 Real-time event logs
* 📊 Analytics (crowd trends & severity distribution)
* 🚨 Alert visualization
* 🖼 Clickable event snapshots

---

## 🔥 Key Highlights

* Real-time intelligent surveillance system
* Combines **AI + clustering + analytics**
* Efficient alert system with spam prevention
* Scalable architecture for smart city applications
* Robust handling of database failures
