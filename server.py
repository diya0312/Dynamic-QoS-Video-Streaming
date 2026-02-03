import socket
import threading
import ssl
import pickle
import struct
import cv2
import sys

video_paths = {
    "input": {
        "240p": "static/output_240p.mp4",
        "480p": "static/output_480p.mp4",
        "720p": "static/output_720p.mp4",
        "1080p": "static/output_1080p.mp4"
    },
    "input2": {
        "240p": "static/output2_240p.mp4",
        "480p": "static/output2_480p.mp4",
        "720p": "static/output2_720p.mp4",
        "1080p": "static/output2_1080p.mp4"
    }
}

video_frames = {}

def preload_videos():
    for video_name, resolutions in video_paths.items():
        video_frames[video_name] = {}
        for res, path in resolutions.items():
            cap = cv2.VideoCapture(path)
            frames = []
            while True:
                success, frame = cap.read()
                if not success:
                    break
                _, buffer = cv2.imencode('.jpg', frame)
                frames.append(pickle.dumps(buffer))
            video_frames[video_name][res] = frames
            print(f"[LOADED] {len(frames)} frames for {video_name} at {res}")

def handle_client(connstream, addr):
    print(f"[CONNECTED - SSL] {addr} using {connstream.cipher()}")
    paused = False  # Play/Pause state
    try:
        while True:
            data = connstream.recv(1024).decode()
            if not data:
                break

            # Handle pause/play commands
            if data == "pause":
                paused = True
                print(f"[PAUSED] Stream paused by {addr}")
                continue
            elif data == "play":
                paused = False
                print(f"[RESUMED] Stream resumed by {addr}")
                continue

            # If paused, skip sending frames
            if paused:
                continue

            try:
                video_name, res, idx = data.split(',')
                idx = int(idx)

                if video_name not in video_frames or \
                   res not in video_frames[video_name] or \
                   idx >= len(video_frames[video_name][res]):
                    connstream.sendall(struct.pack("!I", 0))
                    continue

                frame_data = video_frames[video_name][res][idx]
                connstream.sendall(struct.pack("!I", len(frame_data)) + frame_data)

            except Exception as e:
                print(f"[ERROR] {e}")
                connstream.sendall(struct.pack("!I", 0))
    except Exception as e:
        print(f"[ERROR] Client connection failed: {e}")
    finally:
        connstream.close()
        print(f"[DISCONNECTED] {addr}")


def main():
    preload_videos()

    if len(sys.argv) < 2:
        print("Use python server.py <port>")
        return

    port = int(sys.argv[1])

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)
    print(f"[SERVER STARTED on port {port} with SSL] Waiting for clients...")

    while True:
        client_socket, addr = server_socket.accept()
        connstream = context.wrap_socket(client_socket, server_side=True)
        thread = threading.Thread(target=handle_client, args=(connstream, addr))
        thread.start()

if __name__ == "__main__":
    main()
