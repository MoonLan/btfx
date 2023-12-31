# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hezhihong <bt_ahong@qq.com>
# -------------------------------------------------------------------

# ------------------------------
# postgresql模型
# ------------------------------
import os
import re
import json
import time
from typing import Tuple, Union

from databaseModel.base import databaseBase
import public

try:
    from BTPanel import session
except:
    pass
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except:
    pass


class panelPgsql:
    _CONFIG_PATH = os.path.join(public.get_setup_path(), "pgsql/data/postgresql.conf")

    def __init__(self):
        self.check_package()

        self.__CONN_KWARGS = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": None,
            "database": None,
            "connect_timeout": 3,
        }
        self.__DB_CONN = None
        self.__DB_CUR = None

    # 检查python包是否存在
    @classmethod
    def check_package(cls):
        """
        @name检测依赖是否正常
        """
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        except:
            os.system('btpip install psycopg2-binary')
            try:
                import psycopg2
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            except:
                return False
        return True

    # 连接PGSQL数据库
    def connect(self) -> Tuple[bool, str]:
        is_localhost = self.__CONN_KWARGS["host"] in ["localhost", "127.0.0.1"]

        if is_localhost:
            self.__CONN_KWARGS["port"] = self.get_config_options("port", int, 5432)

            if self.__CONN_KWARGS.get("password") is None:
                tmp_args = public.dict_obj()
                tmp_args.is_True = True
                self.__CONN_KWARGS["password"] = main().get_root_pwd(tmp_args)

        try:
            self.__DB_CONN = psycopg2.connect(**self.__CONN_KWARGS)
            self.__DB_CONN.autocommit = True
            self.__DB_CONN.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # <-- ADD THIS LINE

            self.__DB_CUR = self.__DB_CONN.cursor()
            return True, "正常"
        except:
            err_msg = public.get_error_info()
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
            kwargs["database"] = args[2]
            kwargs["user"] = args[3]
            kwargs["password"] = args[4]

        if kwargs.get("db_host") is not None:
            kwargs["host"] = kwargs.get("db_host")
        if kwargs.get("db_port") is not None:
            kwargs["port"] = kwargs.get("db_port")
        if kwargs.get("db_name") is not None:
            kwargs["database"] = kwargs.get("db_name")
        if kwargs.get("db_user") is not None:
            kwargs["user"] = kwargs.get("db_user")
        if kwargs.get("db_password") is not None:
            kwargs["password"] = kwargs.get("db_password")
        self.__CONN_KWARGS.update(kwargs)

        if not isinstance(self.__CONN_KWARGS["port"], int):
            self.__CONN_KWARGS["port"] = int(self.__CONN_KWARGS["port"])
        return self

    def execute(self, sql):
        # 执行SQL语句返回受影响行
        if self.__DB_CONN is None:
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        if self.__DB_CONN.closed or self.__DB_CUR.closed:  # 判断是否关闭，关闭重新连接
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        try:
            # print(sql)
            result = self.__DB_CUR.execute(sql)
            self.__DB_CONN.commit()
            self.__Close()
            return result
        except Exception as ex:

            return ex

    def query(self, sql):

        # 执行SQL语句返回数据集
        if self.__DB_CONN is None:
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        if self.__DB_CONN.closed or self.__DB_CUR.closed:  # 判断是否关闭，关闭重新连接
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()

            data = list(map(list, result))
            self.__Close()
            return data
        except Exception as ex:
            return ex

    # 关闭连接
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()

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
        conf_obj = re.search(r"\n{}\s*=\s*([^\n]*)\n".format(name), conf_data)
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


class main(databaseBase, panelPgsql):
    _DB_BACKUP_DIR = os.path.join(public.M("config").where("id=?", (1,)).getField("backup_path"), "database")
    _PGSQL_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "pgsql")
    _PGDUMP_BIN = os.path.join(public.get_setup_path(), "pgsql/bin/pg_dump")
    _PSQL_BIN = os.path.join(public.get_setup_path(), "pgsql/bin/psql")

    __ser_name = None
    __soft_path = '/www/server/pgsql'
    __setup_path = '/www/server/panel/'
    __dbuser_info_path = "{}plugin/pgsql_manager_dbuser_info.json".format(__setup_path)
    __plugin_path = "{}plugin/pgsql_manager/".format(__setup_path)

    def __init__(self):
        if not os.path.exists(self._PGSQL_BACKUP_DIR):
            os.makedirs(self._PGSQL_BACKUP_DIR)

        s_path = public.get_setup_path()
        v_info = public.readFile("{}/pgsql/version.pl".format(s_path))
        if v_info:
            ver = v_info.split('.')[0]
            self.__ser_name = 'postgresql-x64-{}'.format(ver)
            self.__soft_path = '{}/pgsql/{}'.format(s_path)

    # 获取配置项
    def get_options(self, get):
        data = {}
        options = ['port', 'listen_addresses']
        if not self.__soft_path: self.__soft_path = '{}/pgsql'.format(public.get_setup_path())
        conf = public.readFile('{}/data/postgresql.conf'.format(self.__soft_path))
        for opt in options:
            tmp = re.findall("\s+" + opt + "\s*=\s*(.+)#", conf)
            if not tmp: continue
            data[opt] = tmp[0].strip()
            if opt == 'listen_addresses':
                data[opt] = data[opt].replace('\'', '')
        data['password'] = self.get_root_pwd(None)['msg']
        return data

    def get_list(self, args):
        """
        @获取数据库列表
        @sql_type = pgsql
        """
        return self.get_base_list(args, sql_type='pgsql')

    def get_sql_obj_by_sid(self, sid: Union[int, str] = 0, conn_config=None):
        """
        @取pgsql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if isinstance(sid, str):
            sid = int(sid)

        if sid:
            if not conn_config: conn_config = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('pgsql')", sid).find()
            db_obj = panelPgsql()

            try:
                db_obj = db_obj.set_host(host=conn_config["db_host"], port=conn_config["db_port"], database=None, user=conn_config["db_user"], password=conn_config["db_password"])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelPgsql()
        return db_obj

    def get_sql_obj(self, db_name):
        """
        @取pgsql数据库对象
        @db_name 数据库名称
        """
        is_cloud_db = False
        if db_name:
            db_find = public.M('databases').where("name=? AND LOWER(type)=LOWER('PgSql')", db_name).find()
            if db_find['sid']:
                return self.get_sql_obj_by_sid(db_find['sid'])
            is_cloud_db = db_find['db_type'] in ['1', 1]

        if is_cloud_db:

            db_obj = panelPgsql()
            conn_config = json.loads(db_find['conn_config'])
            try:
                db_obj = db_obj.set_host(host=conn_config["db_host"], port=conn_config["db_port"], database=conn_config["db_name"], user=conn_config["db_user"], password=conn_config["db_password"])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelPgsql()
        return db_obj

    def GetCloudServer(self, args):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        check_result = os.system('/www/server/pgsql/bin/psql --version')
        if check_result != 0 and not public.M('database_servers').where("LOWER(db_type)=LOWER('pgsql')", ()).count(): return []
        return self.GetBaseCloudServer(args)

    def AddCloudServer(self, args):
        '''
        @添加远程数据库
        '''
        return self.AddBaseCloudServer(args)

    def RemoveCloudServer(self, args):
        '''
        @删除远程数据库
        '''
        return self.RemoveBaseCloudServer(args)

    def ModifyCloudServer(self, args):
        '''
        @修改远程数据库
        '''
        return self.ModifyBaseCloudServer(args)

    def AddDatabase(self, args):
        """
        @添加数据库
        """
        if not hasattr(args, "name"):
            return public.returnMsg(False, "缺少参数！name")
        if not hasattr(args, "sid"):
            return public.returnMsg(False, "缺少参数！sid")

        db_name = args.name
        sid = args.sid

        if re.search(r"\W", db_name):
            return public.returnMsg(False, "数据库名不能包含特殊字符，请重新设置")
        if not str(sid).isdigit():
            return public.returnMsg(False, "参数错误！sid")
        sid = int(sid)

        dtype = "pgsql"
        res = self.add_base_database(args, dtype)
        if not res['status']: return res

        data_name = res['data_name']
        username = res['username']
        password = res['data_pwd']

        pgsql_obj = self.get_sql_obj_by_sid(sid)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")
        result = pgsql_obj.execute("""CREATE DATABASE "{}";""".format(data_name))
        isError = self.IsSqlError(result)
        if isError != None: return isError
        if str(result).find("permission denied to create database") != -1:
            return public.returnMsg(False, "创建数据库权限拒绝！")

        # 添加用户
        self.__CreateUsers(sid, data_name, username, password, '127.0.0.1')

        if not hasattr(args, 'ps'): args['ps'] = public.getMsg('INPUT_PS')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())

        pid = 0
        if hasattr(args, 'pid'): pid = args.pid

        if hasattr(args, 'contact'):
            site = public.M('sites').where("id=?", (args.contact,)).field('id,name').find()
            if site:
                pid = int(args.contact)
                args['ps'] = site['name']

        db_type = 0
        if sid: db_type = 2

        public.set_module_logs('pgsql', 'AddDatabase', 1)
        # 添加入SQLITE
        public.M('databases').add('pid,sid,db_type,name,username,password,accept,ps,addtime,type', (pid, sid, db_type, data_name, username, password, '127.0.0.1', args['ps'], addTime, dtype))
        public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS', (data_name,))
        return public.returnMsg(True, 'ADD_SUCCESS')

    def DeleteDatabase(self, get):
        """
        @删除数据库
        """
        id = get['id']
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).field('id,pid,name,username,password,accept,ps,addtime,db_type,conn_config,sid,type').find()
        if not find: return public.returnMsg(False, '指定数据库不存在.')

        name = get['name']
        username = find['username']

        pgsql_obj = self.get_sql_obj_by_sid(find['sid'])
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        pgsql_obj.execute("""DROP DATABASE "{}";""".format(name))
        pgsql_obj.execute("""DROP USER "{}";""".format(username))
        # 删除SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS', (name,))
        return public.returnMsg(True, 'DEL_SUCCESS')

    def ToBackup(self, args):
        """
        @备份数据库 id 数据库id
        """
        id = args['id']

        find = public.M('databases').where("id=?", (id,)).find()
        if not find: return public.returnMsg(False, '数据库不存在!')

        if not find['password'].strip():
            return public.returnMsg(False, '数据库密码为空，请先设置密码.')

        sql_dump = '{}/bin/pg_dump'.format(self.__soft_path)
        # return sql_dump
        if not os.path.isfile(sql_dump):
            return public.returnMsg(False, '缺少备份工具，请先通过软件商店pgsql管理器!')

        back_path = session['config']['backup_path'] + '/database/pgsql/'
        # return back_path
        if not os.path.exists(back_path): os.makedirs(back_path)

        fileName = find['name'] + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.sql'

        backupName = back_path + fileName

        if int(find['sid']):
            info = self.get_info_by_db_id(id)
            shell = '{} "host={} port={} user={} dbname={} password={}" > {}'.format(sql_dump, info['db_host'], info['db_port'], info['db_user'], find['name'], info['db_password'], backupName)
        else:
            args_one = public.dict_obj()
            port = self.get_port(args_one)
            shell = '{} "host=127.0.0.1 port={} user={} dbname={} password={}" > {}'.format(sql_dump, port['data'], find['username'], find['name'], find['password'], backupName)

        ret = public.ExecShell(shell)
        if not os.path.exists(backupName):
            return public.returnMsg(False, 'BACKUP_ERROR');

        public.M('backup').add('type,name,pid,filename,size,addtime', (1, fileName, id, backupName, 0, time.strftime('%Y-%m-%d %X', time.localtime())))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (find['name'],))

        if os.path.getsize(backupName) < 2048:
            return public.returnMsg(True, '备份执行成功，备份文件小于2Kb，请检查备份完整性.')
        else:
            return public.returnMsg(True, 'BACKUP_SUCCESS')

    def DelBackup(self, args):
        """
        @删除备份文件
        """
        return self.delete_base_backup(args)

    def get_port(self, args):  # 获取端口号
        str_shell = '''netstat -luntp|grep postgres|head -1|awk '{print $4}'|awk -F: '{print $NF}' '''
        try:
            port = public.ExecShell(str_shell)[0]
            if port.strip():
                return {'data': port.strip(), "status": True}
            else:
                return {'data': 5432, "status": False}
        except:
            return {'data': 5432, "status": False}

    # 导入
    def InputSql(self, get):

        name = get.name
        file = get.file
        # return name

        find = public.M('databases').where("name=?", (name,)).find()
        if not find: return public.returnMsg(False, '数据库不存在!')
        # return find
        if not find['password'].strip():
            return public.returnMsg(False, '数据库密码为空，请先设置密码.')

        tmp = file.split('.')
        exts = ['sql']
        ext = tmp[len(tmp) - 1]
        if ext not in exts:
            return public.returnMsg(False, '文件格式不正确,请上传sql文件.')

        sql_dump = '{}/bin/psql'.format(self.__soft_path)
        if not os.path.exists(sql_dump):
            return public.returnMsg(False, '缺少恢复工具，请先通过软件管理安装pgsql!')

        if int(find['sid']):
            info = self.get_info_by_db_id(find['id'])
            shell = '{} "host={} port={} user={} dbname={} password={}" < {}'.format(sql_dump, info['db_host'], info['db_port'], info['db_user'], find['name'], info['db_password'], file)
        else:
            args_one = public.dict_obj()
            port = self.get_port(args_one)
            shell = '{} "host=127.0.0.1 port={} user={} dbname={} password={}" < {}'.format(sql_dump, port['data'], find['username'], find['name'], find['password'], file)

        ret = public.ExecShell(shell)

        public.WriteLog("TYPE_DATABASE", '导入数据库[{}]成功'.format(name))
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS');

    def SyncToDatabases(self, get):
        """
        @name同步数据库到服务器
        """
        tmp_type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if tmp_type == 0:
            # data = sql.field('id,name,username,password,accept,type,sid,db_type').where('type=?',('pgsql',)).select()
            data = sql.field('id,name,username,password,accept,type,sid,db_type').where("LOWER(type)=LOWER('PgSql')", ()).select()

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

    def ToDataBase(self, find):
        """
        @name 添加到服务器
        """
        if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3:
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (find['id'],)).save('password,username', (find['password'], find['username']))

        sid = find['sid']
        pgsql_obj = self.get_sql_obj_by_sid(sid)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        result = pgsql_obj.execute("""CREATE DATABASE "{}";""".format(find['name']))
        isError = self.IsSqlError(result)
        if isError != None and isError['status'] == False and isError['msg'] == '指定数据库已存在，请勿重复添加.': return 1

        self.__CreateUsers(sid, find['name'], find['username'], find['password'], '127.0.0.1')

        return 1

    def SyncGetDatabases(self, get):
        """
        @name 从服务器获取数据库
        @param sid 0为本地数据库 1为远程数据库
        """
        n = 0
        s = 0
        db_type = 0
        sid = get.get('sid/d', 0)
        if sid: db_type = 2

        pgsql_obj = self.get_sql_obj_by_sid(sid)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        data = pgsql_obj.query('SELECT datname FROM pg_database;')  # select * from pg_database order by datname
        isError = self.IsSqlError(data)
        if isError != None: return isError
        if type(data) == str: return public.returnMsg(False, data)

        sql = public.M('databases')
        nameArr = ['information_schema', 'postgres', 'template1', 'template0', 'performance_schema', 'mysql', 'sys', 'master', 'model', 'msdb', 'tempdb', 'ReportServerTempDB', 'YueMiao', 'ReportServer']
        for item in data:
            dbname = item[0]
            if dbname in nameArr: continue

            if sql.where("name=? AND LOWER(type)=LOWER('PgSql')", (dbname,)).count(): continue
            if sql.table('databases').add('name,username,password,accept,ps,addtime,type,sid,db_type', (dbname, dbname, "", "", public.getMsg('INPUT_PS'), time.strftime('%Y-%m-%d %X', time.localtime()), 'PgSql', sid, db_type)): n += 1

        return public.returnMsg(True, 'DATABASE_GET_SUCCESS', (str(n),))

    def ResDatabasePassword(self, args):
        """
        @修改用户密码
        """
        id = args['id']
        username = args['name'].strip()
        newpassword = public.trim(args['password'])
        if not newpassword: return public.returnMsg(False, '修改失败，数据库密码不能为空.')

        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid').find()
        if not find: return public.returnMsg(False, '修改失败，指定数据库不存在.')

        pgsql_obj = self.get_sql_obj_by_sid(find['sid'])
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        data = pgsql_obj.query('SELECT rolname FROM pg_roles;')
        if username not in data:
            # 添加用户
            result = self.__CreateUsers(find['sid'], username, username, newpassword, "127.0.0.0.1")
        else:
            result = pgsql_obj.execute("""ALTER USER "{}" with password '{}';""".format(username, newpassword))
        isError = self.IsSqlError(result)
        if isError != None: return isError

        # 修改SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).setField('password', newpassword)

        public.WriteLog("TYPE_DATABASE", 'DATABASE_PASS_SUCCESS', (find['name'],))
        return public.returnMsg(True, 'DATABASE_PASS_SUCCESS', (find['name'],))

    def get_root_pwd(self, args):
        """
        @获取sa密码
        """
        # check_result = os.system('/www/server/pgsql/bin/psql1 --version')
        if not os.path.exists("/www/server/pgsql/bin/psql"): return public.returnMsg(False, '检测到PgSQL未安装或未启动，请先安装或启动')
        password = ''
        path = '{}/data/postgresAS.json'.format(public.get_panel_path())
        if os.path.isfile(path):
            try:
                password = json.loads(public.readFile(path))['password']
                # print('333333333')
                # print(password)
            except:
                pass
        if 'is_True' in args and args.is_True: return password
        return public.returnMsg(True, password)

    def set_root_pwd(self, args):
        """
        @设置sa密码
        """
        password = public.trim(args['password'])
        if len(password) < 8: return public.returnMsg(False, '密码输入错误，不能少于8位数.')
        check_result = os.system('/www/server/pgsql/bin/psql --version')
        if check_result != 0: return public.returnMsg(False, '检测到PgSQL未安装或未启动，请先安装或启动')
        pgsql_obj = self.get_sql_obj_by_sid('0')
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        data = pgsql_obj.query('SELECT datname FROM pg_database;')
        isError = self.IsSqlError(data)
        if isError != None: return isError

        path = '{}/data/pg_hba.conf'.format(self.__soft_path)
        p_path = '{}/data/postgresAS.json'.format(public.get_panel_path())
        if not os.path.isfile(path): return public.returnMsg(False, '{}文件不存在，请检查安装是否完整！'.format(path))
        src_conf = public.readFile(path)
        add_conf = src_conf.replace('md5', 'trust')
        # public.writeFile(path,public.readFile(path).replace('md5','trust'))
        public.writeFile(path, add_conf)

        pg_obj = panelPgsql()
        pg_obj.execute("""ALTER USER "postgres" WITH PASSWORD '{}';""".format(password))
        data = {"username": "postgres", "password": ""}
        try:
            data = json.loads(public.readFile(p_path))
        except:
            pass
        data['password'] = password
        public.writeFile(p_path, json.dumps(data))
        public.writeFile(path, src_conf)
        return public.returnMsg(True, '管理员密码修改成功.')

    def get_info_by_db_id(self, db_id):
        """
        @获取数据库连接详情
        @db_id 数据库id
        """
        # print(db_id,'111111111111')
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('pgsql')", db_id).find()
        # return find
        if not find: return False
        # print(find)
        if find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        elif find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('pgsql')", find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        else:  # 本地数据库
            db_host = '127.0.0.1'
            args_one = public.dict_obj()
            db_port = self.get_port(args_one)
            db_user = "postgres"
            t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            db_password = json.loads(public.readFile(t_path)).get("password", "")
        data = {
            'db_name': find["name"],
            'db_host': db_host,
            'db_port': int(db_port),
            'db_user': db_user,
            'db_password': db_password,
        }
        return data

    def get_database_size_by_id(self, args):
        """
        @获取数据库尺寸（批量删除验证）
        @args json/int 数据库id
        """
        total = 0
        db_id = args
        if not isinstance(args, int): db_id = args['db_id']

        try:
            name = public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", db_id).getField('name')
            sql_obj = self.get_sql_obj(name)
            tables = sql_obj.query("select name,size,type from sys.master_files where type=0 and name = '{}'".format(name))

            total = tables[0][1]
            if not total: total = 0
        except:
            pass

        return total

    def check_del_data(self, args):
        """
        @删除数据库前置检测
        """
        return self.check_base_del_data(args)

    # 本地创建数据库
    def __CreateUsers(self, sid, data_name, username, password, address):
        """
        @创建数据库用户
        """
        sql_obj = self.get_sql_obj_by_sid(sid)
        sql_obj.execute("""CREATE USER "{}" WITH PASSWORD '{}';""".format(username, password))
        sql_obj.execute("""GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}";""".format(data_name, username))
        return True

    def __get_db_list(self, sql_obj):
        """
        获取pgsql数据库列表
        """
        data = []
        ret = sql_obj.query('SELECT datname FROM pg_database;')
        if type(ret) == list:
            for x in ret:
                data.append(x[0])
        return data

    def __new_password(self):
        """
        生成随机密码
        """
        import random
        import string
        # 生成随机密码
        password = "".join(random.sample(string.ascii_letters + string.digits, 16))
        return password

    def CheckDatabaseStatus(self, get):
        """
        数据库状态检测
        """
        if not hasattr(get, "sid"):
            return public.returnMsg(False, "缺少参数！sid")
        if not str(get.sid).isdigit():
            return public.returnMsg(False, "参数错误！sid")
        sid = int(get.sid)

        pgsql_obj = panelPgsql()
        if sid == 0:
            db_status, err_msg = pgsql_obj.connect()
        else:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('pgsql')", (sid,)).find()
            if not conn_config:
                db_status = False
                err_msg = "远程数据库信息不存在！"
            else:
                pgsql_obj.set_host(host=conn_config["db_host"], port=conn_config["db_port"], database=None, user=conn_config["db_user"], password=conn_config["db_password"])
                db_status, err_msg = pgsql_obj.connect()

        return {"status": True, "msg": "正常" if db_status is True else "异常", "db_status": db_status, "err_msg": err_msg}

    def check_cloud_database_status(self, conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        旧方法，添加数据库时调用
        """
        try:
            if conn_config.get("db_name"): conn_config["db_name"] = None
            pgsql_obj = panelPgsql().set_host(host=conn_config['db_host'], port=conn_config['db_port'], database=None, user=conn_config['db_user'], password=conn_config['db_password'])

            status, err_msg = pgsql_obj.connect()
            if status is False:
                return {"status": False, "msg": "远程数据库连接失败!"}
            return status
        except:
            return public.returnMsg(False, "远程数据库连接失败！")
