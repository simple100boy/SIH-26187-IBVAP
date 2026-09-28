================================================================================
               IBVAP - REAL CCTV VIDEO INPUT INSTRUCTIONS
================================================================================

To use your own real CCTV video recordings or MP4 files for AI analysis:

1. Place your video files in this folder (`data/videos/`):
   - `cam-01.mp4` -> For Camera 1 (CAM-01 ALPHA GATE NORTH)
   - `cam-02.mp4` -> For Camera 2 (CAM-02 EASTERN PERIMETER)
   - `cam-03.mp4` -> For Camera 3 (CAM-03 VEHICLE CHECKPOINT)
   - `cam-04.mp4` -> For Camera 4 (CAM-04 THERMAL PERIMETER)
   - `cam-05.mp4` -> For Camera 5 (CAM-05 NIGHT WATCH TOWER)
   - `cam-06.mp4` -> For Camera 6 (CAM-06 RESERVE CAMERA)

2. Supported Video Formats: `.mp4`, `.avi`, `.mkv`, `.mov`

3. The system will automatically detect the video file, loop it smoothly, and perform real-time AI object detection, tracking, ANPR plate recognition, FRS facial analysis, and tripwire intrusion alerts!

4. If a video file is missing for a camera (e.g., `cam-06.mp4`), the UI will display the Camera Offline card as configured in the C2 layout.
