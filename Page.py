import yaml
class Page():
    def __init__(self, page_file):
        with open(page_file) as f:
            parsed_page = yaml.load(f, Loader=yaml.FullLoader)
        
        self.name = parsed_page.get("name", "NASMon Page")
        self.commands = parsed_page.get("commands", [])
        self.text = parsed_page.get("text", [])
        self.images = parsed_page.get("images", [])
        self.bargraph = parsed_page.get("bargraph", [])

