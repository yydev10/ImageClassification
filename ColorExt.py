from colorthief import ColorThief

class ColorExt():
    def __init__(self,img_url):
        self.ct = ColorThief(img_url)
    
    def get_color(self,count):
        result = []
        palette = self.ct.get_palette(color_count=count)

        for i in range(0,len(palette)):
            item = dict()
            if i == 0:
                item['type'] = 'dominant'
            else :
                item['type'] = 'nomal'
            (r,g,b) = palette[i]
            item['r'] = r
            item['g'] = g
            item['b'] = b
            result.append(item)
        
        return result
