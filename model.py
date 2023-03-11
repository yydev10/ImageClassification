import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, GlobalAveragePooling2D
from tensorflow.keras.applications import Xception
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from datetime import datetime
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import numpy as np
import cv2
import glob
import matplotlib.pyplot as plt

IMG_WIDTH = 224
IMG_HEIGHT = 224

bese_model = Xception(weights='imagenet', include_top=False, input_shape=(IMG_WIDTH,IMG_HEIGHT,3))
#bese_model.summary()

model = Sequential()

model.add(bese_model)
#model.add(Flatten())
model.add(GlobalAveragePooling2D())

# 새로운 분류기
model.add(Dense(16,activation='relu'))
model.add(Dropout(0.25))
model.add(Dense(2,activation='softmax')) # 답 2개이므로 출력층 노드 2개

#model.compile(loss='sparse_categorical_crossentropy',
#            optimizer=tf.keras.optimizers.Adam(),
#            metrics=['accuracy'])

model.summary()

train_dir = 'cats_and_dogs_filtered/train'
test_dir = 'cats_and_dogs_filtered/validation'

#이미지 읽어올 때 자동 정규화
train_data_gen = ImageDataGenerator(rescale=1./255,
                                    rotation_range=10, width_shift_range=0.1,
                                    height_shift_range=0.1,shear_range=0.1,zoom_range=0.1)

test_data_gen = ImageDataGenerator(rescale=1./255)

train_data = train_data_gen.flow_from_directory(train_dir, batch_size = 32,
                                                color_mode='rgb', shuffle = True, class_mode = 'categorical',
                                                target_size=(IMG_WIDTH,IMG_HEIGHT))
test_data = test_data_gen.flow_from_directory(test_dir,batch_size = 32,
                                              color_mode='rgb', shuffle=True,class_mode='categorical',
                                              target_size=(IMG_WIDTH,IMG_HEIGHT))

model.compile(loss='categorical_crossentropy',optimizer=tf.keras.optimizers.Adam(2e-5),metrics=['accuracy'])

save_file_name = './cats_and_dogs_filtered_Xception_Colab.h5'

checkpoint = ModelCheckpoint(save_file_name,monitor='val_loss',
                             verbose=1, save_best_only=True,mode ='auto')

earlystopping = EarlyStopping(monitor='val_loss',patience=5)

hist = model.fit(train_data,epochs=30, validation_data = test_data, callbacks=[checkpoint,earlystopping])

### 학습 끝

test_imge_list = []
test_image_name_list = glob.glob('test_image_dir/*')

for i in range(len(test_image_name_list)):
    src_img = cv2.imread(test_image_name_list[i],cv2.IMREAD_COLOR)
    src_img = cv2.resize(src_img, dsize=(IMG_WIDTH,IMG_HEIGHT))

    dst_img = cv2.cvtColor(src_img,cv2.COLOR_BGR2RGB)
    dst_img = dst_img / 255.0

    test_imge_list.append(dst_img)

pred = model.predict(np.array(test_imge_list))

class_name = ['cat','dog']

plt.figure(figsize=(8,6))

for i in range(len(pred)):
    plt.subplot(4,4,i+1)
    prediction = str(class_name[np.argmax(pred[i])])
    probility = '{0:0.2f}'.format(100*max(pred[i]))
    title_str = prediction+" . "+probility+'%'
    print(title_str)
    plt.axis('off')
    plt.title(title_str)
    plt.imshow(test_imge_list[i])

plt.show()