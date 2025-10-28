from MvCamera import Camera
import cv2

IMG_WIDTH = 3000
IMG_HEIGHT = 2000
x_offset = 0
y_offset = 0
exposure_time = 20


def close_camera(cam):
    cam.stopCapture()
    cam.closeCamera()


def connect_camera():
    # initialize camera and check availability
    cam = Camera()
    camList = cam.findDevices()
    if camList.nDeviceNum:
        cam.openCamera(0)
        cam.configureCapture(
            capture_mode=0,
            width=IMG_WIDTH,
            height=IMG_HEIGHT,
            x_offset=x_offset,
            y_offset=y_offset,
            ae_mode=False,
            ae_time=exposure_time,
            white_balance=True,
            high_value=0,
            low_value=0,
            fps=30,
            pixel_format=0x0108000A,
            gain=8,
        )
        cam.startCapture()
        return cam

if __name__ =="__main__":
    cam=connect_camera()

    while True:
        img=cam.getImage()
        cv2.namedWindow("output_image", cv2.WINDOW_GUI_NORMAL)
        #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        cv2.imshow("output_image", img)
        cv2.imwrite("Powder_Distabance.")
        # press q to close camera on image screen
        if cv2.waitKey(0) & 0xFF == ord("q"):
            break
        
    close_camera(cam)
