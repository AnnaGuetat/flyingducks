# flyingducks

DGMD E-17 (16144) Robotics, Autonomous Vehicles, Drones, and AI
Fall 2019
Harvard Extension School

Team:
 Anna Guetat
 Lech Brzozowski
 

Motivation:
We have decided to start on both setups autonomous drive and flight. We have equipment available for both, and our curiosity drives us towards trying both initially and choosing along the way on the final project.  
 
For autonomous drive, the focus is line following with obstacle detection.

Focus of this repository is Duckiebot and motivation to learn with hands on experience autonomous drive and fly systems with focus on lane following and  obstacle detection.
Additional motivation came from understanding where the technology is heading and what ethical constraints it already brings.

For lane following the focus is on demo: 

   Code: https://docs.duckietown.org/DT19/opmanual_duckiebot/out/demo_lane_following.html

For obstacle detection: 

   Code: 
   https://github.com/duckietown/duckietown-objdet/blob/master/README.md

   Duckietown learning materials: https://docs.duckietown.org/DT19/learning_materials/out/object_detection.html

   Object Detection and Imitation Learning in Duckietown:
   https://minyoung.info/documents/yolo_report.pdf

Future work:

    Object Detection with color segmentation and color detection
    It would be interesting to benefit from learnings of OpenCV to partition images captured by Duckiebot camera into set of pixels and determine behavior based on it. For example stop on the red line.
    That would build over edge detection demo as color detection or segmentation combined with edge detection leads to accurate results compared to just edge detection.
    Additional:
       - Detecting distance to the object
       - Classifying detected objects (e.g. ducks, other vehicles)
       - Object tracking
       - Learn SLAM (simultaneous localisation & mapping)

