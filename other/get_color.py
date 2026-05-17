"""
This script opens a live camera preview and allows the user to click on any pixel
to display its RGB and HSV color values in the terminal. 

It is useful for color sampling, calibration, and computer vision experiments.
"""

import cv2

# mouse callback
def mouse_callback(event, x, y, flags, param):
    global frame

    if event == cv2.EVENT_LBUTTONDOWN and frame is not None:
        # get BGR color from the current frame
        b, g, r = frame[y, x]

        # convert single pixel BGR -> HSV
        pixel_bgr = frame[y:y+1, x:x+1]  # 1x1 slice
        pixel_hsv = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = pixel_hsv[0, 0]

        print(f"Clicked at ({x}, {y})")
        print(f"BGR: ({b}, {g}, {r})")
        print(f"RGB: ({r}, {g}, {b})")
        print(f"HSV: ({h}, {s}, {v})")

# open camera (0 – default)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera.")
    exit(1)

cv2.namedWindow("Camera Preview")
cv2.setMouseCallback("Camera Preview", mouse_callback)

frame = None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame from camera.")
        break

    cv2.imshow("Camera Preview", frame)

    # exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
