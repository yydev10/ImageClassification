import multiprocessing
from Upload import Upload

class WorkProcess():
    
    # 이미지 업로드
    def upload(self,image,result):
        item = {}
        item['image_name'] = image
        
        remote_path = Upload(image).upload_cloudinary()
        if remote_path == 'error image upload':
            return remote_path
        
        item['remote'] = remote_path['url']
        print(item)
        result.append(item)

    # 멀티프로세스 이미지 업로드 함수
    def multi_upload(self,image_list):
        manager = multiprocessing.Manager()
        result = manager.list()

        jobs = []
        # 멀티 프로세싱을 사용해 병렬처리
        for i in range(len(image_list)):
            process = multiprocessing.Process(target=self.upload, args=(image_list[i],result))
            jobs.append(process)
            process.start()
        
        # 프로세스 종료 대기
        for proc in jobs:
            proc.join()

        return result
