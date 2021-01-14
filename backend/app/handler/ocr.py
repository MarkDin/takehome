from .base_handler import BaseHandler, route, need_auth, json_serialize, JsonError, IMG_TYPES
from ..service import ocr
from functools import partial
from ..model.uploaded_image import User, UploadedImage
import random

GENERATE_SALT_CHARACTERS = "12345676890abcdefghijkmnlopqrstuvwxyz"


@route(r'/test')
class TestHandler(BaseHandler):
    @json_serialize
    def post(self):
        return {"dk": "hello"}

    @json_serialize
    def get(self):
        return {"hello": "world!"}


@route(r'/ocr/upload')
class OCRHandler(BaseHandler):

    def upload_images(self, deal_func) -> UploadedImage:
        max_size = 5242880  # TODO move to  configure file
        # 获取上传文件
        try:
            file_metas = self.request.files['file']  # 提取表单中‘name’为‘file’的文件元数据
        except Exception:
            raise JsonError(400, u'没有上传文件')

        images = []
        for meta in file_metas:
            content_type = meta['content_type']
            if content_type not in IMG_TYPES:
                print(content_type)
                raise JsonError(406, '不支持的文件类型')
            elif not meta['filename']:
                raise JsonError(400, '没有上传图片')
            elif content_type != 'image/gif' and len(meta['body']) > max_size:
                raise JsonError(406, '请上传小于%skb的图片' % (max_size / 1024))
            else:
                images.append(meta['body'])
        return deal_func(images=images)

    @json_serialize
    @need_auth
    def post(self):
        user_id = self.get_argument("id", None)
        if not user_id:
            raise JsonError(404, "参数错误")
        image = self.upload_images(partial(ocr.save_image_to_database, user_id=user_id))
        image_data = image.image
        letters = ocr.recognize_from_image(image_data)
        image.update(image.id, letters="".join(letters))
        return {
            "letters": letters
        }

    @json_serialize
    @need_auth
    def get(self):
        page = self.get_int("page")
        page_size = self.get_int("page_size")
        user_id = self.get_argument("id")
        records = ocr.get_records(user_id, page, page_size)
        return [record.to_dict() for record in records]


@route(r'/orc/register')
class AuthHandler(BaseHandler):

    @json_serialize
    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")
        salt = random.choices(GENERATE_SALT_CHARACTERS, k=6)
        password = hash(password + salt)
        user = User.add(username=username, password=password, salt=salt)
        return {
            "user": user
        }
