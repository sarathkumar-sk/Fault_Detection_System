from MvCamera import Camera
import cv2
import numpy as np
from ultralytics import YOLO


model = YOLO("best.pt")
    

IMG_WIDTH = 3000
IMG_HEIGHT = 2000
x_offset = 0
y_offset = 0
exposure_time = 93924


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
def draw_bounding_boxes(img, results, color=(0, 255, 0)):
        """Draw bounding boxes on the image."""
        img_copy = img.copy()
        for result in results:
            for box in result.boxes:
                b = box.xyxy[0]  # Bounding box coordinates (x1, y1, x2, y2)
                confidence = float(box.conf) # Confidence score
                class_id = int(box.cls)  # Class ID

                # Draw rectangle and label
                cv2.rectangle(img_copy, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 10)
                label = f"Class: {class_id}, Conf: {confidence:.2f}"
                cv2.putText(img_copy, label, (int(b[0]), int(b[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            2, color, 10, cv2.LINE_AA)
        return img_copy


if __name__ =="__main__":
   
    cam=connect_camera()
    while True:

        img=cam.getImage()
        cv2.namedWindow("output_image", cv2.WINDOW_GUI_NORMAL)
        cv2.namedWindow("yolo-detection", cv2.WINDOW_GUI_NORMAL)
        gray=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        eq=cv2.equalizeHist(gray)
        norm=cv2.normalize(eq,None,0,255,cv2.NORM_MINMAX).astype(np.uint8)
        final=cv2.cvtColor(norm,cv2.COLOR_GRAY2BGR)
        results = model(final)
       
    
        img_with_boxes = draw_bounding_boxes(final, results, color=(0, 255, 0))
        cv2.imshow("output_image", img)
        cv2.imshow("yolo-detection",img_with_boxes)
        # press q to close camera on image screen
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        
    close_camera(cam)
