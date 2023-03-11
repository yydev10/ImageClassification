import tensorflow as tf
import cv2 , os, glob
import numpy as np
import matplotlib.pyplot as plt
from keras.models import load_model
import random

IMG_WIDTH = 224
IMG_HEIGHT = 224

model = load_model('cats_and_dogs_filtered_Xception_Colab.h5')

class_names=['people','cat','dog']

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