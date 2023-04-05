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
config = cloudinary.config(secure=False)

class Upload():
    def __init__(self,img_url):
        self.img_url = img_url
    
    # 클라우드 서버에 이미지 업로든
    def upload_cloudinary(self):
        print("클라우드 서버로 이미지 업로드")
        try:
            response = cloudinary.uploader.upload(self.img_url) 
            print(response)
            return response
        except:
            response = "error image upload"
            return response