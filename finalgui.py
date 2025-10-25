from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import cv2
import numpy as np
from ultralytics import YOLO
from MvCamera import Camera
import serial

class_mappings = {
    0: "Alloy Rubbing", 1: "Blisters", 2: "Blow Holes", 3: "Bound Out", 4: "Brush Mark",
    5: "Led Sweat", 6: "Masking", 7: "Powder Clot", 8: "Powder Disturbance",
    9: "Powder Segregation", 10: "Score Marks"
}

IMG_WIDTH, IMG_HEIGHT = 3000, 2000
x_offset, y_offset, exposure_time = 0, 0, 20


class YOLODetectionGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLO Detection GUI")
        self.showFullScreen()
        self.ser = serial.Serial('/dev/ttyACM0',9600)
        self.model = YOLO("./best2.pt")
        self.cam = None
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.frame_count = 0
        self.skip_rate = 0
        self.prev_tick = cv2.getTickCount()
        self.results = []
        
        self.pending_serial_message = None
        self.serial_timer = QtCore.QTimer()
        self.serial_timer.setSingleShot(True)
        self.serial_timer.timeout.connect(self.send_serial_message)


        self.total_spray_time_ms = 0
        self.defect_count = 0

        # GUI Layout
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)

        self.start_button = QtWidgets.QPushButton("Start Detection")
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 30px;")
        self.start_button.clicked.connect(self.start_detection)

        self.stop_button = QtWidgets.QPushButton("Stop Detection")
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 30px;")
        self.stop_button.clicked.connect(self.stop_detection)

        self.speed_button = QtWidgets.QPushButton("Set Speed")
        self.speed_button.setStyleSheet("font-size: 30px;")
        self.speed_button.clicked.connect(self.set_speed)
        
        # Logo Label
        self.logo_label = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("Bimetal.jpg").scaled(200, 200, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setFixedSize(pixmap.size())
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        
        # Info Labels
        self.spray_time_label = QtWidgets.QLabel("Spray Open Time: 0 ms")
        self.spray_time_label.setStyleSheet("font-size: 25px;")
        self.defect_count_label = QtWidgets.QLabel("Total Defects: 0")
        self.defect_count_label.setStyleSheet("font-size: 25px;")
        self.defect_length_label = QtWidgets.QLabel("Defect Length: 0.0 ft")
        self.defect_length_label.setStyleSheet("font-size: 25px;")
        self.spray_time_label.setAlignment(QtCore.Qt.AlignCenter)
        self.defect_count_label.setAlignment(QtCore.Qt.AlignCenter)
        self.defect_length_label.setAlignment(QtCore.Qt.AlignCenter)

        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.speed_button)

        image_layout = QtWidgets.QVBoxLayout()

        # Right-side info panel
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.addStretch() 
        info_layout.addWidget(self.spray_time_label)
        info_layout.addWidget(self.defect_count_label)
        info_layout.addWidget(self.defect_length_label)
        info_layout.addStretch()

        image_layout.addWidget(self.image_label)
        # Create a container layout for top right logo
        top_right_layout = QtWidgets.QHBoxLayout()
        top_right_layout.addStretch()
        top_right_layout.addWidget(self.logo_label)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(top_right_layout)     # Top bar with logo
        
        #main_layout.addLayout(image_layout)         # Video feed
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.addLayout(image_layout, 3)
        content_layout.addLayout(info_layout, 1)
        main_layout.addLayout(content_layout)

        main_layout.addLayout(button_layout)        # Buttons
        self.setLayout(main_layout)

    def connect_camera(self):
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
                ae_mode=True,
                ae_time=exposure_time,
                white_balance=True,
                high_value=0,
                low_value=0,
                fps=60,
                pixel_format=0x0108000A,
                gain=8,
            )
            cam.startCapture()
            return cam
        return None

    def start_detection(self):
        if self.cam is None:
            self.cam = self.connect_camera()
        self.timer.start(30)

    def stop_detection(self):
        self.timer.stop()
        if self.cam:
            self.cam.stopCapture()
            self.cam.closeCamera()
            self.cam = None

    def set_speed(self):
        speed, ok = QtWidgets.QInputDialog.getInt(self, "Set Detection Speed", "Enter the Speed Rate:", value=self.skip_rate, min=1, max=30)
        if ok:
            self.skip_rate = speed

    def update_frame(self):
        if not self.cam:
            return
        img = self.cam.getImage()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        eq = cv2.equalizeHist(gray)
        norm = cv2.normalize(eq, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        final = cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)

        if self.frame_count % 2 == 0:
            self.results = self.model(final)
        self.frame_count += 1

        annotated = self.draw_boxes(final, self.results)
       

        rgb_image = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        self.image_label.setPixmap(QtGui.QPixmap.fromImage(qt_image).scaled(
            self.image_label.width(), self.image_label.height(), QtCore.Qt.KeepAspectRatio))

    def draw_boxes(self, img, results, color=(0, 255, 0)):
        img_copy = img.copy()
        height, width = img.shape[:2]

        segments_triggered = set()
        defects_in_frame = 0
        for result in results:
            for box in result.boxes:
                b = box.xyxy[0]
                confidence = float(box.conf)
                class_id = int(box.cls)
                cls = class_mappings.get(class_id, "Unknown")
                defects_in_frame += 1

                # Draw bounding box
                cv2.rectangle(img_copy, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), color, 10)
                label = f"{cls}, {confidence:.2f}"
                cv2.putText(img_copy, label, (int(b[0]), int(b[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, color, 10, cv2.LINE_AA)

                # Find the center of the bounding box
                center_x = (b[0] + b[2]) / 2

                # Determine which vertical segment the defect belongs to
                segment_width = width / 4
                if center_x < segment_width:
                    segments_triggered.add("no1")
                elif center_x < 2 * segment_width:
                    segments_triggered.add("no2")
                elif center_x < 3 * segment_width:
                    segments_triggered.add("no3")
                else:
                    segments_triggered.add("no4")
        

        if segments_triggered:
            message = ",".join(sorted(segments_triggered)) + "\n"
            if not self.serial_timer.isActive():
                self.pending_serial_message = message
                self.serial_timer.start(self.skip_rate * 1000)  


            self.total_spray_time_ms += 0.5
            self.defect_count += defects_in_frame
            self.update_info_labels()


        # Draw segment lines
        for i in range(1, 4):  # Draw 3 vertical lines to divide into 4 segments
            x = int(i * width / 4)
            cv2.line(img_copy, (x, 0), (x, height), (255, 0, 0), 5)

        return img_copy
    
    def send_serial_message(self):
        if self.pending_serial_message:
            print("Sending to serial:", self.pending_serial_message.strip())
            self.ser.write(self.pending_serial_message.encode())
            self.pending_serial_message = None


    def update_info_labels(self):
        # Update Spray Time Label
        self.spray_time_label.setText(f"Spray Open Time: {self.total_spray_time_ms} s")
        
        # Update Defect Count Label
        self.defect_count_label.setText(f"Total Defects: {self.defect_count}")
        
        # Calculate Defect Length
        length_feet = (self.total_spray_time_ms) * 1.0
        self.defect_length_label.setText(f"Defect Length: {length_feet:.2f} ft")


    def closeEvent(self, event):
        self.stop_detection()
        event.accept()


if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    window = YOLODetectionGUI()
    window.show()
    sys.exit(app.exec_())
