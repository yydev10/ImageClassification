from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

import tensorflow as tf
from keras.models import load_model
import cv2 , os, glob
import numpy as np

from exif import Image
from geopy.geocoders import Nominatim

from DB import Database

import json
import DB

# Set your Cloudinary credentials
# ==============================
from dotenv import load_dotenv
load_dotenv()

# Import the Cloudinary libraries
# ==============================
import cloudinary
import cloudinary.uploader
import cloudinary.api

# config
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'img/'
config = cloudinary.config(secure=True)

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
            return str(address)
        else :
            return ''
    except AttributeError:
        return 'error'

# 이미지 전처리 함수
def image_classification(image_list,r):
    image = []

    for i in range(len(image_list)):
        img = cv2.imread(image_list[i],cv2.IMREAD_COLOR)
        img = cv2.resize(img, dsize=(224,224))
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        img = img / 255.0
        image.append(img)

    #모델 load
    model = load_model('cats_and_dogs_filtered_Xception_Colab.h5')
    pred = model.predict(np.array(image))

    #예측 . 일치율% 형태로 출력
    for i in range(len(pred)):
        prediction = str(class_name[np.argmax(pred[i])])
        probility = '{0:0.2f}'.format(100*max(pred[i]))
        r['prediction'] = prediction
        r["probility"] = probility

    return r

# 클라우디너리 서버에 이미지 업로드
def upload_cloudnary_img(image):
    print("클라우디너리 서버에 이미지 업로드")
    response = cloudinary.uploader.upload(image)
    return response

# mysql 쿼리에 이미지 정보 저장
def save_db(result):
    sql = "INSERT INTO \
            capstonedb.ImageInfo(uid,image_url,image_date,image_location,image_width,image_height) \
            VALUES('%s','%s','%s','%s','%d','%d')\
            " % ('sdfsfsgsdsd',result['remote'],result['datetime'],result['address'],result['width'],result['height'])
    
    Database().execute(sql)
    Database().commit()

# 메타데이터 추출
def get_meta_info(file):
    #메타데이터 load
    with open(file,"rb") as f:
        image_byte = f.read()
    image = Image(image_byte)

    if image.has_exif:
        meta_list = image.list_all()
        if('datetime' in meta_list):
            image_meta["datetime"] = image.datetime # 촬영일자
        else :
            image_meta["datetime"] = ""
        if('gps_latitude' in meta_list):
            image_meta["address"] = image_gps(image) # 이미지 주소
        else :
            image_meta["address"] = ""
        print(image_meta)
    return image_meta

# 파일 업로드 후 카테고리 json로 리턴
@app.route('/image_upload',methods=['POST'])
def image_upload():
    # 파일 업로드 후 
    file_list = request.files.getlist("file_list")
    image_list = []
    result = []
    
    for file in file_list:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(filename)
        image_list.append(filename)

    for i in range(len(image_list)) :
        # 이미지 이름 저장
        result.append({'image_name': image_list[i]})

        #클라우디너리 서버에 이미지 업로드
        img_upload = upload_cloudnary_img(image_list[i])
        r = result[i]
        r['width'] = img_upload["width"]
        r['height'] = img_upload["height"]
        r['remote'] = img_upload["secure_url"]

        # 배경화면 추천 기준 -> 
        
        # 메타데이터 추출
        image_meta = get_meta_info(image_list[i])
        r['datetime'] = image_meta["datetime"]
        r['address'] = image_meta["address"]

    # 이미지 카테고리 분류
    r = image_classification(image_list, r)

    for i in range(len(image_list)):
        # db 저장
        print(result[i])
        save_db(result[i])
        # result_list.append({'image':file.replace('img/',''),
        #                 'remote' : img_upload["secure_url"],
        #                 'prediction' :image_meta["prediction"],
        #                 'probility':image_meta["probility"],
        #                 'datetime': image_meta["datetime"],
        #                 'address' : image_meta["address"],
        #                 'image_width' : img_upload["width"],
        #                 'image_height' : img_upload["height"]})
        
        # 분석 끝난 이미지 삭제
        os.remove(image_list[i])

    result1 = {'code' : '201', 'message': '', 'result' : result}
    return json.dumps(result1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
