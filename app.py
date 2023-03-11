from flask import Flask, flash, request, jsonify
from werkzeug.utils import secure_filename

import tensorflow as tf
from keras.models import load_model
import cv2 , os, glob
import numpy as np


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'img/'

# TODO : 카테고리 파일 db 연결하기
file = open('category.text','r') 
class_name = [f.strip('\n') for f in file.readlines()]
file.close()

print(class_name)

# 파일 업로드 후 카테고리 json로 리턴
@app.route('/image_upload',methods=['POST'])
def image_classification():
    file = request.files['file']

    filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(filename)

    #이미지 전처리
    image = []
    img = cv2.imread(filename,cv2.IMREAD_COLOR)
    img = cv2.resize(img, dsize=(224,224))
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    img = img / 255.0
    image.append(img)

    #모델 load
    model = load_model('cats_and_dogs_filtered_Xception_Colab.h5')
    pred = model.predict(np.array(image))

    #예측 . 일치율% 형태로 출력
    prediction = str(class_name[np.argmax(pred[0])])
    probility = '{0:0.2f}'.format(100*max(pred[0]))

    # 검증한 이미지 삭제
    os.remove(filename)
    
    result = {'image' : file.filename, 'prediction': prediction, 'probility': probility}
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
