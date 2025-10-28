import sys
import os
import cv2
import numpy as np

sys.path.append("/opt/MVS/Samples/64/Python/MvImport")
sys.path.append("C:\\Program Files (x86)\\MVS\\Development\\Samples\\Python\\MvImport")

from MvCameraControl_class import *


class Camera:
    def __init__(self) -> None:
        self.imgSize: int = 0
        self.width: int = 0
        self.height: int = 0
        self.format: int = 0
        self.isInitialized: bool = False
        self.isTriggered: bool = False
        self.isCapStarted: bool = False
        self.mfgName: str = ""
        self.cam: MvCamera = MvCamera()
        self.stFrameInfo = None
        self.imgSize = None
        self.data_buf = None

    def findDevices(self) -> MV_CC_DEVICE_INFO_LIST:
        deviceList: MV_CC_DEVICE_INFO_LIST = MV_CC_DEVICE_INFO_LIST()
        tlayerType: int = MV_GIGE_DEVICE | MV_USB_DEVICE
        MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
        return deviceList

    def openCamera(self, index: int) -> int:
        ret = 0

        deviceList = self.findDevices()
        stDeviceList = cast(
            deviceList.pDeviceInfo[index], POINTER(MV_CC_DEVICE_INFO)
        ).contents

        ret = self.cam.MV_CC_CreateHandle(stDeviceList)
        if ret == MV_OK:
            ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            for char in stDeviceList.SpecialInfo.stGigEInfo.chManufacturerName:
                self.mfgName = self.mfgName + chr(char)
        return ret

    def setExposureTime(self, exposureTime: float):
        if self.mfgName == "Basler":
            self.cam.MV_CC_SetFloatValue("ExposureTimeAbs", 1000 * exposureTime)
        else:
            self.cam.MV_CC_SetFloatValue("ExposureTime", 1000 * exposureTime)

    def configureCapture(
        self,
        capture_mode: int,
        width: int,
        height: int,
        x_offset: int,
        y_offset: int,
        ae_mode: bool,
        ae_time: float,
        white_balance: bool,
        high_value: int,
        low_value: int,
        fps: float = 30,
        reverseX: bool = False,
        pixel_format=0x0108000A,  # 0x01080009
        gain=6,
    ):
        ret = 0
        exposureTime = 1000 * ae_time
        self.isTriggered = capture_mode
        ret += self.cam.MV_CC_SetIntValue("OffsetX", 0)
        ret += self.cam.MV_CC_SetIntValue("OffsetY", 0)
        ret += self.cam.MV_CC_SetIntValue("Width", width)
        ret += self.cam.MV_CC_SetIntValue("Height", height)
        ret += self.cam.MV_CC_SetIntValue("OffsetX", x_offset)
        ret += self.cam.MV_CC_SetIntValue("OffsetY", y_offset)

        ret += self.cam.MV_CC_SetBoolValue("ReverseX", reverseX)

        ret += self.cam.MV_CC_SetEnumValue("PixelFormat", pixel_format)

        ret += self.cam.MV_CC_SetFloatValue("AcquisitionFrameRate", fps)
        ret += self.cam.MV_CC_SetFloatValue("TriggerDelay", 1000 * low_value)

        # ret += self.cam.MV_CC_SetBoolValue("AcquisitionFrameRateEnable", 0)

        if self.mfgName == "Basler":
            ret += self.cam.MV_CC_SetFloatValue("ExposureTimeAbs", exposureTime)
            ret += self.cam.MV_CC_SetFloatValue("GainRaw", 160)
            print("Setting Bascam")
        else:
            ret += self.cam.MV_CC_SetFloatValue("ExposureTime", exposureTime)
            ret += self.cam.MV_CC_SetFloatValue("GainRaw", gain)

        if white_balance:
            ret += self.cam.MV_CC_SetEnumValue("BalanceWhiteAuto", 1)
        else:
            ret += self.cam.MV_CC_SetEnumValue("BalanceWhiteAuto", 0)

        print(f"High Value: {high_value}")
        print(f"Low Value: {low_value}")
        ret += self.cam.MV_CC_SetIntValue("StrobeLineDuration", high_value)
        ret += self.cam.MV_CC_SetIntValue("StrobeLineDelay", low_value)

        ret += self.cam.MV_CC_SetEnumValue("LineSelector", 1)
        ret += self.cam.MV_CC_SetEnumValue("LineMode", 8)
        ret += self.cam.MV_CC_SetBoolValue("LineInverter", 1)
        ret += self.cam.MV_CC_SetBoolValue("StrobeEnable", 1)
        ret += self.cam.MV_CC_SetEnumValue("LineSource", 0)

        if self.isTriggered:
            ret += self.cam.MV_CC_SetEnumValue("TriggerMode", 1)
            ret += self.cam.MV_CC_SetBoolValue("AcquisitionFrameRateEnable", 0)

            if self.mfgName == "Basler":
                ret += self.cam.MV_CC_SetEnumValue("TriggerSource", 1)
            else:
                ret += self.cam.MV_CC_SetEnumValue(
                    "TriggerSource", MV_TRIGGER_SOURCE_LINE0
                )
            ret += self.cam.MV_CC_SetEnumValue("SensorShutterMode", 1)
        else:
            ret += self.cam.MV_CC_SetEnumValue("TriggerMode", 0)
            ret += self.cam.MV_CC_SetBoolValue("AcquisitionFrameRateEnable", 1)

        ret += self.cam.MV_CC_SetEnumValue("LineSelector", 2)
        ret += self.cam.MV_CC_SetEnumValue("LineMode", 8)
        ret += self.cam.MV_CC_SetBoolValue("LineInverter", 1)
        ret += self.cam.MV_CC_SetBoolValue("StrobeEnable", 1)
        ret += self.cam.MV_CC_SetEnumValue("LineSource", 5)

        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))

        ret += self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
        self.imgSize = stParam.nCurValue

        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()
        self.data_buf = (c_ubyte * self.imgSize)()
        self.isInitialized = True

        return 0

    def startCapture(self):
        assert self.isInitialized != False

        ret = self.cam.MV_CC_StartGrabbing()
        if ret == MV_OK:
            self.isCaptured = True

        return ret

    def stopCapture(self):
        if not self.isCapStarted:
            return 0
        ret = self.cam.MV_CC_StopGrabbing()
        if ret == MV_OK:
            self.isCapStarted = False
        return ret

    def closeCamera(self):
        if self.data_buf != None:
            del self.data_buf
        ret = self.cam.MV_CC_DestroyHandle()
        self.isInitialized = ret != MV_OK
        return ret

    def getImage(self):
        ret = self.cam.MV_CC_GetOneFrameTimeout(
            self.data_buf, self.imgSize, self.stFrameInfo, 1000
        )
        data_buffer = byref(self.data_buf)
        if ret == MV_OK:
            img = np.frombuffer(bytes(data_buffer._obj), np.uint8).reshape(
                (self.stFrameInfo.nHeight, self.stFrameInfo.nWidth)
            )
            # return cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB)
            return cv2.cvtColor(img, cv2.COLOR_BAYER_GB2RGB)
        else:
            print("No Data Found")
            ret = 1

    def __del__(self):
        self.stopCapture()
        self.closeCamera()
