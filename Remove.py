# Set your Cloudinary credentials
# ==============================
import cloudinary.api
import cloudinary
from dotenv import load_dotenv
load_dotenv()

# Import the Cloudinary libraries
# ==============================

# config
config = cloudinary.config(secure=False)


class Remove():
    def __init__(self, img_list):
        self.img_list = img_list

    # 클클라우드 서버의 이미지 삭제
    def remove_cloudinary(self):
        print("클라우드 서버의 이미지 삭제")
        try:
            response = cloudinary.api.delete_resources(self.img_list)
            print(response)
            return response
        except:
            response = "error image remove"
            return response
