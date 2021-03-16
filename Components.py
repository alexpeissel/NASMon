import chevron
import json
import requests

from PIL import Image
from urllib.parse import urlparse
from io import BytesIO

from loguru import logger


class BaseComponent():
    def __init__(self, component_definition):
        self.component_definition = json.dumps(component_definition)

    def _transform(self, rendered):
        return rendered

    def render(self, template_vars):
        rendered = chevron.render(self.component_definition, template_vars)
        rendered_dict = json.loads(rendered)
        transformed = self._transform(**rendered_dict)
        return transformed

class CommandComponent(BaseComponent):
    pass

class TextComponent(BaseComponent):
    def _transform(self, text=None, x=None, y=None, size=None):
        return {
            "text_bytes": bytes(text, "utf-8"),
            "x": x,
            "y": y,
            "size": size
        }


class ImageComponent(BaseComponent):
    MAX_SIZE = 128, 32

    def __init__(self, component_definition):
        loaded_image = self._load_image(component_definition.get("image"))
        loaded_image.thumbnail(self.MAX_SIZE, Image.ANTIALIAS)
        self.image = loaded_image.convert("1")
        super().__init__(component_definition)

    def _load_image(self, image_location):
        try:
            url = urlparse(image_location)

            if url.scheme:
                logger.debug(f"Downloading image from URL: {image_location}")
                response = requests.get(image_location, allow_redirects=True)
                return Image.open(BytesIO(response.content))
            else:
                logger.debug(f"Loading image from file: {image_location}")
                return Image.open(image_location)
        except Exception as e:
            logger.error(f"Loading image threw exception: {e}")

    def _transform(self, image=None, x=None, y=None, width=None, height=None, rotation=None):
        if not width:
            width = self.image.size[0]
        if not height:
            height = self.image.size[1]
        if x is None:
            x = round((128 / 2) - self.image.size[0] / 2)
        if y is None:
            y = 0

        return {
            "bmp_bytes": self.image.tobytes(),
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }


class BargraphComponent(BaseComponent):
    BARGRAPH_LENGTH=23
    PERCENT = 100.0 / BARGRAPH_LENGTH

    def _transform(self, value=None, green_threshold=0,  yellow_threshold=50,  red_threshold=75):
        # Create the initial list
        bargraph_data = ["o"] * self.BARGRAPH_LENGTH

        for i in range(0, len(bargraph_data)):
            if int(float(value)) > ((i + 1) * self.PERCENT):
                if (i + 1) * (100.0 / self.BARGRAPH_LENGTH) >= int(red_threshold):
                    bargraph_data[i] = 'r'
                elif (i + 1) * (100.0 / self.BARGRAPH_LENGTH) >= int(yellow_threshold):
                    bargraph_data[i] = 'y'
                elif (i + 1) * (100.0 / self.BARGRAPH_LENGTH) >= int(green_threshold):
                    bargraph_data[i] = 'g'
                else:
                    bargraph_data[i] = 'o'
        
        return {
            "graph_bytes": bytes("".join(bargraph_data), "utf-8")
        }
