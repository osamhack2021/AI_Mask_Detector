import cv2
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtWidgets import  QWidget, QLabel, QApplication
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import sys
import time

class CameraThread(QThread):
    changePixmap = pyqtSignal(QImage)

    model = './res10_300x300_ssd_iter_140000_fp16.caffemodel'
    config = './deploy.prototxt'
    #model = './opencv_face_detector_uint8.pb'
    #config = './opencv_face_detector.pbtxt'

    mask_model = tf.keras.models.load_model('./model.h5')
    probability_model = tf.keras.Sequential([mask_model])
    width = 64
    height = 64

    cap = cv2.VideoCapture()
    Running = True

    fileName = 0
    def setPlayType(self, fileName = 0):
        self.fileName = fileName

    def terminate(self):
        print('camera terminate')
        self.Running = False        
        # for i in range(10):
        #     time.sleep(0.1)   

        #super().terminate()

        print('camera terminate11')
        #if self.cap.isOpened() == True:
            
            #self.cap.release()
        #    print('self.cap.release()')
        
        #print('camera destroyAllWindows')
        #cv2.destroyAllWindows()	

        #print('camera terminate22')
        
        #for i in range(5):
        #    time.sleep(0.1)   
        
        #print('camera terminate33')



    def run(self):
        if self.fileName == 0:
            #릴리즈 시에 내부적으로 에러가 발생하는 크래쉬 테스트 (CAP_DSHOW 추가)
            self.cap = cv2.VideoCapture(self.fileName, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.fileName)

        if not self.cap.isOpened():
            print('Camera open failed!')
            #exit()

        net = cv2.dnn.readNet(self.model, self.config)

        if net.empty():
            print('Net open failed!')
            #exit()        

        categories = ['mask','none']
        print('len(categories) = ', len(categories))

        while self.Running:
            ret, frame = self.cap.read()
            if ret:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = img.shape

                blob = cv2.dnn.blobFromImage(img, 1, (300, 300), (104, 177, 123))
                net.setInput(blob)
                detect = net.forward()

                detect = detect[0, 0, :, :]

                #print('--------------------------')
                for i in range(detect.shape[0]):
                    confidence = detect[i, 2]
                    if confidence < 0.4:
                        break

                    x1 = int(detect[i, 3] * w)
                    y1 = int(detect[i, 4] * h)
                    x2 = int(detect[i, 5] * w)
                    y2 = int(detect[i, 6] * h)

                    margin = 0
                    face = img[y1-margin:y2+margin, x1-margin:x2+margin]

                    resize = cv2.resize(face, (self.width , self.height))

                    rgb_tensor = tf.convert_to_tensor(resize, dtype=tf.float32)
                    rgb_tensor /= 255.
                    rgb_tensor = tf.expand_dims(rgb_tensor , 0)

                    # 예측
                    predictions = self.probability_model.predict(rgb_tensor)

                    
                    #print(categories[predictions[i][1]], '  ' , np.argmax(predictions[i]))
                    #lebel = categories[predictions[i]]

                    if predictions[0][0] > predictions[0][1]:# and predictions[0][0] > 0.7:
                        label = 'Mask ' + str(predictions[0][0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0))
                        cv2.putText(frame, label, (x1, y1 - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
                    
                    if predictions[0][0] < predictions[0][1]:# and predictions[0][1] > 0.7:
                        label = 'No Mask ' + str(predictions[0][1])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255))
                        cv2.putText(frame, label, (x1, y1 - 1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

                    #print(predictions[0][0], '   ', predictions[0][1])

                #cv2.imshow('frame', frame)        

                frame = cv2.resize(frame, dsize=(640,480))
                h, w, ch = frame.shape
                bytesPerLine = ch * w            
                convertToQtFormat = QImage(frame.data, w, h, bytesPerLine, QImage.Format_BGR888)
                #p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(convertToQtFormat)
                #self.changePixmap.emit(p)

                if cv2.waitKey(30) == 27:
                    break

            else:
                print('error : ', ret)
                #동영상 실행이 끝났을때 처리
                self.Running = False

        try:
            self.cap.release()
            cv2.destroyAllWindows()	                 
            print('cap release')
        except:
            print('except:')





if __name__ == "__main__": 
    myWindow = CameraThread() 
    myWindow.run() 