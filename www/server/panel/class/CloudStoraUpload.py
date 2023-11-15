# coding: utf-8
#  + -------------------------------------------------------------------
# | 宝塔云存储上传接口
#  + -------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#  + -------------------------------------------------------------------
# | Author: sww
#  + -------------------------------------------------------------------

'''
增加
先添加/www/server/panel/data/libList.conf文件中的信息
增加对应存储的class --实现检测是否链接成功，实现上传接口封装  链接失败或未登录都返回false，成功返回对象 authorize权限判定函数
增加CloudStoraUpload类中cloud_obj映射
'''

import os
import sys
import traceback

import public


# 七牛云
class qiniu:
    flag = True
    qc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/qiniu' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/qiniu')
        try:
            from qiniu_main import QiNiuClient as qc
            self.qc_obj = qc()
            self.qc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.qc_obj
        else:
            return False


# 百度云
class bos:
    flag = True
    bc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/bos' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/bos')
        try:
            from bos_main import BOSClient as bc
            self.bc_obj = bc()
            self.bc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.bc_obj
        else:
            return False


# 腾讯云
class cos:
    flag = True
    cc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/txcos' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/txcos')
        try:
            from txcos_main import COSClient as cc
            self.cc_obj = cc()
            self.cc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.cc_obj
        else:
            return False


# 又拍云
class upyun:
    flag = True
    uc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/upyun' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/upyun')
        try:
            from upyun_main import UpYunClient as uc
            self.uc_obj = uc()
            self.uc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.uc_obj
        else:
            return False


# 阿里云
class alioss:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/alioss' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/alioss')
        try:
            from alioss_main import OSSClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False


# 未测试
class gdrive:
    flag = True
    gc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/gdrive' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/gdrive')
        try:
            from gdrive_main import gdrive_main as gc
            self.gc_obj = gc()
            if not self.gc_obj.set_creds():
                self.flag = False
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.gc_obj
        else:
            return False


# 亚马逊
class aws_s3:
    flag = True
    cc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/aws_s3' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/aws_s3')
        try:
            from gdrive_main import COSClient as cc
            self.cc_obj = cc()
            self.cc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.cc_obj
        else:
            return False


# 未测试  未做登录确定
class gcloud_storage:
    flag = True
    gsc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/gcloud_storage' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/gcloud_storage')
        try:
            from gcloud_storage_main import gcloud_storage_main as gsc
            self.gsc_obj = gsc()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.gsc_obj
        else:
            return False


# 华为云
class obs:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/obs' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/obs')
        try:
            from obs_main import OBSClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False


# 未测试
class msonedrive:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/msonedrive' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/msonedrive')
        try:
            from msonedrive_main import OneDriveClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False


# ftp    未登录验证
class ftp:
    flag = True
    ftp_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/ftp' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/ftp')
        try:
            from ftp_main import get_client
            self.ftp_obj = get_client(use_sftp=None)
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.ftp_obj
        else:
            return False


# 京东云
class jdcloud:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/jdcloud' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/jdcloud')
        try:
            from jdcloud_main import OBSClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False


# 总函数
class CloudStoraUpload:
    cloud_list = []
    cloud_obj = {
        'qiniu': qiniu,
        'alioss': alioss,
        'ftp': ftp,
        'bos': bos,
        'obs': obs,
        'aws_s3': aws_s3,
        'gdrive': gdrive,
        'msonedrive': msonedrive,
        'gcloud_storage': gcloud_storage,
        'upyun': upyun,
        'jdcloud': jdcloud,
        'txcos': cos,
    }

    def __init__(self):
        self.obj = None
        # 获取当前云存储的安装列表
        import json
        tmp = public.readFile('/www/server/panel/data/libList.conf')
        if tmp:
            libs = json.loads(tmp)
            for lib in libs:
                if not 'opt' in lib: continue
                filename = '/www/server/panel/plugin/{}'.format(lib['opt'])
                if not os.path.exists(filename): continue
                self.cloud_list.append(lib['opt'])

    def run(self, cloud_name):
        if cloud_name not in self.cloud_list or cloud_name not in self.cloud_obj.keys():
            return False
        obj = self.cloud_obj[cloud_name]()
        if not obj.flag:
            return False
        self.obj = obj.get_obj()
        return self.obj

    def cloud_upload_file(self, file_name: str, upload_path: str, *args, **kwargs):
        """按照数据类型上传文件

        针对 panelBackup v1.2以上调用
        :param file_name: 上传文件名称
        :param data_type: 数据类型 site/database/path
        :return: True/False
        """
        try:
            return self.obj.resumable_upload(file_name, object_name=upload_path, *args, **kwargs)
        except Exception as e:
            return False

    def cloud_delete_dir(self, file_path: str, *args, **kwargs):
        """删除文件夹
        """
        try:

            dir_list = self.obj.get_list(file_path)
            for info in dir_list["list"]:
                path = os.path.join(file_path, info['name'])
                self.obj.delete_object(path, *args, **kwargs)
            return True
        except Exception as e:
            return False

    def cloud_download_file(self, clould_path, loacl_path, *args, **kwargs):
        try:
            if not self.obj:
                return False
            if self.obj.get_list(clould_path)['list']:  # 调用目录下载
                self.cloud_download_dir(clould_path, loacl_path, *args, **kwargs)
            return self.obj.download_file(clould_path, loacl_path, *args, **kwargs)
        except:
            return public.returnMsg(False, '云存储下载文件失败')

    def cloud_download_dir(self, clould_path, loacl_path, *args, **kwargs):
        try:
            if not self.obj:
                return False
            data = self.obj.get_list(clould_path)
            if not os.path.exists(loacl_path):
                os.makedirs(loacl_path)
            for i in data['list']:
                path = os.path.join(data['path'], i['name'])
                loacl_path1 = os.path.join(loacl_path, i['name'])
                if self.obj.get_list(path)['list']:  # 判断是否是文件夹
                    if not os.path.exists(loacl_path1):
                        os.makedirs(loacl_path1)
                    self.cloud_download_dir(path, loacl_path1, *args, **kwargs)
                else:
                    self.obj.download_file(path, loacl_path1, *args, **kwargs)
            return
        except:
            return public.returnMsg(False, '云存储下载文件失败')

    def get_file_download_url(self, down_load_path):
        if self.obj.get_list(down_load_path)['list']:
            return public.returnMsg(False, '不支持文件夹下载，请手动到云存储服务端下载')
        file_name = os.path.basename(down_load_path)
        down_load_path = os.path.dirname(down_load_path)
        data = self.obj.get_list(down_load_path)
        if data['list']:
            for i in data['list']:
                if i['name'] == file_name:
                    return public.returnMsg(True, i['download'])
        return public.returnMsg(False, '获取下载链接失败')

# if __name__ == '__main__':
# c = CloudStoraUpload()
# a = c.run('alioss')
# x = 'bt_backup/database/test_cron_back_1_2023-10-10_02-30-03_mysql_data.sql.gz'
# print(c.obj.backup_path)
# c.cloud_download_file('/bt_backup/', '/xiaopacai/backup')
