# -*- coding: utf-8 -*-

import json
import os

from tencent_cos import TencentCOSBucket
from aliyun_oss import AliyunOSSBucket
from utils import FileManager, OSSSynchronizer


if __name__ == '__main__':
    with open('config/config.json', 'rt', encoding='utf-8') as fp:
        configs = json.load(fp)

    if type(configs) == dict:
        configs = [configs, ]

    for config in configs:

        oss_type = config.get('oss_type')
        oss_config_file = config.get('oss_config')
        local_dir = config.get('local_dir')
        direction = config.get('direction')

        if not oss_type or not oss_config_file or not local_dir or not direction:
            print('`oss_type` 、 `oss_config` 、 `local_dir` 、 `direction` 四个字段都是必填的，请补充完整')
            exit(-1)

        if oss_type not in ('tencent-cos', 'aliyun-oss'):
            print('`oss_type` 的值只能是 `tencent-cos` （腾讯云COS） 或者 `aliyun-oss` （阿里云OSS）')
            exit(-1)

        if not os.path.isfile(oss_config_file):
            print(f'`oss_config` 的值 "{oss_config_file}" 所指向的文件不存在')
            exit(-1)

        if not os.path.isdir(local_dir):
            print(f'`local_dir` 的值 "{local_dir}" 所指向的目录不存在')
            exit(-1)

        if direction not in ('local-to-remote', 'remote-to-local'):
            print('`direction` 的值只能是 `local-to-remote` 或者 `remote-to-local`')
            exit(-1)

        with open(oss_config_file, 'rt', encoding='utf-8') as fp:
            oss_config = json.load(fp)
            if oss_type == 'tencent-cos':
                bucket = TencentCOSBucket(oss_config)
            else:
                bucket = AliyunOSSBucket(oss_config)

        file_manager = FileManager(local_dir)
        oss_synchronizer = OSSSynchronizer(file_manager, bucket)

        if direction == 'local-to-remote':
            print(f'正在同步 {local_dir}（本地）-> {oss_config.get("bucket", "Unknown Bucket")}（OSS）')
            oss_synchronizer.sync_from_local_to_oss()
        else:
            print(f'正在同步 {oss_config.get("bucket", "Unknown Bucket")}（OSS） -> {local_dir}（本地）')
            oss_synchronizer.sync_from_oss_to_local()
