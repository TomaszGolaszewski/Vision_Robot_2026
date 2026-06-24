import cv2
import numpy as np


def draw_axis(img, center, eigenvector, length=200, color=(255, 0, 0), thickness=2):
    """Function that draws the axis of symmetry using the PCA method.

    PCA (Principal Component Analysis - Analiza Składowych Głównych) 
    is a common statistical technique used for dimensionality reduction.
    (eigenvector - wektor własny)
    """
    x0, y0 = center
    x1 = int(x0 + eigenvector[0] * length)
    y1 = int(y0 + eigenvector[1] * length)
    x2 = int(x0 - eigenvector[0] * length)
    y2 = int(y0 - eigenvector[1] * length)

    cv2.line(img, (x1, y1), (x2, y2), color, thickness)


def run_test():

    # initializing webcam video capture
    webcam = cv2.VideoCapture(0)
    if not webcam.isOpened():
        print("Cannot open camera!")
        exit()

    while True:
        ret, frame = webcam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # detect bright object
        _, thresh = cv2.threshold(blur, 150, 255, cv2.THRESH_BINARY)

        # detect object outlines
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # the largest object
            largest = max(contours, key=cv2.contourArea)

            for cnt in contours:
                if cnt is largest:
                    # red contour
                    cv2.drawContours(frame, [cnt], -1, (0, 0, 255), 3)

                    # PCA for the symmetry axes
                    # PCA (Principal Component Analysis - Analiza Składowych Głównych) 
                    # is a common statistical technique used for dimensionality reduction.
                    data = cnt.reshape(-1, 2).astype(np.float32)
                    mean, eigenvectors, eigenvalues = cv2.PCACompute2(data, mean=None)
                    # print(eigenvectors, np.linalg.norm(eigenvectors[0]))

                    center = tuple(mean[0].astype(int))
                    main_axis = eigenvectors[0]  # main axis

                    # draw the axis of symmetry (blue)
                    draw_axis(frame, center, main_axis, color=(255, 0, 0), thickness=2)

                else:
                    # green contour
                    cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)

        # draw window
        cv2.imshow("Wykrywanie jasnych obiektów", frame)
        # cv2.imshow("Debug", thresh)

        # program termination (ESC)
        if cv2.waitKey(1) == 27:
            break

    webcam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_test()

# TODO: dodać progowanie adaptacyjne ???