# -*- coding: utf-8 -*-

import base64
import hmac
from hashlib import sha1, md5
import requests
import time
from typing import Dict
from urllib.parse import quote
from xml.etree import ElementTree

from abstract_oss import OSSBucket


class AliyunOSSBucket(OSSBucket):
    def __init__(self, config: Dict[str, str]):
        self.host = config.get('host')
        self.bucket = config.get('bucket')
        self.access_key_id = config.get('access_key_id')
        self.access_key_secret = config.get('access_key_secret')

        if not self.host or not self.bucket or not self.access_key_id or not self.access_key_secret:
            raise TypeError('缺少必要的初始化参数')

    def make_auth(self, auth_info: dict) -> str:
        """计算签名

        Args:
            auth_info: 与签名相关的信息

        Returns:
            签名结果
        """
        verb = auth_info.get('verb')
        content_md5 = auth_info.get('content-md5') if auth_info.get('content-md5') else ''
        content_type = auth_info.get('content-type') if auth_info.get('content-type') else ''
        date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        canonicalized_oss_headers = (
            auth_info.get('canonicalized_oss_headers')
            if auth_info.get('canonicalized_oss_headers')
            else ''
        )
        canonicalized_resource = (
            auth_info.get('canonicalized_resource')
            if auth_info.get('canonicalized_resource')
            else '/' + self.bucket + '/'
        )

        string_to_sign = (
            f'{verb}\n'
            f'{content_md5}\n'
            f'{content_type}\n'
            f'{date}\n'
            f'{canonicalized_oss_headers}{canonicalized_resource}'
        )
        print(string_to_sign)

        signature = base64.b64encode(
            hmac.new(
                self.access_key_secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                sha1
            ).digest()
        ).decode('utf-8')

        return f'OSS {self.access_key_id}:{signature}'

    def list_objects(self) -> list:
        objs = []
        marker = None

        while True:
            headers = {
                'Host': self.host,
                'Date': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime()),
                'Authorization': self.make_auth({
                    'verb': 'GET',
                })
            }
            res = requests.get(
                'https://' + self.host + '/{marker}'.format(marker=('?marker=' + marker) if marker else ''),
                headers=headers
            )
            etree = ElementTree.fromstring(res.text)
            for content in etree.findall('Contents'):
                objs.append((content.find('Key').text, content.find('ETag').text[1:-1]))

            marker = etree.findall('NextMarker')
            if marker:
                marker = marker[0].text
            else:
                break

        return objs

    def put_object(self, obj_name: str, data: bytes) -> bool:
        content_type = self.get_content_type(obj_name)

        # 计算Content-MD5
        content_md5 = base64.b64encode(md5(data).digest()).decode()

        headers = {
            'Host': self.host,
            'Date': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime()),
            'Content-Type': content_type,
            'Content-MD5': content_md5,
            'Content-Disposition': 'inline',
            'Authorization': self.make_auth({
                'verb': 'PUT',
                'content-md5': content_md5,
                'content-type': content_type,
                'canonicalized_resource': '/' + self.bucket + '/' + obj_name
            })
        }
        res = requests.put('https://' + self.host + '/' + quote(obj_name), data=data, headers=headers)
        print(res.status_code, res.text, res.headers)
        return res.status_code == 200

    def get_object(self, obj_name: str) -> bytes:
        headers = {
            'Host': self.host,
            'Date': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime()),
            'Authorization': self.make_auth({
                'verb': 'GET',
                'canonicalized_resource': '/' + self.bucket + '/' + obj_name
            })
        }
        res = requests.get('https://' + self.host + '/' + quote(obj_name), headers=headers)
        return res.content

    def del_object(self, obj_name: str) -> bool:
        headers = {
            'Host': self.host,
            'Date': time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime()),
            'Authorization': self.make_auth({
                'verb': 'DELETE',
                'canonicalized_resource': '/' + self.bucket + '/' + obj_name
            })
        }
        res = requests.delete('https://' + self.host + '/' + quote(obj_name), headers=headers)
        return res.status_code == 204
