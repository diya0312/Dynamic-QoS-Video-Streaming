from flask import Flask, render_template, request

app = Flask(__name__)

# Function to determine video quality based on network speed
def choose_video_quality(latency, bandwidth):
    if latency > 100 or bandwidth < 2:
        return "output_480p.mp4"
    elif bandwidth < 5:
        return "output_720p.mp4"
    else:
        return "output_1080p.mp4"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stream")
def stream():
    # Simulating network conditions (later replaced with real-time analysis)
    latency = float(request.args.get("latency", 50))  
    bandwidth = float(request.args.get("bandwidth", 5))

    video_file = choose_video_quality(latency, bandwidth)
    return {"video_url": f"/static/{video_file}"}

if __name__ == "__main__":
    app.run(debug=True)

