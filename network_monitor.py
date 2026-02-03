import pyshark

def analyze_network():
    cap = pyshark.LiveCapture(interface="Wi-Fi", display_filter="tcp")
    
    total_packets = 0
    total_bytes = 0

    for packet in cap.sniff_continuously(packet_count=10):
        try:
            total_packets += 1
            total_bytes += int(packet.length)
        except AttributeError:
            continue

    avg_bandwidth = (total_bytes / total_packets) / 1024  # Convert to KBps
    return avg_bandwidth

print("Estimated Bandwidth:", analyze_network(), "KBps")

