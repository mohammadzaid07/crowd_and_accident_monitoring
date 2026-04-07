# 🚦 Crowd & Accident Monitoring System

## 📌 Overview

This project is a **real-time smart monitoring system** that detects:

* 👥 Crowd density
* 🚨 Road accidents

It provides **live video analysis, event logging, alerts, and analytics dashboard** to help in smart city management.

---

## 🎯 Features

### 🔹 Detection System

* Crowd detection using **YOLO**
* Accident detection using trained model
* Clustering using **DBSCAN** for crowd analysis

### 🔹 Real-Time Dashboard

* Live video feed
* Event logs (crowd & accident)
* Severity indicators (LOW / MEDIUM / HIGH / CRITICAL)

### 🔹 Analytics

* 📊 Crowd trend graph
* 📊 Severity distribution chart
* 📊 Live statistics (total events, latest severity)

### 🔹 Alerts

* SMS alerts using **Twilio API**

### 🔹 Database

* Event logging using **MongoDB Atlas**
* Stores:
  * crowd events
  * accident events

### 🔹 Security

* Sensitive keys stored using **.env file**

---

## 🧠 System Workflow

1. Capture video input
2. Detect objects (people / accidents)
3. Analyze crowd using clustering
4. Assign severity level
5. Store event in database
6. Show results on dashboard
7. Send alerts (if critical)

---

## 🛠️ Tech Stack

* **Python**
* **Flask**
* **YOLO (Ultralytics)**
* **OpenCV**
* **MongoDB Atlas**
* **Twilio API**
* **Chart.js (Dashboard)**
* **HTML / CSS / JavaScript**

---

## 📁 Project Structure

```
project/
│
├── app.py
├── CnA_detection_V6_testing.py
├── pi_stream.py
├── templates/
├── static/
├── requirements.txt
├── README.md
├── .env (not uploaded)
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

```
git clone https://github.com/mohammadzaid07/crowd_and_accident_monitoring.git
cd crowd_and_accident_monitoring
```

---

### 2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

### 3️⃣ Create `.env` file

```
MONGO_URI=your_mongodb_uri
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE=your_number
USER_PHONE=your_number
```

---

### 4️⃣ Run the Application

```
python CnA_detection_V6_testing.py
```

---

### 5️⃣ Open Dashboard

```
http://127.0.0.1:5000
```

---

## 📊 Dashboard Preview

* Live video feed
* Real-time logs
* Analytics charts
* Severity-based alerts

*(Add screenshots here if needed)*

---

## 🔥 Key Highlights

* Real-time intelligent monitoring system
* Adaptive severity detection
* Integrated analytics dashboard
* Practical smart city application

---

## 🚀 Future Improvements

* Map-based visualization
* Email alerts
* Mobile app integration
* Multi-camera support

---

## 👨‍💻 Author

**Mohammad Zaid**
M.Tech (Computer Engineering)

---

## 📌 Note

This project is for  **academic and research purposes** .
