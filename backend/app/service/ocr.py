import io
import re
from PIL import Image

import pytesseract

from backend.app.model.uploaded_image import UploadedImage


def recognize_from_image(image_data):
    im = Image.open(io.BytesIO(image_data))
    letters = pytesseract.image_to_string(im)
    pattern = re.compile(r'[a-zA-Z]')
    res = list()
    if letters:
        for letter in letters:
            if pattern.match(letter):
                res.append(letter)
    return res


def recognize_from_image_path(file_path):
    image = Image.open(file_path)
    return recognize_from_image(image)


def save_image_to_database(user_id, images):
    image = UploadedImage.add(user_id=user_id, image=images[0])
    return image


def get_records(user_id, page, page_size):
    ids = UploadedImage.gets_by_user_id(user_id=user_id, page=page, page_size=page_size)
    return UploadedImage.gets(ids)
