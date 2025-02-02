import tensorflow as tf
from tensorflow import keras
from keras.callbacks import EarlyStopping
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from sklearn.model_selection import train_test_split

import numpy as np
import matplotlib.pyplot as plt

plt.style.use("seaborn-white")

import os
import shutil
from keras.preprocessing import image
import cv2

root_dir = os.path.dirname(os.path.abspath("README.md"))

face_model = (
    root_dir + "/resource/opencv_library/res10_300x300_ssd_iter_140000_fp16.caffemodel"
)
face_config = root_dir + "/resource/opencv_library/deploy.prototxt"
img_withmask_dir = root_dir + "/dataset/with_mask"
img_witouthmask_dir = root_dir + "/dataset/without_mask"
def_target_size_x = 64
def_target_size_y = 64

net = cv2.dnn.readNet(face_model, face_config)

x = []
y = []
test_x = []

print(tf.__version__)


def preprocess_img(img_path, y_Data, isTestMe=False):
    # img = image.load_img(img_path, target_size=(def_target_size, def_target_size))
    # img = image.load_img(img_path, grayscale=True, target_size=(def_target_size, def_target_size))

    # plt.imshow(img, cmap=plt.cm.binary)
    # plt.show()

    # print(img_path)

    img = cv2.imread(img_path, flags=cv2.IMREAD_UNCHANGED)
    img = cv2.cvtColor(img, code=cv2.COLOR_BGR2RGB)

    blob = cv2.dnn.blobFromImage(img, 1, (300, 300), (104, 177, 123))
    net.setInput(blob)
    detect = net.forward()

    detect = detect[0, 0, :, :]
    (h, w) = img.shape[:2]

    face = []

    for i in range(detect.shape[0]):
        confidence = detect[i, 2]
        if confidence < 0.6:
            break

        x1 = int(detect[i, 3] * w)
        y1 = int(detect[i, 4] * h)
        x2 = int(detect[i, 5] * w)
        y2 = int(detect[i, 6] * h)

        # cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0))

        face = img[y1:y2, x1:x2]

        face = cv2.resize(face, dsize=(def_target_size_x, def_target_size_y))

        # width, height, channel = face.shape
        # print(x1, y1, x2, y2, width, height)
        # img[0:width, 0:height] = face

        # print(face.shape)
        # plt.imshow(face, cmap=plt.cm.binary)
        # plt.show()

        rgb_tensor = tf.convert_to_tensor(face, dtype=tf.float32)
        rgb_tensor /= 255.0

        if isTestMe == False:
            x.append(rgb_tensor)
            y.append(y_Data)
        else:
            test_x.append(rgb_tensor)


for i in os.listdir(img_withmask_dir):
    img_path = os.path.join(img_withmask_dir, i)
    img_tensor = preprocess_img(img_path, 0)


for i in os.listdir(img_witouthmask_dir):
    img_path = os.path.join(img_witouthmask_dir, i)
    img_tensor = preprocess_img(img_path, 1)

categories = ["mask", "none"]
print("len(categories) = ", len(categories))

x = np.array(x)
print(x.shape)
y = np.array(y)
print(y.shape)

X_train, X_test, Y_train, Y_test = train_test_split(x, y, test_size=0.1)

# 내사진 테스트
# test_x.clear()
# img_test_me_dir = './AI_Mask_Detector/train/test_me'
# for i in os.listdir(img_test_me_dir):
#     img_path = os.path.join(img_test_me_dir, i)
#     img_tensor = preprocess_img(img_path, 0, True)

# X_test = np.array(test_x)
# print('X_test2 shape : ', X_test.shape)


Y_train = keras.utils.to_categorical(Y_train, 2)
Y_test = keras.utils.to_categorical(Y_test, 2)

print("X_train shape : ", X_train.shape)
print("Y_train shape : ", Y_train.shape)

print("X_test shape : ", X_test.shape)
print("Y_test shape : ", Y_test.shape)

# 학습데이터 회전
train_datagen = ImageDataGenerator(
    # rescale=1./255,
    rotation_range=30,
    shear_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True,
    fill_mode="nearest",
)

train_generator = train_datagen.flow(x=X_train, y=Y_train, batch_size=32, shuffle=True)

val_generator = train_datagen.flow(x=X_test, y=Y_test, batch_size=32, shuffle=True)

# 이미지 확인
# augs = train_generator.__getitem__(8)
# plt.figure(figsize=(16, 8))
# for i, img in enumerate(augs[0]):
#     plt.subplot(4, 8, i+1)
#     #plt.title('%.2f' % augs[1][i])
#     plt.axis('off')
#     img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#     plt.imshow(img.squeeze())
# plt.show()

model = keras.models.Sequential()
model.add(
    keras.layers.Conv2D(
        32,
        kernel_size=(3, 3),
        activation="relu",
        input_shape=(def_target_size_x, def_target_size_y, 3),
    )
)
model.add(keras.layers.MaxPooling2D(2, 2))
model.add(keras.layers.Dropout(rate=0.25))
model.add(keras.layers.Conv2D(32, kernel_size=(3, 3), activation="relu"))
model.add(keras.layers.MaxPooling2D(2, 2))
model.add(keras.layers.Dropout(rate=0.25))
model.add(keras.layers.Conv2D(32, kernel_size=(3, 3), activation="relu"))
model.add(keras.layers.MaxPooling2D(2, 2))
model.add(keras.layers.Dropout(rate=0.25))
model.add(keras.layers.Flatten())
model.add(keras.layers.Dense(128, activation="relu"))
model.add(keras.layers.Dense(2, activation="softmax"))

print(model.summary())

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

Early_stopping_callback = EarlyStopping(
    monitor="val_loss", mode="min", verbose=1, patience=3
)

# model.fit(X_train, Y_train, epochs=100, validation_split=0.1, callbacks=[Early_stopping_callback])
# model.fit(X_train, Y_train, epochs=3, validation_split=0.1)
model.fit_generator(
    train_generator,
    epochs=100,
    validation_data=val_generator,
    callbacks=[Early_stopping_callback],
)

model.save(root_dir + "/model.h5")

# 예측
predictions = model.predict(X_test)

test_loss, test_acc = model.evaluate(X_test, Y_test, verbose=2)
print("\n테스트 정확도:", test_acc)


# 이미지 시각화 에러처리
roofCnt = 8 * 10
if len(X_test) < roofCnt:
    roofCnt = len(X_test)

# #이미지 시각화
plt.figure(figsize=(10, 10))
for i in range(roofCnt):
    plt.subplot(8, 10, i + 1)
    plt.xticks([])
    plt.yticks([])
    plt.grid(False)
    plt.imshow(X_test[i], cmap=plt.cm.binary)

    # print(predictions[i])
    # print(categories[predictions[i]])
    # print(str(round(np.argmax(predictions[i]),2)))
    # print(categories[predictions[i]], '  ' , np.argmax(predictions[i]))

    if predictions[i][0] > predictions[i][1]:
        label = "Mask " + str(round(predictions[i][0], 2))
    else:
        label = "No " + str(round(predictions[i][1], 2))

    plt.xlabel(label)
    # plt.xlabel(categories[Y_train[i]])
plt.show()
