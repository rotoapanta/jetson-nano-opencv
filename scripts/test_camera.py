#!/usr/bin/env python3
from __future__ import print_function
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2
from camera import open_camera
from config import settings

camera = open_camera(settings)
start, frames = time.time(), 0
try:
    while True:
        ok, frame = camera.read()
        if not ok:
            print("ERROR:", camera.last_error)
            break
        frames += 1
        cv2.imshow("Prueba cámara v2", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
finally:
    elapsed = max(0.001, time.time() - start)
    camera.release()
    cv2.destroyAllWindows()
    print("FPS promedio: {:.2f}".format(frames / elapsed))
