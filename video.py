from MvCamera import Camera
import cv2

IMG_WIDTH = 3000
IMG_HEIGHT = 2000

def close_camera(cam):
    cam.stopCapture()
    cam.closeCamera()

def connect_camera():
    cam = Camera()
    camList = cam.findDevices()
    if camList.nDeviceNum:
        cam.openCamera(0)
        cam.configureCapture(
            capture_mode=0,
            width=IMG_WIDTH,
            height=IMG_HEIGHT,
            x_offset=0,
            y_offset=0,
            ae_mode=True,
            ae_time=20,
            white_balance=True,
            high_value=0,
            low_value=0,
            fps=30,  # Dummy value
            pixel_format=0x0108000A,
            gain=8,
        )
        cam.startCapture()
        return cam
    else:
        raise Exception("No camera devices found.")

if __name__ == "__main__":
    cam = connect_camera()

    # Setup VideoWriter (uses dummy FPS)
    out = cv2.VideoWriter(
        "output.mp4",
        cv2.VideoWriter_fourcc(*"mp4v"),
        10,  # Just a placeholder FPS
        (IMG_WIDTH, IMG_HEIGHT)
    )

    while True:
        img = cam.getImage()
        if img is not None:
            cv2.imshow("Camera Feed", img)
            out.write(img)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    close_camera(cam)
    out.release()
    cv2.destroyAllWindows()
