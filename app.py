from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

import tensorflow as tf
from keras.models import load_model
import cv2 , os, glob
import numpy as np

from exif import Image
from geopy.geocoders import Nominatim
import axios
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'img/'

# TODO : 카테고리 파일 db 연결하기
file = open('category.text','r') 
class_name = [f.strip('\n') for f in file.readlines()]
file.close()

image_meta = {}

def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == 'S' or ref == 'W':
        decimal_degrees = -decimal_degrees
    return decimal_degrees

# 이미지 위도 경도 -> 실제 주소로 변경
def image_gps(image):
    try:
        image.gps_longitude
        latitude = decimal_coords(image.gps_latitude,image.gps_latitude_ref)
        longitude = decimal_coords(image.gps_longitude,image.gps_longitude_ref)

        # 좌표 -> 주소 변환
        if latitude != 0.0 or longitude != 0.0:
            lat_lng_str  = "%f, %f" % (latitude,longitude)
            geolocoder = Nominatim(user_agent = 'South Korea', timeout=None)
            address = geolocoder.reverse(lat_lng_str)
            return address
        else :
            return ''
    except AttributeError:
        return 'error'

# 이미지 전처리 함수
def image_classification(filename):
    image = []
    img = cv2.imread(filename,cv2.IMREAD_COLOR)
    h,w,_ = img.shape # 이미지 넓이 구하기
    image_meta["height"] = h
    image_meta["width"] = w

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

    return (prediction, probility)

# 클라우디너리 서버에 이미지 업로드
async def upload_cloudnary_img(image):
    print("클라우디너리 서버에 이미지 업로드")
    url = 'https://api.cloudinary.com/v1_1/[cloud name]/image/upload'
    api_key = ''
    upload_preset = ''

    form_data = {
        'api_key': api_key,
        'upload_preset': '[remembered preset name]',
        'timestamp': int(datetime.now().timestamp()),
        'file': image
    }

    headers = {
        'Content-Type': 'multipart/form-data'
    }

    response = await axios.post(url, data=form_data, headers=headers)

    if not response:
        response = await axios.post(url, data=form_data, headers=headers) # 한번 더 재요청
        if not response:
            return 'error image upload'
    else :
        return response.data.url

# mysql 쿼리에 이미지 정보 저장

# 파일 업로드 후 카테고리 json로 리턴
@app.route('/image_upload',methods=['POST'])
def image_upload():
    file = request.files['file_list']
    
    filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(filename)

    #클라우디너리 서버에 이미지 업로드
    upload_cloudnary_img(file)

    #메타데이터 load
    with open(filename,"rb") as f:
        image_byte = f.read()
    image = Image(image_byte)

    # 메타데이터 추출
    if image.has_exif:
        image_meta["datetime"] = image.datetime # 촬영일자
        image_meta["address"] = image_gps(image) # 이미지 주소

    # 이미지 카테고리 분류
    prediction, probility = image_classification(filename)
    
    for k in image_meta:
        print(image_meta[k])

    result = {'image' : file.filename, 'prediction': prediction, 'probility': probility}
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
