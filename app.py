from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

import tensorflow as tf
from keras.models import load_model
import cv2
import os
import glob
import numpy as np

from DB import Database
from ColorExt import ColorExt
from WorkProcess import WorkProcess
from MetaImage import MetaImage

import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'img/'

CORS(app, resources={r"/api/*": {"origins": "*"}})

# TODO : 카테고리 파일 db 연결하기
file = open('category.text', 'r', encoding='UTF8')
class_name = [f.strip('\n') for f in file.readlines()]
file.close()

image_meta = {}
my_database_class = Database()

# 이미지 허용가능한 확장자
img_ext = ['jpg', 'jpeg', 'JPG', 'png', 'bmp']

# 이미지 전처리 함수


def image_classification(image_list):
    image = []
    image_predict = []

    for i in range(len(image_list)):
        img = cv2.imread(image_list[i], cv2.IMREAD_COLOR)
        img = cv2.resize(img, dsize=(224, 224))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img / 255.0
        image.append(img)

    # 모델 load
    model = load_model(
        'cats_and_dogs_filtered_Xception_Colab.h5', compile=False)
    pred = model.predict(np.array(image))

    # 예측 . 일치율% 형태로 출력
    for i in range(len(pred)):
        prediction = str(class_name[np.argmax(pred[i])])
        probility = '{0:0.2f}'.format(100*max(pred[i]))
        # r['prediction'] = prediction
        # r["probility"] = probility
        image_predict.append(prediction)

    return image_predict

# mysql 쿼리에 이미지 정보 저장


def save_db(uuid, result, story_yn):
    if "datetime" not in result:
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_location,image_width,image_height,wallpaper_yn,story_yn) \
            VALUES('%s','%s','%s','%d','%d','%s','%c')" % (uuid, result['remote'], result['address'], result['width'], result['height'], result['wallpaper'], story_yn)
    elif "address" not in result:
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_date,image_width,image_height,wallpaper_yn,story_yn) \
            VALUES('%s','%s','%s','%d','%d','%s','%c')" % (uuid, result['remote'], result['datetime'], result['width'], result['height'], result['wallpaper'], story_yn)
    elif "address" not in result and "datetime" not in result:
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_width,image_height,wallpaper_yn,story_yn) \
            VALUES('%s','%s','%d','%d','%s','%c')" % (uuid, result['remote'], result['width'], result['height'], result['wallpaper'], story_yn)
    else:
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_date,image_location,image_width,image_height,wallpaper_yn,story_yn) \
            VALUES('%s','%s','%s','%s','%d','%d','%s','%c')" % (uuid, result['remote'], result['datetime'], result['address'], result['width'], result['height'], result['wallpaper'], story_yn)

    print(sql)

    my_database_class.execute(sql)
    my_database_class.commit()

# db에 카테고리


def save_category(image_id, result):
    print(result)
    category = "INSERT INTO capstonedb.ImageCategory(category_name,image_id) VALUES('%s','%d')" % (
        result, int(image_id))

    my_database_class.execute(category)
    my_database_class.commit()

# db에 컬러 이미지 저장


def save_color(image_id, result):
    param_list = []
    for p in result:
        item = [image_id, p['r'], p['g'], p['b'], p['type']]
        t = tuple(item)
        param_list.append(t)

    print(param_list)

    sql = "INSERT INTO `capstonedb`.`Palette` VALUES(%s,%s,%s,%s,%s)"
    my_database_class.executeMany(sql, param_list)
    my_database_class.commit()

# image_id 반환


def get_image_id(image_url):
    sql = "SELECT id FROM ImageInfo WHERE image_url='%s'" % (image_url)
    print(sql)
    image_id = my_database_class.executeOne(sql)
    return image_id['id']

# 배경화면 추천 로직


def get_aspect_ratio(width, height, category_list):
    category = category_list[0]
    minRatio = 1.2
    maxRatio = 1.8

    ratio = round(width / height, 3)

    if ratio >= minRatio and ratio <= maxRatio and width >= 800 and (category == "바다" or category == "산" or category == "강아지" or category == "고양이"):
        return 'Y'
    else:
        return 'N'

# 파일 업로드 후 카테고리 json로 리턴


@app.route('/api/image_upload', methods=['POST'])
def image_upload():
    print('파일 업로드 start')
    # 파일 업로드 후
    uuid = request.form['uid']
    file_list = request.files.getlist("file_list")
    # Y : story에 올리는 이미지 , N : story에 올리지 않는 이미지
    story_yn = request.form['story_yn']

    image_list = []
    result = []

    print(file_list)

    for file in file_list:
        ext = file.filename.split('.')[1]
        if ext not in img_ext:
            return {'code': '402', 'message': 'error', 'result': '지원하지 않는 이미지 확장자 입니다.\njpg, png, bmp 확장자만 지원합니다'}

        filename = os.path.join(
            app.config['UPLOAD_FOLDER'], file.filename)
        print(filename)
        file.save(filename)
        image_list.append(filename)

    # 한번에 이미지 업로드 후 결과값 리턴
    data = WorkProcess().multi_upload(image_list)
    print(data)

    if "error image upload" in data:
        return {'code': '401', 'message': 'error', 'result': '서버에 이미지 업로드를 실패했습니다.'}

    image_list = []
    for i in range(len(data)):
        print(data[i])

        data_dic = data[i]
        image_name = []
        print(data_dic.get('image_name'))

        # 메타데이터 추출
        image_meta = MetaImage(data_dic.get('image_name')).get_meta_info()
        print(image_meta)

        if image_meta is not None:
            data_dic['width'] = image_meta["width"]
            data_dic['height'] = image_meta["height"]
            data_dic['datetime'] = image_meta["datetime"]
            if "address" in image_meta:
                data_dic['address'] = image_meta["address"]

        # 이미지 색상 추출
        color_ext = ColorExt(data_dic.get('image_name'))
        data_dic['color'] = color_ext.get_color(3)

        # 배경화면 추천
        image_name.append(data_dic.get('image_name'))
        category = image_classification(image_name)
        data_dic['wallpaper'] = get_aspect_ratio(
            data_dic['width'], data_dic['height'], category)

        # 딕셔너리 추가
        image_list.append(data_dic.get('image_name'))
        result.append(data_dic)

    # 이미지 카테고리 분류
    image_class = image_classification(image_list)

    for i in range(len(result)):

        # db 저장
        save_db(uuid, result[i], story_yn)

        # image_url로 image_id 반환
        image_id = get_image_id(result[i].get('remote'))

        # 색상 저장
        save_color(image_id, result[i].get('color'))

        # 카테고리 저장
        save_category(image_id, image_class[i])

        # 분석 끝난 이미지 삭제
        try:
            os.remove(result[i].get('image_name'))
        except:
            result_msg = {'code': '403', 'message': '',
                          'result': '이미지 처리에 오류가 발생했습니다.'}
            json.dumps(result_msg)

    result1 = {'code': '201', 'message': '', 'result': '이미지 등록 완료'}
    return json.dumps(result1)


@app.route('/api/image_Remove', methods=['POST'])
def image_remove():
    url_list = request.json['img_url']

    result = WorkProcess().remove(url_list)

    if "error image upload" in result:
        return {'code': '401', 'message': 'error', 'result': '서버에 이미지 업로드를 실패했습니다.'}
    else:
        return {'code': '201', 'message': '', 'result': 'cloudinary 삭제 완료'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)
