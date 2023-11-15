# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------
# 角色说明：
# read：允许用户读取指定数据库
# readWrite：允许用户读写指定数据库
# dbAdmin：允许用户在指定数据库中执行管理函数，如索引创建、删除，查看统计或访问system.profile
# userAdmin：允许用户向system.users集合写入，可以找指定数据库里创建、删除和管理用户
# clusterAdmin：只在admin数据库中可用，赋予用户所有分片和复制集相关函数的管理权限。
# readAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的读权限
# readWriteAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的读写权限
# userAdminAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的userAdmin权限
# dbAdminAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的dbAdmin权限。
# root：只在admin数据库中可用。超级账号，超级权限

# sqlite模型
# ------------------------------
import os
import re
import json
import time
from typing import Tuple

from databaseModel.base import databaseBase
import public

try:
    import pymongo
except:
    public.ExecShell("btpip install pymongo")
    import pymongo
try:
    from BTPanel import session
except:
    pass


class panelMongoDB():
    _CONFIG_PATH = os.path.join(public.get_setup_path(), "mongodb/config.conf")

    def __init__(self):
        self.check_package()

        self.__CONN_KWARGS = {
            "host": "localhost",
            "port": 27017,
            "username": None,
            "password": None,
            "socketTimeoutMS": 3000,  # 套接字超时时间
            "connectTimeoutMS": 3000,  # 连接超时时间
            # "serverSelectionTimeoutMS": 3000,  # 服务器选择超时时间
        }
        self.__DB_CONN = None

    # 检查python包是否存在
    @classmethod
    def check_package(cls):
        """
        @name检测依赖是否正常
        """
        try:
            import pymongo
        except:
            public.ExecShell("btpip install pymongo")
            try:
                import pymongo
            except:
                return False
        return True

    # 连接MongoDB数据库
    def connect(self) -> Tuple[bool, str]:
        auth = self.get_config_options("authorization", str, "disabled") == "enabled"
        is_localhost = self.__CONN_KWARGS["host"] in ["localhost", "127.0.0.1"]
        # 本地连接自动补充 port username password
        if is_localhost:
            self.__CONN_KWARGS["port"] = self.get_config_options("port", int, 27017)

            if auth:
                if self.__CONN_KWARGS.get("username") is None and auth:  # 自动补充 username
                    self.__CONN_KWARGS["username"] = "root"
                if self.__CONN_KWARGS.get("password") is None:  # 自动补充 password
                    mongodb_root_path = os.path.join(public.get_panel_path(), "data/mongo.root")
                    if not os.path.exists(mongodb_root_path):
                        return False, "本地登录密码为空"
                    self.__CONN_KWARGS["password"] = public.readFile(mongodb_root_path)

        if not isinstance(self.__CONN_KWARGS["port"], int):
            self.__CONN_KWARGS["port"] = int(self.__CONN_KWARGS["port"])

        err_msg = ""
        try:
            self.__DB_CONN = pymongo.MongoClient(**self.__CONN_KWARGS)
            self.__DB_CONN.admin.command({"listDatabases": 1})
            return True, "正常"
        except Exception as err:
            err_msg = str(err)

        if self.__CONN_KWARGS.get("username") is None or self.__CONN_KWARGS.get("password") is None:
            return False, "用户名密码不能为空！"
        try:
            self.__DB_CONN = pymongo.MongoClient(**self.__CONN_KWARGS)
            self.__DB_CONN.admin.authenticate(self.__CONN_KWARGS["username"], self.__CONN_KWARGS["password"])
            self.__DB_CONN.admin.command({"listDatabases": 1})
            return True, "正常"
        except Exception as err:
            err_msg = str(err)
        return False, err_msg

    # 设置连接参数
    def set_host(self, *args, **kwargs):
        """
        设置连接参数
        """
        # args 兼容老版本，后续新增禁止使用 args
        if len(args) >= 5:
            kwargs["host"] = args[0]
            kwargs["port"] = args[1]
            kwargs["username"] = args[2]
            kwargs["password"] = args[3]

        if kwargs.get("db_host") is not None:
            kwargs["host"] = kwargs.get("db_host")
        if kwargs.get("db_port") is not None:
            kwargs["port"] = kwargs.get("db_port")
        if kwargs.get("db_user") is not None:
            kwargs["username"] = kwargs.get("db_user")
        if kwargs.get("db_password") is not None:
            kwargs["password"] = kwargs.get("db_password")
        self.__CONN_KWARGS.update(kwargs)

        if not isinstance(self.__CONN_KWARGS["port"], int):
            self.__CONN_KWARGS["port"] = int(self.__CONN_KWARGS["port"])
        return self

    def get_db_obj(self, db_name="admin"):
        if self.__DB_CONN is None:
            status, err_msg = self.connect()
            if status is False:
                return err_msg

        return self.__DB_CONN[db_name]

    # 获取配置文件
    @classmethod
    def get_config(cls, config_path: str = None):
        if config_path is None:
            config_path = cls._CONFIG_PATH
        if not os.path.exists(config_path):
            return ""
        info_data = public.readFile(config_path)
        return info_data

    # 获取未注释的配置文件参数
    @classmethod
    def get_config_options(cls, name: str, value_type: type, default=None):
        """
        获取未注释的配置文件参数
        name: 参数名称
        value_type: 参数类型
        """
        conf_data = public.readFile(cls._CONFIG_PATH)
        if not str(conf_data).endswith("\n"):
            conf_data += "\n"
        conf_obj = re.search(r"\n\s*{}\s*:\s*([^\n]*)\n".format(name), conf_data)
        if conf_obj:
            value = conf_obj.group(1)
            if value_type == bool:
                value = value == "true"
            else:
                value = value_type(value)
            return value

        if default is not None:
            if isinstance(default, value_type):
                return default
            elif value_type == bool:
                default = default == "true"
            else:
                default = value_type(default)
            return default
        return None

    # 获取配置项
    @classmethod
    def get_options(cls, *args, **kwargs):
        config_info = {
            "port": 27017,
            "bind_ip": "127.0.0.1",
            "logpath": "",
            "dbpath": "",
            "authorization": "disabled"
        }
        if not os.path.exists(cls._CONFIG_PATH):
            return config_info

        conf = public.readFile(cls._CONFIG_PATH)

        for opt in config_info.keys():
            tmp = re.findall(opt + ":\s+(.+)", conf)
            if not tmp: continue
            config_info[opt] = tmp[0]

        # public.writeFile("/www/server/1.txt",json.dumps(data))
        return config_info

    # 重启 mongodb 服务
    @classmethod
    def restart_localhost_services(cls):
        """
        @重启服务
        """
        public.ExecShell('/etc/init.d/mongodb restart')

    @classmethod
    def set_auth_open(cls, status):
        """
        @设置数据库密码访问开关
        @状态 status:1 开启，2：关闭
        """

        conf = public.readFile(cls._CONFIG_PATH)
        if status:
            conf = re.sub('authorization\s*\:\s*disabled', 'authorization: enabled', conf)
        else:
            conf = re.sub('authorization\s*\:\s*enabled', 'authorization: disabled', conf)

        public.writeFile(cls._CONFIG_PATH, conf)
        cls.restart_localhost_services()
        return True


class main(databaseBase):
    _DB_BACKUP_DIR = os.path.join(public.M("config").where("id=?", (1,)).getField("backup_path"), "database")
    _MONGODB_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "mongodb")
    _MONGODBDUMP_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongodump")
    _MONGOEXPORT_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongoexport")
    _MONGORESTORE_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongorestore")
    _MONGOIMPORT_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongoimport")

    def __init__(self):
        if not os.path.exists(self._MONGODB_BACKUP_DIR):
            os.makedirs(self._MONGODB_BACKUP_DIR)

    def get_list(self, get):
        """
        @获取数据库列表
        @sql_type = sqlserver
        """
        search = ''
        if 'search' in get: search = get['search']

        conditions = ''
        if '_' in search:
            cs = ''
            for i in search:
                if i == '_':
                    cs += '/_'
                else:
                    cs += i
            search = cs
            conditions = " escape '/'"

        SQL = public.M('databases');

        where = "lower(type) = lower('mongodb')"
        if search:
            where += "AND (name like '%{search}%' or ps like '%{search}%'{conditions})".format(search=search,
                                                                                               conditions=conditions)
        if 'db_type' in get:
            where += " AND db_type='{}'".format(get['db_type'])

        if 'sid' in get:
            where += " AND sid='{}'".format(get['sid'])

        order = "id desc"
        if hasattr(get, 'order'): order = get.order

        info = {}
        rdata = {}

        info['p'] = 1
        info['row'] = 20
        result = '1,2,3,4,5,8'
        info['count'] = SQL.where(where, ()).count();

        if hasattr(get, 'limit'): info['row'] = int(get.limit)
        if hasattr(get, 'result'): result = get.result;
        if hasattr(get, 'p'): info['p'] = int(get['p'])

        import page
        # 实例化分页类
        page = page.Page();

        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'): info['return_js'] = get.tojs

        rdata['where'] = where;

        # 获取分页数据
        rdata['page'] = page.GetPage(info, result)
        # 取出数据
        rdata['data'] = SQL.where(where, ()).order(order).field(
            'id,sid,pid,name,username,password,accept,ps,addtime,type,db_type,conn_config').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).select()

        for sdata in rdata['data']:
            # 清除不存在的
            backup_count = 0
            backup_list = public.M('backup').where("pid=? AND type=1", (sdata['id'])).select()
            for backup in backup_list:
                if not os.path.exists(backup["filename"]):
                    public.M('backup').where("id=? AND type=1", (backup['id'])).delete()
                    continue
                backup_count += 1
            sdata['backup_count'] = backup_count

            sdata['conn_config'] = json.loads(sdata['conn_config'])
        return rdata;

    def GetCloudServer(self, get):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        where = '1=1'
        if 'type' in get: where = "db_type = '{}'".format(get['type'])

        data = public.M('database_servers').where(where, ()).select()

        if not isinstance(data, list): data = []

        if get['type'] == 'mysql':
            bt_mysql_bin = public.get_mysql_info()['path'] + '/bin/mysql.exe'
            if os.path.exists(bt_mysql_bin):
                data.insert(0, {'id': 0, 'db_host': '127.0.0.1', 'db_port': 3306, 'db_user': 'root', 'db_password': '',
                                'ps': '本地服务器', 'addtime': 0, 'db_type': 'mysql'})
        elif get['type'] == 'sqlserver':
            pass
        elif get['type'] == 'mongodb':
            if os.path.exists('/www/server/mongodb/bin'):
                data.insert(0, {'id': 0, 'db_host': '127.0.0.1', 'db_port': 27017, 'db_user': 'root', 'db_password': '',
                                'ps': '本地服务器', 'addtime': 0, 'db_type': 'mongodb'})
        elif get['type'] == 'redis':
            if os.path.exists('/www/server/redis'):
                data.insert(0, {'id': 0, 'db_host': '127.0.0.1', 'db_port': 6379, 'db_user': 'root', 'db_password': '',
                                'ps': '本地服务器', 'addtime': 0, 'db_type': 'redis'})
        elif get['type'] == 'pgsql':
            if os.path.exists('/www/server/pgsql'):
                data.insert(0,
                            {'id': 0, 'db_host': '127.0.0.1', 'db_port': 5432, 'db_user': 'postgres', 'db_password': '',
                             'ps': '本地服务器', 'addtime': 0, 'db_type': 'pgsql'})
        return data

    def AddCloudServer(self, get):
        """
        @name 添加远程服务器
        @author hwliang<2021-01-10>
        @param db_host<string> 服务器地址
        @param db_port<port> 数据库端口
        @param db_user<string> 用户名
        @param db_password<string> 数据库密码
        @param db_ps<string> 数据库备注
        @param type<string> 数据库类型，mysql/sqlserver/sqlite
        @return dict
        """

        arrs = ['db_host', 'db_port', 'db_user', 'db_password', 'db_ps', 'type']
        if get.type == 'redis': arrs = ['db_host', 'db_port', 'db_password', 'db_ps', 'type']

        for key in arrs:
            if key not in get:
                return public.returnMsg(False, '参数传递错误，缺少参数{}!'.format(key))

        get['db_name'] = None

        mongodb_obj = panelMongoDB().set_host(host=get.get("db_host"), port=get.get("db_port"), username=get.get("db_user"), password=get.get("db_password"))
        status, err_msg = mongodb_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        if public.M('database_servers').where('db_host=? AND db_port=?', (get['db_host'], get['db_port'])).count():
            return public.returnMsg(False, '指定服务器已存在: [{}:{}]'.format(get['db_host'], get['db_port']))
        get['db_port'] = int(get['db_port'])
        pdata = {
            'db_host': get['db_host'],
            'db_port': int(get['db_port']),
            'db_user': get['db_user'],
            'db_password': get['db_password'],
            'db_type': get['type'],
            'ps': public.xssencode2(get['db_ps'].strip()),
            'addtime': int(time.time())
        }
        result = public.M("database_servers").insert(pdata)

        if isinstance(result, int):
            public.WriteLog('数据库管理', '添加远程MySQL服务器[{}:{}]'.format(get['db_host'], get['db_port']))
            return public.returnMsg(True, '添加成功!')
        return public.returnMsg(False, '添加失败： {}'.format(result))

    def RemoveCloudServer(self, get):
        '''
        @删除远程数据库
        '''
        id = int(get.id)
        if not id: return public.returnMsg(False, '参数传递错误，请重试!')
        db_find = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mongodb')", (id,)).find()
        if not db_find: return public.returnMsg(False, '指定远程服务器不存在!')
        public.M('databases').where('sid=?', id).delete()
        result = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('mongodb')", id).delete()
        if isinstance(result, int):
            public.WriteLog('数据库管理',
                            '删除远程MySQL服务器[{}:{}]'.format(db_find['db_host'], int(db_find['db_port'])))
            return public.returnMsg(True, '删除成功!')
        return public.returnMsg(False, '删除失败： {}'.format(result))

    def ModifyCloudServer(self, get):
        '''
            @name 修改远程服务器
            @author hwliang<2021-01-10>
            @param id<int> 远程服务器ID
            @param db_host<string> 服务器地址
            @param db_port<port> 数据库端口
            @param db_user<string> 用户名
            @param db_password<string> 数据库密码
            @param db_ps<string> 数据库备注
            @return dict
        '''

        arrs = ['db_host', 'db_port', 'db_user', 'db_password', 'db_ps', 'type']
        if get.type == 'redis': arrs = ['db_host', 'db_port', 'db_password', 'db_ps', 'type']

        for key in arrs:
            if key not in get:
                return public.returnMsg(False, '参数传递错误，缺少参数{}!'.format(key))

        id = int(get.id)
        get['db_port'] = int(get['db_port'])
        db_find = public.M('database_servers').where('id=?', (id,)).find()
        if not db_find: return public.returnMsg(False, '指定远程服务器不存在!')
        _modify = False
        if db_find['db_host'] != get['db_host'] or db_find['db_port'] != get['db_port']:
            _modify = True
            if public.M('database_servers').where('db_host=? AND db_port=?', (get['db_host'], get['db_port'])).count():
                return public.returnMsg(False, '指定服务器已存在: [{}:{}]'.format(get['db_host'], get['db_port']))

        if db_find['db_user'] != get['db_user'] or db_find['db_password'] != get['db_password']:
            _modify = True
        _modify = True
        # if _modify:

        # res = self.check_cloud_database(get)
        # if res.get("db_status", False) is False:
        #     return res

        pdata = {
            'db_host': get['db_host'],
            'db_port': int(get['db_port']),
            'db_user': get['db_user'],
            'db_password': get['db_password'],
            'db_type': get['type'],
            'ps': public.xssencode2(get['db_ps'].strip())
        }

        result = public.M("database_servers").where('id=?', (id,)).update(pdata)
        if isinstance(result, int):
            public.WriteLog('数据库管理', '修改远程MySQL服务器[{}:{}]'.format(get['db_host'], get['db_port']))
            return public.returnMsg(True, '修改成功!')
        return public.returnMsg(False, '修改失败： {}'.format(result))

    def set_auth_status(self, get):
        """
        @设置密码认证状态
        @status int 0：关闭，1：开启
        """

        if not public.process_exists("mongod"):
            return public.returnMsg(False, "Mongodb服务还未开启！")

        status = int(get.status)
        path = '{}/data/mongo.root'.format(public.get_panel_path())
        if status:
            if hasattr(get, 'password'):
                password = get['password'].strip()
                if not password or not re.search("^[\w@\.]+$", password):
                    return public.returnMsg(False, '数据库密码不能为空或带有特殊字符')

                if re.search('[\u4e00-\u9fa5]', password):
                    return public.returnMsg(False, '数据库密码不能为中文，请换个名称!')
            else:
                password = public.GetRandomString(16)
            panelMongoDB.set_auth_open(False)

            mongodb_obj = panelMongoDB()
            status, err_msg = mongodb_obj.connect()
            if status is False:
                public.returnMsg(False, "连接数据库失败！")

            _client = mongodb_obj.get_db_obj('admin')
            try:
                _client.command("dropUser", "root")
            except:
                pass

            _client.command("createUser", "root", pwd=password, roles=[
                {'role': 'root', 'db': 'admin'},
                {'role': 'clusterAdmin', 'db': 'admin'},
                {'role': 'readAnyDatabase', 'db': 'admin'},
                {'role': 'readWriteAnyDatabase', 'db': 'admin'},
                {'role': 'userAdminAnyDatabase', 'db': 'admin'},
                {'role': 'dbAdminAnyDatabase', 'db': 'admin'},
                {'role': 'userAdmin', 'db': 'admin'},
                {'role': 'dbAdmin', 'db': 'admin'}
            ])
            panelMongoDB.set_auth_open(True)

            public.writeFile(path, password)
        else:
            if os.path.exists(path): os.remove(path)
            panelMongoDB.set_auth_open(False)

        return public.returnMsg(True, '操作成功.')

    def get_obj_by_sid(self, sid=0, conn_config=None):
        """
        @取mssql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if type(sid) == str:
            try:
                sid = int(sid)
            except:
                sid = 0

        if sid:
            if not conn_config: conn_config = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('mongodb')", sid).find()
            mongodb_obj = panelMongoDB().set_host(host=conn_config["db_host"], port=conn_config["db_port"], username=conn_config["db_user"], password=conn_config["db_password"])
            status, err_msg = mongodb_obj.connect()
            if status is False:
                raise public.PanelError(err_msg)
        else:
            mongodb_obj = panelMongoDB()
            status, err_msg = mongodb_obj.connect()
            if status is False:
                raise public.PanelError(err_msg)
        return mongodb_obj

    def AddDatabase(self, get):
        """
        @添加数据库
        """
        try:
            sid = int(get.sid)
        except:
            return public.returnMsg(False, '数据库类型sid需要int类型！')
        if not int(get.sid) and not public.process_exists("mongod"):
            return public.returnMsg(False, "Mongodb服务还未开启！")
        dtype = 'MongoDB'
        username = ''
        password = ''
        auth_status = panelMongoDB.get_config_options("authorization", str, "disabled") == "enabled"  # auth为true时如果__DB_USER为空则将它赋值为 root，用于开启本地认证后数据库用户为空的情况
        data_name = get.name.strip()
        if not data_name:
            return public.returnMsg(False, "数据库名不能为空！")
        if auth_status:
            res = self.add_base_database(get, dtype)
            if not res['status']: return res

            data_name = res['data_name']
            username = res['username']
            password = res['data_pwd']
        else:
            username = data_name
        db_obj = self.get_obj_by_sid(get.sid).get_db_obj(data_name)
        if isinstance(db_obj, str):
            return public.returnMsg(False, "数据库名连接错误！{}".format(db_obj))

        if not hasattr(get, 'ps'): get['ps'] = public.getMsg('INPUT_PS')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())

        pid = 0
        if hasattr(get, 'pid'): pid = get.pid

        if hasattr(get, 'contact'):
            site = public.M('sites').where("id=?", (get.contact,)).field('id,name').find()
            if site:
                pid = int(get.contact)
                get['ps'] = site['name']

        db_type = 0
        if sid: db_type = 2

        db_obj.chat.insert_one({})
        if auth_status:
            db_obj.command("createUser", username, pwd=password, roles=[{'role': 'dbOwner', 'db': data_name}, {'role': 'userAdmin', 'db': data_name}])

        public.set_module_logs('linux_mongodb', 'AddDatabase', 1)

        # 添加入SQLITE
        public.M('databases').add('pid,sid,db_type,name,username,password,accept,ps,addtime,type', (pid, sid, db_type, data_name, username, password, '127.0.0.1', get['ps'], addTime, dtype))
        public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS', (data_name,))
        return public.returnMsg(True, 'ADD_SUCCESS')

    def DeleteDatabase(self, get):
        """
        @删除数据库
        """
        id = get['id']
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid,db_type').find()
        if not find: return public.returnMsg(False, '指定数据库不存在.')
        try:
            int(find['sid'])
        except:
            return public.returnMsg(False, '数据库类型sid需要int类型！')
        if not public.process_exists("mongod") and not int(find['sid']):
            return public.returnMsg(False, "Mongodb服务还未开启！")
        name = get['name']
        username = find['username']
        db_obj = self.get_obj_by_sid(find['sid']).get_db_obj(name)
        try:
            db_obj.command("dropUser", username)
        except:
            pass

        db_obj.command('dropDatabase')
        # 删除SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS', (name,))
        return public.returnMsg(True, 'DEL_SUCCESS')

    def get_info_by_db_id(self, db_id):
        """
        @获取数据库连接详情
        @db_id 数据库id
        """
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('mongodb')", db_id).find()
        if not find: return False

        if find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
        elif find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mongodb')", find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
        else:  # 本地数据库
            db_host = '127.0.0.1'
            db_port = panelMongoDB.get_config_options("port", int, 27017)
        data = {
            'db_name': find["name"],
            'db_host': db_host,
            'db_port': int(db_port),
            'db_user': find['username'],
            'db_password': find['password'],
        }
        return data

    # 导入
    def InputSql(self, args):
        name = args.name
        file = args.file

        if not os.path.exists(file): return public.returnMsg(False, '导入路径不存在!')
        if not os.path.isfile(file): return public.returnMsg(False, '仅支持导入压缩文件!')
        find = public.M('databases').where("name=? AND LOWER(type)=LOWER('MongoDB')", (name,)).find()
        if not find: return public.returnMsg(False, '数据库不存在!')

        get = public.dict_obj()
        get.sid = find['sid']
        if not public.process_exists("mongod") and not int(find['sid']):
            return public.returnMsg(False, "Mongodb服务还未开启！")
        info = self.get_info_by_db_id(find['id'])
        mongorestore_obj = '{}/mongodb/bin/mongorestore'.format(public.get_setup_path())
        mongoimport_obj = '{}/mongodb/bin/mongoimport'.format(public.get_setup_path())
        if not os.path.exists(mongorestore_obj): return public.returnMsg(False, '缺少备份工具，请先通过软件管理安装MongoDB!')

        dir_tmp, file_tmp = os.path.split(file)
        split_tmp = file_tmp.split(".")
        ext = split_tmp[-1]

        ext_err = ".".join(split_tmp[1:])
        if len(split_tmp[1:]) == 2 and split_tmp[1] not in ['json', 'csv']:
            return public.returnMsg(False, f'.{ext_err} 暂不支持该文件格式！')
        if ext not in ['json', 'csv', 'gz', 'zip']:
            return public.returnMsg(False, f'.{ext_err} 暂不支持该文件格式！')

        tmpFile = ".".join(split_tmp[:-1])
        isgzip = False
        if ext != '':  # gz zip
            if tmpFile == '':
                return public.returnMsg(False, 'FILE_NOT_EXISTS', (tmpFile,))
            isgzip = True

            # 面板默认备份路径
            backupPath = session['config']['backup_path'] + '/database'
            input_path = os.path.join(backupPath, tmpFile)
            # 备份文件的路径
            input_path2 = os.path.join(dir_tmp, tmpFile)

            if ext == 'zip':  # zip
                public.ExecShell("cd " + backupPath + " && unzip " + '"' + file + '"')
            else:  # gz
                public.ExecShell("cd " + backupPath + " && tar zxf " + '"' + file + '"')
                if not os.path.exists(input_path):
                    # 兼容从备份文件所在目录恢复
                    if not os.path.exists(input_path2):
                        public.ExecShell("cd " + backupPath + " && gunzip -q " + '"' + file + '"')
                    else:
                        input_path = input_path2

            if not os.path.exists(input_path) and os.path.isfile(input_path2):
                input_path = input_path2
        else:
            input_path = file

        if os.path.isdir(input_path):  # zip,gz,bson
            if panelMongoDB.get_config_options("authorization", str, "disabled") == "enabled":
                for temp_file in os.listdir(input_path):
                    shell = f"""
                        {mongorestore_obj} \
                        --host={info['db_host']} \
                        --port={info['db_port']} \
                        --db={find['name']} \
                        --username={info['db_user']} \
                        --password={info['db_password']} \
                        --drop \
                        {os.path.join(input_path, temp_file)}
                    """
                    public.ExecShell(shell)
            else:
                for temp_file in os.listdir(input_path):
                    shell = f"""
                        {mongorestore_obj} \
                        --host={info['db_host']} \
                        --port={info['db_port']} \
                        --db={find['name']} \
                        --drop \
                        {os.path.join(input_path, temp_file)}
                    """
                    public.ExecShell(shell)
            if isgzip is True:
                public.ExecShell("rm -f " + input_path)
        else:  # json,csv
            file_tmp = os.path.basename(input_path)
            file_name = file_tmp.split(".")[0]
            ext = file_tmp.split(".")[-1]

            if ext not in ["json", "csv"]:
                return public.returnMsg(False, '文件格式不正确!')

            shell_txt = ""
            if ext == "csv":
                fp = open(input_path, "r")
                fields_list = fp.readline()
                fp.close()
                shell_txt = f"--fields={fields_list}"
            if panelMongoDB.get_config_options("authorization", str, "disabled") == "enabled":
                shell = f"""
                    {mongoimport_obj} \
                    --host={info['db_host']} \
                    --port={info['db_port']} \
                    --db={find['name']} \
                    --username={info['db_user']} \
                    --password={info['db_password']} \
                    --collection={file_name} \
                    --file={input_path} \
                    --type={ext} \
                    --drop
                """
            else:
                shell = f"""
                    {mongoimport_obj} \
                    --host={info['db_host']} \
                    --port={info['db_port']} \
                    --db={find['name']} \
                    --collection={file_name} \
                    --file={input_path} \
                    --type={ext} \
                    --drop
                """
            shell = f"{shell} {shell_txt}"
            public.ExecShell(shell)
        public.WriteLog("TYPE_DATABASE", '导入数据库[{}]成功'.format(name))
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS')

    def ToBackup(self, args):
        """
        @备份数据库 id 数据库id
        """
        id = args['id']
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).find()
        if not find: return public.returnMsg(False, '数据库不存在!')

        fileName = f"{find['name']}_mongodb_data_{time.strftime('%Y%m%d_%H%M%S', time.localtime())}"
        backupName = session['config']['backup_path'] + '/database/mongodb/' + fileName

        spath = os.path.dirname(backupName)
        if not os.path.exists(spath): os.makedirs(spath)

        get = public.dict_obj()
        get.sid = find['sid']
        try:
            sid = int(find['sid'])
        except:
            return public.returnMsg(False, '数据库类型sid需要int类型！')
        if not public.process_exists("mongod") and not int(find['sid']):
            return public.returnMsg(False, "Mongodb服务还未开启！")
        info = self.get_info_by_db_id(id)

        sql_dump = '{}/mongodb/bin/mongodump'.format(public.get_setup_path())
        if not os.path.exists(sql_dump): return public.returnMsg(False, '缺少备份工具，请先通过软件管理安装MongoDB!')

        if panelMongoDB.get_config_options("authorization", str, "disabled") == "enabled":
            if not info['db_password']:
                return public.returnMsg(False, 'Mongodb已经开启密码认证，数据库备份时密码不能为空，请设置密码后再试！')
            shell = "{}  -h {} --port {} -u {} -p {} -d {} -o {} ".format(sql_dump, info['db_host'], info['db_port'], info['db_user'], info['db_password'], find['name'], backupName)
        else:
            shell = "{}  -h {} --port {} -d {} -o {} ".format(sql_dump, info['db_host'], info['db_port'], find['name'], backupName)

        ret = public.ExecShell(shell)
        if not os.path.exists(backupName):
            return public.returnMsg(False, '数据库备份失败，文件不存在')

        backupFile = f"{backupName}.zip"
        public.ExecShell(f"cd {spath} && zip {backupFile} -r  {fileName}")
        fileName = f"{fileName}.zip"
        public.M('backup').add('type,name,pid,filename,size,addtime', (1, fileName, id, backupFile, 0, time.strftime('%Y-%m-%d %X', time.localtime())))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (find['name'],))

        public.ExecShell(f"rm -rf {backupName}")
        if not os.path.exists(backupFile):
            return public.returnMsg(True, '备份失败，{}.'.format(ret[0]))
        if os.path.getsize(backupFile) < 1:
            return public.returnMsg(True, '备份执行成功，备份文件小于1b，请检查备份完整性.')
        else:
            return public.returnMsg(True, 'BACKUP_SUCCESS')

    def DelBackup(self, get):
        """
        @删除备份文件
        """
        try:
            name = ''
            id = get.id
            where = "id=?"
            filename = public.M('backup').where(where, (id,)).getField('filename')
            if os.path.exists(filename): os.remove(filename)

            if filename == 'qiniu':
                name = public.M('backup').where(where, (id,)).getField('name');

                public.ExecShell(public.get_run_python("[PYTHON] " + public.GetConfigValue(
                    'setup_path') + '/panel/script/backup_qiniu.py delete_file ' + name))
            public.M('backup').where(where, (id,)).delete()
            public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_SUCCESS', (name, filename))
            return public.returnMsg(True, 'DEL_SUCCESS');
        except Exception as err:
            return public.returnMsg(False, "删除备份文件失败！")

    # 同步数据库到服务器
    def SyncToDatabases(self, get):
        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,name,username,password,accept,type,sid,db_type').where("LOWER(type)=LOWER('MongoDB')", ()).select()
            for value in data:
                if value['db_type'] in ['1', 1]:
                    continue  # 跳过远程数据库
                result = self.ToDataBase(value)
                if result == 1: n += 1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?", (value,)).field('id,name,username,password,sid,db_type,accept,type').find()
                result = self.ToDataBase(find)
                if result == 1: n += 1
        if n == 1:
            return public.returnMsg(True, '同步成功')
        elif n == 0:
            return public.returnMsg(False, '同步失败')
        return public.returnMsg(True, 'DATABASE_SYNC_SUCCESS', (str(n),))

    # 添加到服务器
    def ToDataBase(self, find):
        if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3:
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (find['id'],)).save('password,username', (find['password'], find['username']))

        try:
            sid = int(find['sid'])
        except:
            return public.returnMsg(False, '数据库类型sid需要int类型！')
        if not public.process_exists("mongod") and not int(find['sid']):
            return public.returnMsg(False, "Mongodb服务还未开启！")

        get = public.dict_obj()
        get.sid = sid
        auth_status = panelMongoDB.get_config_options("authorization", str, "disabled") == "enabled"
        if auth_status:
            db_obj = self.get_obj_by_sid(sid).get_db_obj(find['name'])
            try:
                db_obj.chat.insert_one({})
                db_obj.command("dropUser", find['username'])
            except:
                pass
            try:
                db_obj.command("createUser", find['username'], pwd=find['password'], roles=[{'role': 'dbOwner', 'db': find['name']}, {'role': 'userAdmin', 'db': find['name']}])
            except:
                pass
        return 1

    def SyncGetDatabases(self, get):
        """
        @从服务器获取数据库
        """
        n = 0
        s = 0
        db_type = 0
        sid = get.get('sid/d', 0)
        if sid: db_type = 2
        try:
            int(get.sid)
        except:
            return public.returnMsg(False, '数据库类型sid需要int类型！')
        if not public.process_exists("mongod") and not int(get.sid):
            return public.returnMsg(False, "Mongodb服务还未开启！")

        mongodb_obj = self.get_obj_by_sid(sid)

        data = mongodb_obj.get_db_obj('admin').command({"listDatabases": 1})

        sql = public.M('databases')
        nameArr = ['information_schema', 'performance_schema', 'mysql', 'sys', 'master', 'model', 'msdb', 'tempdb', 'config', 'local', 'admin']
        for item in data['databases']:
            dbname = item['name']
            if sql.where("name=? AND LOWER(type)=LOWER('MongoDB')", (dbname,)).count(): continue
            if dbname in nameArr: continue
            if sql.table('databases').add('name,username,password,accept,ps,addtime,type,sid,db_type', (dbname, dbname, "", "", public.getMsg('INPUT_PS'), time.strftime('%Y-%m-%d %X', time.localtime()), 'MongoDB', sid, db_type)): n += 1

        return public.returnMsg(True, 'DATABASE_GET_SUCCESS', (str(n),))

    def ResDatabasePassword(self, get):
        """
        @修改用户密码
        """
        id = get['id']
        username = get['name'].strip()
        newpassword = public.trim(get['password'])

        try:
            if not newpassword:
                return public.returnMsg(False, '修改失败，数据库[' + username + ']密码不能为空.')
            if len(re.search("^[\w@\.]+$", newpassword).groups()) > 0:
                return public.returnMsg(False, '数据库密码不能为空或带有特殊字符')

            if re.search('[\u4e00-\u9fa5]', newpassword):
                return public.returnMsg(False, '数据库密码不能为中文，请换个名称!')
        except:
            return public.returnMsg(False, '数据库密码不能为空或带有特殊字符')

        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid').find()
        if not find: return public.returnMsg(False, '修改失败，指定数据库不存在.')

        get = public.dict_obj()
        get.sid = find['sid']
        try:
            int(find['sid'])
        except:
            return public.returnMsg(False, '数据库类型sid需要int类型！')
        if not public.process_exists("mongod") and not int(find['sid']):
            return public.returnMsg(False, "Mongodb服务还未开启！")
        auth_status = panelMongoDB.get_config_options("authorization", str, "disabled") == "enabled"
        if auth_status:
            db_obj = self.get_obj_by_sid(find['sid']).get_db_obj(username)
            try:
                db_obj.command("updateUser", username, pwd=newpassword)
            except:
                db_obj.command("createUser", username, pwd=newpassword, roles=[{'role': 'dbOwner', 'db': find['name']}, {'role': 'userAdmin', 'db': find['name']}])
        else:
            return public.returnMsg(False, '修改失败，数据库未开启密码访问.')

        # 修改SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).setField('password', newpassword)

        public.WriteLog("TYPE_DATABASE", 'DATABASE_PASS_SUCCESS', (find['name'],))
        return public.returnMsg(True, 'DATABASE_PASS_SUCCESS', (find['name'],))

    def get_root_pwd(self, get):
        """
        @获取root密码
        """
        config = panelMongoDB.get_options()
        sa_path = '{}/data/mongo.root'.format(public.get_panel_path())
        if os.path.exists(sa_path):
            config['msg'] = public.readFile(sa_path)
        else:
            config['msg'] = ''
        config['root'] = config['msg']
        return config

    def get_database_size_by_id(self, get):
        """
        @获取数据库尺寸（批量删除验证）
        @get json/int 数据库id
        """
        # if not public.process_exists("mongod"):
        #     return public.returnMsg(False,"Mongodb服务还未开启！")
        total = 0
        db_id = get
        if not isinstance(get, int): db_id = get['db_id']

        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", db_id).find()
        try:
            int(find['sid'])
        except:
            return 0
        if not public.process_exists("mongod") and not int(find['sid']):
            return 0
        try:
            auth_status = panelMongoDB.get_config_options("authorization", str, "disabled") == "enabled"
            db_obj = self.get_obj_by_sid(find['sid']).get_db_obj(find['name'])
            db_obj
            db_obj.stats()

            total = tables[0][1]
            if not total: total = 0
        except:
            public.get_error_info()

        return total

    def check_del_data(self, args):
        """
        @删除数据库前置检测
        """
        return self.check_base_del_data(args)

    def __new_password(self):
        """
        生成随机密码
        """
        import random
        import string
        # 生成随机密码
        password = "".join(random.sample(string.ascii_letters + string.digits, 16))
        return password

    # 数据库状态检测
    def CheckDatabaseStatus(self, get):
        """
        数据库状态检测
        """
        if not hasattr(get, "sid"):
            return public.returnMsg(False, "缺少参数！sid")
        if not str(get.sid).isdigit():
            return public.returnMsg(False, "参数错误！sid")
        sid = int(get.sid)
        mongodb_obj = panelMongoDB()
        if sid == 0:
            db_status, err_msg = mongodb_obj.connect()
        else:
            conn_config = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('mongodb')", sid).find()
            if not conn_config:
                db_status = False
                err_msg = "远程数据库信息不存在！"
            else:
                mongodb_obj.set_host(host=conn_config.get("db_host"), port=conn_config.get("db_port"), username=conn_config.get("db_user"), password=conn_config.get("db_password"))
                db_status, err_msg = mongodb_obj.connect()

        return {"status": True, "msg": "正常" if db_status is True else "异常", "db_status": db_status, "err_msg": err_msg}

    def check_cloud_database_status(self, conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        旧方法，添加数据库时调用
        """
        try:
            mongodb_obj = panelMongoDB().set_host(host=conn_config.get("db_host"), port=conn_config.get("db_port"), username=conn_config.get("db_user"), password=conn_config.get("db_password"))
            status, err_msg = mongodb_obj.connect()
            return status
        except:
            return public.returnMsg(False, "远程数据库连接失败！")
