import cv2
import numpy as np
import time
from typing import List, Dict, Any, Tuple, Optional
from app.pipeline.detector import TrackedObject

def ccw(A, B, C):
    """Utility function to check counterclockwise orientation of 3 points."""
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(A, B, C, D):
    """Return true if line segment AB intersects line segment CD."""
    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)


class SpatialAnalyticsEngine:
    """
    Performs real-time spatial event detection:
    1. Restricted Zone intrusion detection (polygon area)
    2. Virtual Tripwire crossing detection (line segment crossing)
    3. Loitering detection (dwell time threshold)
    """

    @staticmethod
    def check_zone_intrusion(
        track: TrackedObject,
        zone_coords: List[List[float]],
        frame_width: int,
        frame_height: int
    ) -> bool:
        """
        Checks if the tracked object's centroid is inside the polygon restricted zone.
        zone_coords are normalized [x, y] in [0.0, 1.0].
        """
        if not zone_coords or len(zone_coords) < 3:
            return False

        # Convert normalized coordinates to pixel coordinates
        pts = np.array([
            [int(pt[0] * frame_width), int(pt[1] * frame_height)]
            for pt in zone_coords
        ], dtype=np.int32)

        centroid_pt = (int(track.centroid[0]), int(track.centroid[1]))

        # cv2.pointPolygonTest returns > 0 for inside, 0 for on edge, < 0 for outside
        result = cv2.pointPolygonTest(pts, centroid_pt, False)
        return result >= 0

    @staticmethod
    def check_tripwire_crossing(
        track: TrackedObject,
        tripwire_coords: List[List[float]],
        frame_width: int,
        frame_height: int
    ) -> bool:
        """
        Checks if the movement line of the object between previous position and current position
        intersects the virtual tripwire line segment.
        """
        if not tripwire_coords or len(tripwire_coords) < 2:
            return False

        if len(track.history) < 2:
            return False

        # Previous position and current position
        pt_prev = track.history[-2]
        pt_curr = track.history[-1]

        # Tripwire line segment in pixel coordinates
        tw_p1 = (int(tripwire_coords[0][0] * frame_width), int(tripwire_coords[0][1] * frame_height))
        tw_p2 = (int(tripwire_coords[1][0] * frame_width), int(tripwire_coords[1][1] * frame_height))

        # Check intersection
        return intersect(pt_prev, pt_curr, tw_p1, tw_p2)

    @staticmethod
    def check_loitering(track: TrackedObject, threshold_seconds: float = 5.0) -> Tuple[bool, float]:
        """Checks if dwell time exceeds loitering threshold."""
        dwell_time = time.time() - track.dwell_start
        return dwell_time > threshold_seconds, dwell_time
