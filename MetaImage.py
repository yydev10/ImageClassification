from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from geopy.geocoders import Nominatim
from geopy.point import Point
import pillow_heif
from datetime import datetime

class MetaImage():
    def __init__(self,img):
        self.img = img
    
    def convert_gps_to_decimal(gps_coordinate):
        if gps_coordinate is None:
            return None
        degrees = gps_coordinate[0]
        minutes = gps_coordinate[1]
        seconds = gps_coordinate[2]
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        return decimal
    
    def convert_gps_to_address(self,gps_info):
        latitude = gps_info.get("GPSLatitude")
        longitude = gps_info.get("GPSLongitude")
        if latitude is None or longitude is None:
            return None
        else:
            lat_dec = self.convert_gps_to_decimal(latitude)
            lon_dec = self.convert_gps_to_decimal(longitude)

            locator = Nominatim(user_agent = 'South Korea',timeout=None)
            location = locator.reverse(Point(lat_dec, lon_dec))
            return location.address

    # pillow 라이브러리로 메타 정보 얻기
    def get_meta_info(self):
        image_meta = dict()
        try:
            with Image.open(self.img) as image:
                size = image.size
                width = size[0]
                height = size[1]

                image_meta['width'] = width
                image_meta['height'] = height

                exif_data = image._getexif()
                print(exif_data)
                if exif_data:
                    exif_data_dict = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == "GPSInfo":
                            gps_data = {}
                            for gps_tag_id in value:
                                gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                                if gps_tag == 'GPSLatitude' or gps_tag =='GPSLongitude':
                                    gps_data[gps_tag] = value[gps_tag_id]
                                    exif_data_dict[tag] = gps_data
                        else:
                            exif_data_dict[tag] = value
            
                    if "GPSInfo" in exif_data_dict:
                        address = self.convert_gps_to_address(exif_data_dict['GPSInfo'])
                    else:
                        address = None
         
                    if 'DateTimeOriginal' in exif_data_dict:
                        date_taken = exif_data_dict['DateTimeOriginal']
                    elif 'DateTime' in exif_data_dict:
                        date_taken = exif_data_dict['DateTime']
                    elif 306 in exif_data_dict:
                        date_taken = exif_data_dict[306]
                    else:
                        date_taken = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    image_meta['address'] = '' if address is None else address
                    image_meta['datetime'] = '' if date_taken is None else date_taken

                    return image_meta
                else:
                    image_meta['datatime'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    return image_meta
        except IOError:
            return None

if __name__ == '__main__':
    heic = "test/IMG_0349.HEIC"
    meta = MetaImage(heic).convert_heic_to_jpg()
    print(meta)
