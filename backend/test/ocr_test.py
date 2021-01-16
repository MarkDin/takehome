import json
import os
import sys
import unittest

from urllib import parse

root_path = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.append(root_path)
import requests
from backend.app.service import ocr
from tornado.httpclient import HTTPClient, HTTPClientError
from functools import partial
from backend import settings


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.client = HTTPClient()

    def test_request(self):
        host = "http://" + settings.HOST + ":" + str(settings.PORT)
        url = host + "/api/ocr/upload"
        print(url)
        test_func = partial(
            self.client.fetch,
            request=url,
            method='POST',
            body=parse.quote(json.dumps({
                "username": "ddd",
                "password": "1234"
            }))
        )
        self.assertRaises(HTTPClientError, test_func)

    def test_ocr(self):
        res = ['f', 'r', 'o', 'm', 'P', 'I', 'L', 'i', 'm', 'p', 'o', 'r', 't', 'I', 'm', 'a', 'g', 'e', 'i', 'm', 'p',
               'o', 'r', 't', 'p', 'y', 't', 'e', 's', 's', 'e', 'r', 'a', 'c', 't']
        image_url = 'http://img-blog.csdnimg.cn/2019052911203398.png'
        resposne = requests.get(image_url)
        letters = ocr.recognize_from_image(resposne.content)
        self.assertIsNotNone(letters)
        self.assertListEqual(letters, res)


if __name__ == '__main__':
    unittest.main()
