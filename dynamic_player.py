import socket
import time
import cv2
import pickle
import struct
import subprocess
import ssl
import tkinter as tk
from threading import Thread
from PIL import Image, ImageTk

fps = 30  # Target frames per second
SERVER_PORT_RANGE = range(9999, 10011)
SERVER_IP = "127.0.0.1"

def ping_latency():
    try:
        output = subprocess.check_output(['ping', '-c', '1', '8.8.8.8'], stderr=subprocess.DEVNULL).decode()
        for line in output.split('\n'):
            if "time=" in line:
                return float(line.split("time=")[-1].split(" ")[0])
    except:
        pass
    return 9999

def get_resolution(latency):
    if latency < 50:
        return "1080p"
    elif latency < 100:
        return "720p"
    elif latency < 150:
        return "480p"
    else:
        return "240p"

def request_frame(sock, video_name, res, frame_idx):
    try:
        sock.sendall(f"{video_name},{res},{frame_idx}".encode())
        packed_size = sock.recv(4)
        if not packed_size:
            return None
        size = struct.unpack("!I", packed_size)[0]
        if size == 0:
            return None

        data = b''
        while len(data) < size:
            packet = sock.recv(size - len(data))
            if not packet:
                return None
            data += packet

        buffer = pickle.loads(data)
        return cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    except:
        return None

class VideoPlayer:
    def __init__(self, video_name, server_ip, server_port, root, label):
        self.video_name = video_name
        self.root = root
        self.label = label
        self.playing = False
        self.stopped = False
        self.paused = False
        self.pause_time = 0
        self.start_time = 0
        self.pause_start = 0
        self.server_ip = server_ip
        self.server_port = server_port
        self.context = ssl.create_default_context()
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        sock = socket.create_connection((server_ip, server_port))
        self.ssl_sock = self.context.wrap_socket(sock, server_hostname=server_ip)
        print(f"[SSL CONNECTED] Cipher: {self.ssl_sock.cipher()}")
        self.current_res = get_resolution(ping_latency())
        print(f"[STREAM STARTED] Using initial resolution: {self.current_res}")
        self.last_switch = time.time()

        # Load Balancer
        self.current_port = server_port
        self.load_monitor = Thread(target=self.load_balancer, daemon=True)
        self.load_monitor.start()

    def reconnect(self, new_port):
        try:
            print(f"[SERVER SWITCH] Reconnecting to port {new_port}")
            new_sock = socket.create_connection((self.server_ip, new_port))
            self.ssl_sock.close()
            self.ssl_sock = self.context.wrap_socket(new_sock, server_hostname=self.server_ip)
            print(f"[SSL RECONNECTED] Cipher: {self.ssl_sock.cipher()}")
            self.current_port = new_port
        except Exception as e:
            print(f"[ERROR] Reconnection failed: {e}")

    def load_balancer(self):
        while not self.stopped:
            time.sleep(5)
            try:
                loads = {}
                for port in SERVER_PORT_RANGE:
                    try:
                        with socket.create_connection((SERVER_IP, port), timeout=1) as s:
                            s.sendall(b"load")
                            data = s.recv(16)
                            load = float(data.decode().strip())
                            loads[port] = load
                    except:
                        continue
                if loads:
                    least_loaded_port = min(loads, key=loads.get)
                    print(f"[LOAD BALANCER] Current loads: {loads}")
                    if least_loaded_port != self.current_port:
                        self.reconnect(least_loaded_port)
            except Exception as e:
                print(f"[LOAD BALANCER ERROR] {e}")

    def play_loop(self):
        self.start_time = time.time()
        self.playing = True

        while not self.stopped:
            if self.paused:
                time.sleep(0.1)
                continue

            frame_idx = int((time.time() - self.start_time - self.pause_time) * fps)

            if time.time() - self.last_switch >= 5:
                new_res = get_resolution(ping_latency())
                if new_res != self.current_res:
                    print(f"[SWITCH] {self.current_res} → {new_res}")
                self.current_res = new_res
                self.last_switch = time.time()

            frame = request_frame(self.ssl_sock, self.video_name, self.current_res, frame_idx)
            if frame is None:
                print("[DONE] End of video.")
                break

            frame = cv2.resize(frame, (1280, 720))
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img_tk = ImageTk.PhotoImage(img)

            self.label.config(image=img_tk)
            self.label.image = img_tk
            self.root.update()

        self.ssl_sock.close()

    def pause(self):
        if self.playing and not self.paused:
            self.paused = True
            self.pause_start = time.time()
            print("[PAUSED]")

    def resume(self):
        if self.playing and self.paused:
            self.paused = False
            self.pause_time += time.time() - self.pause_start
            print("[RESUMED]")

    def stop(self):
        self.stopped = True
        self.playing = False
        self.paused = False
        print("[STOPPED]")

def start_player(video_name, server_ip, server_port):
    root = tk.Tk()
    root.title("Adaptive Video Player")

    label = tk.Label(root)
    label.pack(pady=10)

    player = VideoPlayer(video_name, server_ip, server_port, root, label)

    def on_play():
        if player.paused:
            player.resume()
        elif not player.playing:
            Thread(target=player.play_loop, daemon=True).start()

    def on_pause():
        player.pause()

    def on_stop():
        player.stop()
        root.quit()

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    play_btn = tk.Button(button_frame, text="▶ Play", command=on_play, width=10)
    play_btn.pack(side=tk.LEFT, padx=10)

    pause_btn = tk.Button(button_frame, text="|| Pause", command=on_pause, width=10)
    pause_btn.pack(side=tk.LEFT, padx=10)

    stop_btn = tk.Button(button_frame, text="■ Stop", command=on_stop, width=10)
    stop_btn.pack(side=tk.LEFT, padx=10)

    root.protocol("WM_DELETE_WINDOW", on_stop)

    # Autoplay after window loads
    root.after(100, on_play)
    root.mainloop()

def main():
    video_name = input("Enter video to play (input or input2): ").strip()
    server_port = int(input("Enter server port (anything in range of 9000-10000): ").strip())
    server_ip = "127.0.0.1"
    start_player(video_name, server_ip, server_port)

if __name__ == "__main__":
    main()

