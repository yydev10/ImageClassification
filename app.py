from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

import tensorflow as tf
from keras.models import load_model
import cv2 , os, glob
import numpy as np

from DB import Database
from ColorExt import ColorExt
from Upload import Upload
from MetaImage import MetaImage

import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'img/'

CORS(app, resources={r"/api/*": {"origins": "*"}})

# TODO : 카테고리 파일 db 연결하기
file = open('category.text','r') 
class_name = [f.strip('\n') for f in file.readlines()]
file.close()

image_meta = {}
my_database_class = Database()

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
# mysql 쿼리에 이미지 정보 저장
def save_db(uuid,result):
    if result['datetime'] == '' :
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_location,image_width,image_height,wallpaper_yn) \
            VALUES('%s','%s','%s','%d','%d','%s')" % (uuid,result['remote'],result['address'],result['width'],result['height'],result['wallpaper'])
    elif result['address'] == '' :
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_date,image_width,image_height,wallpaper_yn) \
            VALUES('%s','%s','%s','%d','%d','%s')" % (uuid,result['remote'],result['datetime'],result['width'],result['height'],result['wallpaper'])
    elif result['address'] == '' and result['datetime'] == '':
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_width,image_height,wallpaper_yn) \
            VALUES('%s','%s','%d','%d','%s')" % (uuid,result['remote'],result['width'],result['height'],result['wallpaper'])
    else :
        sql = "INSERT INTO capstonedb.ImageInfo(uid,image_url,image_date,image_location,image_width,image_height,wallpaper_yn) \
            VALUES('%s','%s','%s','%s','%d','%d','%s')" % (uuid,result['remote'],result['datetime'],result['address'],result['width'],result['height'],result['wallpaper'])
    
    print(sql)

    my_database_class.execute(sql)
    my_database_class.commit()

# db에 카테고리
def save_category(image_id,result):
    print(result)
    category = "INSERT INTO capstonedb.ImageCategory(category_name,image_id) VALUES('%s','%d')" % (result,int(image_id))
    
    my_database_class.execute(category)
    my_database_class.commit()
        
# db에 컬러 이미지 저장
def save_color(image_id,result):
    param_list = []
    for p in result:
        item = [image_id, p['r'],p['g'],p['b'],p['type']]
        t = tuple(item)
        param_list.append(t)

    print(param_list)

    sql = "INSERT INTO `capstonedb`.`Palette` VALUES(%s,%s,%s,%s,%s)"
    my_database_class.executeMany(sql,param_list)
    my_database_class.commit()

# image_id 반환
def get_image_id(image_url):
    sql = "SELECT id FROM ImageInfo WHERE image_url='%s'" % (image_url)
    print(sql)
    image_id = my_database_class.executeOne(sql)
    return image_id['id']

# 배경화면 비율(16:9) 계산
def get_aspect_ratio(width,height):
    cal = round((width * 9) / 16)
    print(cal)

    if cal == height+1 or cal == height-1:
        return 'Y';
    else:
        return 'N';

# 파일 업로드 후 카테고리 json로 리턴
@app.route('/api/image_upload',methods=['POST'])
def image_upload():
    # 파일 업로드 후 
    uuid = request.form['uid'] 
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
        img_upload = Upload(image_list[i]).upload_cloudinary()
        if img_upload == "error":
            result1 = {'code' : '401', 'message': 'error', 'result' : '서버에 이미지 업로드를 실패했습니다.'}
        else:
            r = result[i]
            r['remote'] = img_upload["secure_url"]

        # 메타데이터 추출
        print(image_list[i])
        image_meta = MetaImage(image_list[i]).get_meta_info() # get_meta_info(image_list[i])
        print(image_meta)
        
        r['width'] = image_meta["width"]
        r['height'] = image_meta["height"]
        r['datetime'] = image_meta["datetime"]
        r['address'] = image_meta["address"]

        # 이미지 색상 추출
        color_ext = ColorExt(image_list[i])
        r['color']= color_ext.get_color(3)

        # 배경화면 추천
        r['wallpaper'] = get_aspect_ratio(r['width'], r['height'])
        
    # 이미지 카테고리 분류
    r = image_classification(image_list, r)

    for i in range(len(image_list)):
        # db 저장
        print(result[i])
        save_db(uuid,result[i])

        # image_url로 image_id 반환
        image_id = get_image_id(result[i]['remote'])

        # 색상 저장
        save_color(image_id,result[i]['color'])

        # 카테고리 저장
        save_category(image_id,result[i]['prediction'])

        # 분석 끝난 이미지 삭제
        os.remove(image_list[i])

    result1 = {'code' : '201', 'message': '', 'result' : '이미지 등록 완료'}
    return json.dumps(result1)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
