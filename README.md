# Dynamic QoS-Based Adaptive Video Streaming System

A real-time Quality of Service (QoS) aware adaptive video streaming system that dynamically adjusts video resolution based on network latency using raw socket programming, multithreading, and SSL-encrypted communication. This project demonstrates how live network conditions can be monitored and used to provide smooth video playback by switching between multiple pre-encoded video resolutions.

## Features

### Dynamic QoS Management
- Continuously monitors network latency
- Automatically switches between 240p, 480p, 720p, and 1080p video streams

### Multiple Clients and Server Support
- One server handles multiple concurrent clients
- Each client runs in a separate thread
- Each client can stream a different video simultaneously

### SSL Encrypted Communication
- Secure socket communication using OpenSSL certificates
- Encrypted data transfer between client and server

### Raw Socket Programming
- Built using Python TCP sockets
- No third-party networking frameworks (no Flask, HTTP, RTSP)

### Smooth Playback
- Preloaded frames for fast access
- No runtime video transcoding


## Prerequisites

- Ubuntu or WSL2
- Python 3.8 or higher
- FFmpeg
- OpenCV
- OpenSSL

## Running The Project 

### Step 1: Create and activate virtual environment
```
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Preparing Video Files

Before running the system, videos must be pre-encoded at multiple resolutions. This is required for dynamic resolution switching during streaming.

### Step 3: For `input.mp4`

```
ffmpeg -i static/input.mp4 -vf scale=426:240 static/output_240p.mp4
ffmpeg -i static/input.mp4 -vf scale=854:480 static/output_480p.mp4
ffmpeg -i static/input.mp4 -vf scale=1280:720 static/output_720p.mp4
ffmpeg -i static/input.mp4 -vf scale=1920:1080 static/output_1080p.mp4
```

Note: Here 'input.mp4' can be replaced with any video file, the videos uploaded here are just sample videos.

### Step 4: SSL Certificate Generation (One-Time Setup)
```
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Step 5: Start the Server 
```
python3 server.py <port>
```
Here port can be replaced with any available port within the range 9000-10000

### Step 6: Start a Client
```
source venv/bin/activate
python3 dynamic_player.py
```
### Notes

- The server must be started before any client connects.
- Each client must run in a separate terminal.
- Ensure all video files are present and correctly named in the static/ directory.






