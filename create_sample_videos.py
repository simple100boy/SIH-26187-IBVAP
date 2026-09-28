import cv2
import numpy as np
import os
import math
from pathlib import Path

def generate_sample_videos():
    video_dir = Path("data/videos")
    video_dir.mkdir(parents=True, exist_ok=True)

    cameras = [
        ("cam-01.mp4", "CAM-01 ALPHA GATE NORTH", (30, 45, 40), "day"),
        ("cam-02.mp4", "CAM-02 EASTERN PERIMETER", (45, 55, 60), "day_road"),
        ("cam-03.mp4", "CAM-03 VEHICLE CHECKPOINT", (50, 50, 50), "checkpoint"),
        ("cam-04.mp4", "CAM-04 THERMAL PERIMETER", (15, 20, 30), "thermal"),
        ("cam-05.mp4", "CAM-05 NIGHT WATCH TOWER", (20, 25, 22), "night"),
    ]

    width, height = 640, 360
    fps = 30.0
    num_frames = 150 # 5 seconds loop

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    for filename, label, bg_color, scene_type in cameras:
        file_path = video_dir / filename
        writer = cv2.VideoWriter(str(file_path), fourcc, fps, (width, height))

        for frame_idx in range(num_frames):
            t = frame_idx / fps
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = bg_color

            if scene_type == "day":
                # Draw border fence & dirt road
                cv2.line(frame, (0, 200), (width, 200), (80, 100, 90), 2)
                for x in range(30, width, 60):
                    cv2.line(frame, (x, 160), (x, 240), (100, 120, 110), 2)
                # Dirt path
                pts = np.array([[100, 360], [250, 200], [390, 200], [540, 360]], np.int32)
                cv2.fillPoly(frame, [pts], (45, 60, 55))
                # Walking patrol figure
                px = int(200 + (t * 50) % 250)
                py = 240
                cv2.circle(frame, (px, py - 30), 10, (200, 210, 220), -1)
                cv2.line(frame, (px, py - 20), (px, py + 15), (200, 210, 220), 4)

            elif scene_type == "day_road":
                # Eastern perimeter roadway
                cv2.rectangle(frame, (150, 0), (490, 360), (40, 45, 45), -1)
                cv2.line(frame, (320, 0), (320, 360), (0, 200, 255), 2)
                # Moving SUV car
                vy = int((t * 70) % 360)
                cv2.rectangle(frame, (280, vy), (360, vy + 70), (30, 50, 100), -1)
                # License plate banner
                cv2.rectangle(frame, (290, vy + 60), (350, vy + 70), (240, 240, 240), -1)
                cv2.putText(frame, "JK02-AB-9876", (292, vy + 68), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 0), 1)

            elif scene_type == "checkpoint":
                # Vehicle Checkpoint gate & people
                cv2.rectangle(frame, (0, 0), (640, 180), (60, 65, 70), -1)
                cv2.putText(frame, "CHECKPOINT DELTA", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 220, 240), 2)
                # People walking
                px1 = int(100 + (t * 40) % 400)
                cv2.circle(frame, (px1, 260), 12, (220, 200, 180), -1)
                cv2.line(frame, (px1, 272), (px1, 320), (50, 80, 120), 5)

            elif scene_type == "thermal":
                # Thermal IR scene
                cv2.rectangle(frame, (100, 100), (540, 300), (30, 35, 40), -1)
                # Bright thermal person signature
                tx = int(150 + (t * 45) % 350)
                cv2.circle(frame, (tx, 220), 15, (240, 240, 250), -1)
                cv2.line(frame, (tx, 235), (tx, 280), (240, 240, 250), 6)

            elif scene_type == "night":
                # Night Watch Tower
                cv2.rectangle(frame, (400, 80), (480, 360), (40, 45, 50), -1) # Watchtower pillar
                # Person moving
                nx = int(120 + (t * 35) % 250)
                cv2.circle(frame, (nx, 260), 10, (180, 190, 200), -1)
                cv2.line(frame, (nx, 270), (nx, 310), (180, 190, 200), 4)

            # Draw Watermark tag
            cv2.putText(frame, f"CCTV REAL VIDEO STREAM | {label}", (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 200), 1)

            writer.write(frame)

        writer.release()
        print(f"Generated sample video: {file_path}")

if __name__ == "__main__":
    generate_sample_videos()
