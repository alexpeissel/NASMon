import yaml

class Page():
    def __init__(self, page_file):
        with open(page_file) as f:
            self.content = yaml.load(f, Loader=yaml.FullLoader)
        
