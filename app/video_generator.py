import cv2
import numpy as np
import time
import math
import random
from typing import Dict, Any

class SyntheticBorderVideoGenerator:
    """
    Generates realistic synthetic video streams representing standard IP CCTV feeds
    at Border Out Posts (BOPs), checkposts, perimeter fences, and strategic locations.
    Allows zero-dependency offline demonstration of the entire IBVAP AI pipeline.
    """
    def __init__(self, camera_id: str, width: int = 1280, height: int = 720):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.frame_count = 0
        self.start_time = time.time()

    def generate_frame(self, night_mode: bool = False) -> np.ndarray:
        self.frame_count += 1
        t = time.time() - self.start_time

        # Create canvas background
        if self.camera_id == "cam-bop-01":
            # BOP North Sector - Night Border Fence
            frame = self._draw_bop_north_fence(t)
        elif self.camera_id == "cam-bop-02":
            # Checkpost Alpha - Vehicle Road & ANPR
            frame = self._draw_checkpost_road(t)
        elif self.camera_id == "cam-bop-03":
            # Perimeter Sector 4 - Patrol & FRS
            frame = self._draw_perimeter_patrol(t)
        else:
            # Outpost Bunker - Low Light & Unattended Objects
            frame = self._draw_outpost_bunker(t)

        # Apply timestamp overlay
        cv2.putText(
            frame,
            f"REC [LIVE] {time.strftime('%Y-%m-%d %H:%M:%S')}.{int((t % 1) * 1000):03d} | {self.camera_id.upper()}",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 200),
            2
        )

        return frame

    def _draw_bop_north_fence(self, t: float) -> np.ndarray:
        # Dark night border terrain background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:, :] = (20, 30, 25) # Dark greenish-gray night hue

        # Draw distant mountain range contour
        pts_mountains = np.array([
            [0, 300], [200, 220], [450, 280], [700, 190], [1000, 260], [1280, 210],
            [1280, 720], [0, 720]
        ], np.int32)
        cv2.fillPoly(frame, [pts_mountains], (12, 20, 16))

        # Draw Border Barbed Wire Fence
        fence_y = 420
        cv2.line(frame, (0, fence_y), (1280, fence_y), (80, 120, 90), 3)
        cv2.line(frame, (0, fence_y - 40), (1280, fence_y - 40), (80, 120, 90), 2)

        # Fence posts
        for x in range(50, 1280, 120):
            cv2.line(frame, (x, fence_y - 60), (x, fence_y + 80), (100, 140, 110), 3)
            # Barbed wire cross lines
            cv2.line(frame, (x - 10, fence_y - 40), (x + 10, fence_y), (120, 160, 130), 1)

        # Ground road
        road_pts = np.array([[200, 720], [500, fence_y + 80], [780, fence_y + 80], [1100, 720]], np.int32)
        cv2.fillPoly(frame, [road_pts], (28, 40, 32))

        # Moving Infiltrator Human Silhouette (Person crossing tripwire & entering restricted zone)
        pos_x = int(250 + (t * 40) % 800)
        pos_y = int(fence_y - 30 + math.sin(t * 4) * 10)

        # Draw human stick figure / silhouette
        # Head
        cv2.circle(frame, (pos_x, pos_y - 45), 12, (200, 220, 210), -1)
        # Body
        cv2.line(frame, (pos_x, pos_y - 33), (pos_x, pos_y + 15), (200, 220, 210), 8)
        # Arms walking animation
        arm_swing = int(math.sin(t * 6) * 15)
        cv2.line(frame, (pos_x - 18, pos_y - 15 + arm_swing), (pos_x + 18, pos_y - 15 - arm_swing), (200, 220, 210), 5)
        # Legs walking animation
        leg_swing = int(math.cos(t * 6) * 20)
        cv2.line(frame, (pos_x, pos_y + 15), (pos_x - 15 + leg_swing, pos_y + 55), (200, 220, 210), 6)
        cv2.line(frame, (pos_x, pos_y + 15), (pos_x + 15 - leg_swing, pos_y + 55), (200, 220, 210), 6)

        return frame

    def _draw_checkpost_road(self, t: float) -> np.ndarray:
        # Checkpost tarmac asphalt & security booth
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:, :] = (50, 50, 55)

        # Draw road lanes
        cv2.rectangle(frame, (300, 0), (980, 720), (35, 35, 40), -1)
        # Yellow border lines
        cv2.line(frame, (300, 0), (300, 720), (0, 220, 255), 4)
        cv2.line(frame, (980, 0), (980, 720), (0, 220, 255), 4)
        # White dashed center line
        for y in range(0, 720, 60):
            cv2.line(frame, (640, y), (640, y + 35), (240, 240, 240), 3)

        # Checkpost security barrier booth on right
        cv2.rectangle(frame, (1000, 250), (1220, 480), (80, 60, 40), -1)
        cv2.putText(frame, "BOP CHECKPOST 02", (1010, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Moving Vehicle (SUV / Truck) approaching gate
        v_y = int((t * 90) % 800 - 150)
        v_x = 480

        # Draw Vehicle Body
        cv2.rectangle(frame, (v_x - 70, v_y - 120), (v_x + 70, v_y + 120), (30, 40, 90), -1)
        # Roof / Windshield
        cv2.rectangle(frame, (v_x - 55, v_y - 60), (v_x + 55, v_y + 40), (70, 90, 130), -1)
        # Headlights
        cv2.circle(frame, (v_x - 50, v_y + 115), 10, (200, 255, 255), -1)
        cv2.circle(frame, (v_x + 50, v_y + 115), 10, (200, 255, 255), -1)

        # License Plate Banner on front bumper
        plate_text = "JK02-AB-9876" if (int(t / 10) % 2 == 0) else "PB08-XY-4321"
        cv2.rectangle(frame, (v_x - 45, v_y + 110), (v_x + 45, v_y + 130), (240, 240, 240), -1)
        cv2.putText(frame, plate_text, (v_x - 40, v_y + 125), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2)

        return frame

    def _draw_perimeter_patrol(self, t: float) -> np.ndarray:
        # Perimeter sector 4 with patrol walkway
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:, :] = (40, 45, 50)

        # Concrete wall background
        cv2.rectangle(frame, (0, 0), (1280, 350), (60, 65, 70), -1)
        cv2.putText(frame, "RESTRICTED PERIMETER WALL - SECTOR 4", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 200, 220), 2)

        # Patrol officer walking left to right
        off_x = int(100 + (t * 50) % 1000)
        off_y = 520

        # Draw patrol officer
        cv2.circle(frame, (off_x, off_y - 45), 14, (230, 210, 180), -1) # Head
        cv2.rectangle(frame, (off_x - 15, off_y - 30), (off_x + 15, off_y + 25), (40, 90, 50), -1) # Camo jacket
        # Legs
        cv2.line(frame, (off_x - 8, off_y + 25), (off_x - 8, off_y + 75), (30, 40, 30), 6)
        cv2.line(frame, (off_x + 8, off_y + 25), (off_x + 8, off_y + 75), (30, 40, 30), 6)

        # Unidentified suspect walking right to left
        sus_x = int(1150 - (t * 60) % 1000)
        sus_y = 500

        cv2.circle(frame, (sus_x, sus_y - 45), 14, (180, 160, 140), -1) # Head
        cv2.rectangle(frame, (sus_x - 15, sus_y - 30), (sus_x + 15, sus_y + 25), (20, 20, 20), -1) # Dark hoodie
        cv2.line(frame, (sus_x - 8, sus_y + 25), (sus_x - 8, sus_y + 75), (10, 10, 10), 6)
        cv2.line(frame, (sus_x + 8, sus_y + 25), (sus_x + 8, sus_y + 75), (10, 10, 10), 6)

        return frame

    def _draw_outpost_bunker(self, t: float) -> np.ndarray:
        # Bunker outpost dark environment
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:, :] = (15, 18, 22)

        # Bunker concrete fortification structure
        cv2.rectangle(frame, (200, 180), (1080, 600), (45, 50, 55), -1)
        cv2.rectangle(frame, (450, 300), (830, 600), (25, 28, 32), -1) # Entrance door

        # Warning signs
        cv2.putText(frame, "HIGH SECURITY BUNKER - AUTHORIZED ONLY", (240, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Unattended Bag left at bunker door
        bag_x, bag_y = 640, 530
        cv2.rectangle(frame, (bag_x - 25, bag_y - 20), (bag_x + 25, bag_y + 20), (150, 50, 30), -1)
        cv2.putText(frame, "BAG", (bag_x - 15, bag_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return frame
