#!/usr/bin/env python3
from __future__ import print_function
import argparse, os, time
import cv2
from camera import open_camera
from config import settings
from face_detector import FaceDetector

def parse_args():
    parser = argparse.ArgumentParser(description="Registro de muestras faciales")
    parser.add_argument("--name", required=True)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--interval", type=float, default=0.25)
    return parser.parse_args()

def main():
    args = parse_args()
    output_dir = os.path.join(settings.faces_dir, args.name)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    detector = FaceDetector(
        settings.haar_model,
        settings.detection_scale_factor,
        settings.detection_min_neighbors,
        settings.detection_min_size
    )
    camera = open_camera(settings)
    saved, last_save = 0, 0.0
    try:
        while saved < args.samples:
            ok, frame = camera.read()
            if not ok or frame is None:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = sorted(
                detector.detect(gray),
                key=lambda item: int(item[2]) * int(item[3]),
                reverse=True
            )
            if faces:
                x, y, w, h = faces[0]
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                if time.time() - last_save >= args.interval:
                    crop = gray[y:y+h, x:x+w]
                    filename = os.path.join(output_dir, "{:04d}.jpg".format(saved+1))
                    if cv2.imwrite(filename, crop):
                        saved += 1
                        last_save = time.time()
                        print("Muestra guardada: {}/{} - {}".format(
                            saved, args.samples, filename))
            cv2.putText(frame, "Muestras: {}/{}".format(saved, args.samples),
                        (15,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0,255,255), 2)
            cv2.imshow("Registro facial v2", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
    print("Registro finalizado. Muestras guardadas: {}".format(saved))

if __name__ == "__main__":
    main()
