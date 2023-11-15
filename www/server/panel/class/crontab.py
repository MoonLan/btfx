# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: sww <hwl@bt.cn>
# +-------------------------------------------------------------------

import json
import os
import re
import time
import traceback

import requests

import public

try:
    from BTPanel import cache
except:
    pass


class crontab:
    field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress,save_local,notice,notice_channel,db_type,split_type,split_value'

    def __init__(self):
        cront = public.M('crontab').order("id desc").field(self.field).select()
        if type(cront) == str:
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save_local' INTEGER DEFAULT 0", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice' INTEGER DEFAULT 0", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice_channel' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'db_type' TEXT DEFAULT ''", ())
            public.M('crontab').execute("UPDATE 'crontab' SET 'db_type'='mysql' WHERE sType='database' and db_type=''",
                                        ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'split_type' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'split_value' INTEGER DEFAULT 0", ())

    # 设置置顶
    def set_task_top(self, get=None):
        """
        设置任务置顶，不传参数查询设置的计划任务列表
        :param get: task_id
        :return:
        """
        cron_task_top_path = '/www/server/panel/data/cron_task_top'
        if os.path.exists(cron_task_top_path):
            task_top = json.loads(public.readFile(cron_task_top_path))
        else:
            task_top = {'list': []}
        if get and hasattr(get, 'task_id'):
            task_top['list'] = [i for i in task_top['list'] if i != get['task_id']]
            task_top['list'].append(get['task_id'])
            public.writeFile(cron_task_top_path, json.dumps(task_top))
            return public.returnMsg(True, '设置置顶成功！')
        return task_top

    # 取消置顶
    def cancel_top(self, get):
        """
        取消任务置顶
        :param get:task_id
        :return:
        """
        cron_task_top_path = '/www/server/panel/data/cron_task_top'
        if os.path.exists(cron_task_top_path):
            task_top = json.loads(public.readFile(cron_task_top_path))
        else:
            return public.returnMsg(True, '取消置顶成功！')
        if hasattr(get, 'task_id'):
            task_top['list'].remove(get['task_id'])
            public.writeFile(cron_task_top_path, json.dumps(task_top))
            return public.returnMsg(True, '取消置顶成功！')
        else:
            return public.returnMsg(False, '请传入取消置顶ID！')

    # 取计划任务列表
    def GetCrontab(self, get):

        self.checkBackup()
        self.__clean_log()
        cront = public.M('crontab').order("id desc").field(self.field).select()
        #
        # # sqllit分组查询
        # if hasattr(get, 'group_by'):
        #     if get.group_by != '':
        #         cront = public.M('crontab').where('type=?', (get.group_by,)).select()
        data = []
        for i in range(len(cront)):
            tmp = {}
            tmp = cront[i]
            if cront[i]['type'] == "day":
                tmp['type'] = public.getMsg('CRONTAB_TODAY')
                tmp['cycle'] = public.getMsg('CRONTAB_TODAY_CYCLE',
                                             (str(cront[i]['where_hour']), str(cront[i]['where_minute'])))
            elif cront[i]['type'] == "day-n":
                tmp['type'] = public.getMsg('CRONTAB_N_TODAY', (str(cront[i]['where1']),))
                tmp['cycle'] = public.getMsg('CRONTAB_N_TODAY_CYCLE', (
                    str(cront[i]['where1']), str(cront[i]['where_hour']), str(cront[i]['where_minute'])))
            elif cront[i]['type'] == "hour":
                tmp['type'] = public.getMsg('CRONTAB_HOUR')
                tmp['cycle'] = public.getMsg('CRONTAB_HOUR_CYCLE', (str(cront[i]['where_minute']),))
            elif cront[i]['type'] == "hour-n":
                tmp['type'] = public.getMsg('CRONTAB_N_HOUR', (str(cront[i]['where1']),))
                tmp['cycle'] = public.getMsg('CRONTAB_N_HOUR_CYCLE',
                                             (str(cront[i]['where1']), str(cront[i]['where_minute'])))
            elif cront[i]['type'] == "minute-n":
                tmp['type'] = public.getMsg('CRONTAB_N_MINUTE', (str(cront[i]['where1']),))
                tmp['cycle'] = public.getMsg('CRONTAB_N_MINUTE_CYCLE', (str(cront[i]['where1']),))
            elif cront[i]['type'] == "week":
                tmp['type'] = public.getMsg('CRONTAB_WEEK')
                if not cront[i]['where1']: cront[i]['where1'] = '0'
                tmp['cycle'] = public.getMsg('CRONTAB_WEEK_CYCLE', (
                    self.toWeek(int(cront[i]['where1'])), str(cront[i]['where_hour']),
                    str(cront[i]['where_minute'])))
            elif cront[i]['type'] == "month":
                tmp['type'] = public.getMsg('CRONTAB_MONTH')
                tmp['cycle'] = public.getMsg('CRONTAB_MONTH_CYCLE', (
                    str(cront[i]['where1']), str(cront[i]['where_hour']), str(cront[i]['where_minute'])))

            log_file = '/www/server/cron/{}.log'.format(tmp['echo'])
            if os.path.exists(log_file):
                tmp['addtime'] = self.get_last_exec_time(log_file)
            data.append(tmp)
        top_list = self.set_task_top()['list']
        if top_list:
            top_list = top_list[::-1]
        top_data = [item for item in data if str(item['id']) in top_list]
        data1 = [item for item in data if str(item['id']) not in top_list]
        top_data.sort(key=lambda x: top_list.index(str(x['id'])))
        data = top_data + data1
        if hasattr(get, 'search'):
            if get.search != '':
                data = [
                    item for item in data if
                    get.search in item['name']
                    or get.search in item['sName']
                    or get.search in item['type']
                    or get.search in item['addtime']
                ]
        # count = len(data)
        # p = int(get['p']) if hasattr(get, 'p') else 1
        # rows = int(get['rows']) if hasattr(get, 'rows') else 10
        # data1 = public.get_page(count, p, rows)
        # data1['data'] = data[int(data1['shift']) * int(data1['row']):(int(data1['shift']) + 1) * int(data1['row'])]
        return data

    def get_backup_list(self, args):
        '''
            @name 获取指定备份任务的备份文件列表
            @author hwliang
            @param args<dict> 参数{
                cron_id<int> 任务ID 必填
                p<int> 页码 默认1
                rows<int> 每页显示条数 默认10
                callback<string> jsonp回调函数  默认为空
            }
            @return <dict>{
                page<str> 分页HTML
                data<list> 数据列表
            }
        '''

        p = args.get('p/d', 1)
        rows = args.get('rows/d', 10)
        tojs = args.get('tojs/s', '')
        callback = args.get('callback/s', '') if tojs else tojs

        cron_id = args.get('cron_id/d')
        count = public.M('backup').where('cron_id=?', (cron_id,)).count()
        data = public.get_page(count, p, rows, callback)
        data['data'] = public.M('backup').where('cron_id=?', (cron_id,)).limit(data['row'], data['shift']).select()
        return data

    def get_last_exec_time(self, log_file):
        '''
            @name 获取上次执行时间
            @author hwliang
            @param log_file<string> 日志文件路径
            @return format_date
        '''
        exec_date = ''
        try:
            log_body = public.GetNumLines(log_file, 20)
            if log_body:
                log_arr = log_body.split('\n')
                date_list = []
                for i in log_arr:
                    if i.find('★') != -1 and i.find('[') != -1 and i.find(']') != -1:
                        date_list.append(i)
                if date_list:
                    exec_date = date_list[-1].split(']')[0].split('[')[1]
        except:
            pass

        finally:
            if not exec_date:
                exec_date = public.format_date(times=int(os.path.getmtime(log_file)))
        return exec_date

    # 清理日志
    def __clean_log(self):
        try:
            log_file = '/www/server/cron'
            if not os.path.exists(log_file): return False
            for f in os.listdir(log_file):
                if f[-4:] != '.log': continue
                filename = log_file + '/' + f
                if os.path.getsize(filename) < 1048576 / 2: continue
                tmp = public.GetNumLines(filename, 100)
                public.writeFile(filename, tmp)
        except:
            pass

    # 转换大写星期
    def toWeek(self, num):
        wheres = {
            0: public.getMsg('CRONTAB_SUNDAY'),
            1: public.getMsg('CRONTAB_MONDAY'),
            2: public.getMsg('CRONTAB_TUESDAY'),
            3: public.getMsg('CRONTAB_WEDNESDAY'),
            4: public.getMsg('CRONTAB_THURSDAY'),
            5: public.getMsg('CRONTAB_FRIDAY'),
            6: public.getMsg('CRONTAB_SATURDAY')
        }
        try:
            return wheres[num]
        except:
            return ''

    # 检查环境
    def checkBackup(self):
        if cache.get('check_backup'): return None

        # 检查备份表是否正确
        if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?',
                                               ('table', 'backup', '%cron_id%')).count():
            public.M('backup').execute("ALTER TABLE 'backup' ADD 'cron_id' INTEGER DEFAULT 0", ())

        # 检查备份脚本是否存在
        filePath = public.GetConfigValue('setup_path') + '/panel/script/backup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/backup.sh', filePath)
        # 检查日志切割脚本是否存在
        filePath = public.GetConfigValue('setup_path') + '/panel/script/logsBackup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/logsBackup.py', filePath)
        # 检查计划任务服务状态
        import system
        sm = system.system()
        if os.path.exists('/etc/init.d/crond'):
            if not public.process_exists('crond'): public.ExecShell('/etc/init.d/crond start')
        elif os.path.exists('/etc/init.d/cron'):
            if not public.process_exists('cron'): public.ExecShell('/etc/init.d/cron start')
        elif os.path.exists('/usr/lib/systemd/system/crond.service'):
            if not public.process_exists('crond'): public.ExecShell('systemctl start crond')
        cache.set('check_backup', True, 3600)

    # 设置计划任务状态
    def set_cron_status(self, get):
        id = get['id']
        cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()
        status_msg = ['停用', '启用']
        status = 1
        if cronInfo['status'] == status:
            status = 0
            self.remove_for_crond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            if not self.sync_to_crond(cronInfo):
                return public.returnMsg(False, '写入计划任务失败,请检查磁盘是否可写或是否开启了系统加固!')

        public.M('crontab').where('id=?', (id,)).setField('status', status)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']状态为[' + status_msg[status] + ']')
        return public.returnMsg(True, '设置成功')


    # 修改计划任务
    def modify_crond(self, get):
        if hasattr(get, 'sType'):
            if get['sType'] == 'toShell':
                get.sBody = get.sBody.replace('\r\n', '\n')
        if len(get['name']) < 1:
            return public.returnMsg(False, 'CRONTAB_TASKNAME_EMPTY')
        id = get['id']
        cuonConfig, get, name = self.GetCrondCycle(get)
        cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()
        projectlog = self.modify_project_log_split(cronInfo, get)
        if projectlog.modify():
            return public.returnMsg(projectlog.flag, projectlog.msg)
        if not get['where1']: get['where1'] = get['week']
        del (cronInfo['id'])
        del (cronInfo['addtime'])
        cronInfo['name'] = get['name']
        if hasattr(get, 'sType'):
            if cronInfo['sType'] == "sync_time": cronInfo['sName'] = get['sName']
        cronInfo['type'] = get['type']
        cronInfo['where1'] = get['where1']
        cronInfo['where_hour'] = get['hour']
        cronInfo['where_minute'] = get['minute']
        cronInfo['save'] = get['save']
        cronInfo['backupTo'] = get['backupTo']
        cronInfo['sBody'] = get['sBody']
        cronInfo['urladdress'] = get['urladdress']
        columns = 'name,type,where1,where_hour,where_minute,save,backupTo,sName,sBody,urladdress'
        values = (get['name'], get['type'], get['where1'], get['hour'],
                  get['minute'], get['save'], get['backupTo'], cronInfo['sName'], get['sBody']
                  , get['urladdress'])
        if 'save_local' in get:
            columns += ",save_local, notice, notice_channel"
            values = (get['name'], get['type'], get['where1'], get['hour'],
                      get['minute'], get['save'], get['backupTo'], cronInfo['sName'], get['sBody'],
                      get['urladdress'], get['save_local'], get["notice"],
                      get["notice_channel"])
        self.remove_for_crond(cronInfo['echo'])
        if cronInfo['status'] == 0: return public.returnMsg(False, '当前任务处于停止状态,请开启任务后再修改!')
        if not self.sync_to_crond(cronInfo):
            return public.returnMsg(False, '写入计划任务失败,请检查磁盘是否可写或是否开启了系统加固!')
        public.M('crontab').where('id=?', (id,)).save(columns, values)

        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']成功')
        return public.returnMsg(True, '修改成功')

    # 获取指定任务数据
    def get_crond_find(self, get):
        id = int(get.id)
        data = public.M('crontab').where('id=?', (id,)).field(self.field).find()
        return data

    # 同步到crond
    def sync_to_crond(self, cronInfo):
        if not 'status' in cronInfo: return False
        if 'where_hour' in cronInfo:
            cronInfo['hour'] = cronInfo['where_hour']
            cronInfo['minute'] = cronInfo['where_minute']
            cronInfo['week'] = cronInfo['where1']
        cuonConfig, cronInfo, name = self.GetCrondCycle(cronInfo)
        cronPath = public.GetConfigValue('setup_path') + '/cron'
        cronName = self.GetShell(cronInfo)
        if type(cronName) == dict: return cronName
        # cuonConfig += ' ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'

        if cronInfo['type'] == 'minute-n' and int(cronInfo['where1']) < 10:
            flock_name = cronPath + '/' + cronName + '.lock'
            public.writeFile(flock_name, '')
            os.system('chmod 777 {}'.format(flock_name))
            cuonConfig += ' flock -xn ' + cronPath + '/' + cronName + '.lock' + ' -c ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
        else:
            cuonConfig += ' ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
        wRes = self.WriteShell(cuonConfig)
        if type(wRes) != bool: return False
        self.CrondReload()
        return True

    # 添加计划任务
    def AddCrontab(self, get):
        if len(get['name']) < 1:
            return public.returnMsg(False, 'CRONTAB_TASKNAME_EMPTY')
        if get == 'toShell':
            get['sBody'] = get['sBody'].replace('\r\n', '\n')
        cuonConfig, get, name = self.GetCrondCycle(get)
        cronPath = public.GetConfigValue('setup_path') + '/cron'
        cronName = self.GetShell(get)
        if type(cronName) == dict: return cronName
        if get['type'] == 'minute-n' and int(get['where1']) < 10:
            flock_name = cronPath + '/' + cronName + '.lock'
            public.writeFile(flock_name, '')
            os.system('chmod 777 {}'.format(flock_name))
            cuonConfig += ' flock -xn ' + cronPath + '/' + cronName + '.lock' + ' -c ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
        else:
            cuonConfig += ' ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
        wRes = self.WriteShell(cuonConfig)
        if type(wRes) != bool: return wRes
        self.CrondReload()
        columns = 'name,type,where1,where_hour,where_minute,echo,addtime,\
                  status,save,backupTo,sType,sName,sBody,urladdress,db_type'
        values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                  get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                  1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                  get['urladdress'], get.get("db_type"),)
        if "save_local" in get:
            columns += ",save_local,notice,notice_channel"
            values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                      get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                      1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                      get['urladdress'], get.get("db_type"), get["save_local"], get['notice'], get['notice_channel'])
        addData = public.M('crontab').add(columns, values)
        public.add_security_logs('计划任务', '添加计划任务[' + get['name'] + ']成功' + str(values))
        if type(addData) == str:
            return public.returnMsg(False, addData)
        public.WriteLog('计划任务', '添加计划任务[' + get['name'] + ']成功')
        if addData > 0:
            result = public.returnMsg(True, 'ADD_SUCCESS')
            result['id'] = addData
            return result
        return public.returnMsg(False, 'ADD_ERROR')

    # 构造周期
    def GetCrondCycle(self, params):
        cuonConfig = ""
        name = ""
        if params['type'] == "day":
            cuonConfig = self.GetDay(params)
            name = public.getMsg('CRONTAB_TODAY')
        elif params['type'] == "day-n":
            cuonConfig = self.GetDay_N(params)
            name = public.getMsg('CRONTAB_N_TODAY', (params['where1'],))
        elif params['type'] == "hour":
            cuonConfig = self.GetHour(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type'] == "hour-n":
            cuonConfig = self.GetHour_N(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type'] == "minute-n":
            cuonConfig = self.Minute_N(params)
        elif params['type'] == "week":
            params['where1'] = params['week']
            cuonConfig = self.Week(params)
        elif params['type'] == "month":
            cuonConfig = self.Month(params)
        return cuonConfig, params, name

    # 取任务构造Day
    def GetDay(self, param):
        cuonConfig = "{0} {1} * * * ".format(param['minute'], param['hour'])
        return cuonConfig

    # 取任务构造Day_n
    def GetDay_N(self, param):
        cuonConfig = "{0} {1} */{2} * * ".format(param['minute'], param['hour'], param['where1'])
        return cuonConfig

    # 取任务构造Hour
    def GetHour(self, param):
        cuonConfig = "{0} * * * * ".format(param['minute'])
        return cuonConfig

    # 取任务构造Hour-N
    def GetHour_N(self, param):
        cuonConfig = "{0} */{1} * * * ".format(param['minute'], param['where1'])
        return cuonConfig

    # 取任务构造Minute-N
    def Minute_N(self, param):
        cuonConfig = "*/{0} * * * * ".format(param['where1'])
        return cuonConfig

    # 取任务构造week
    def Week(self, param):
        cuonConfig = "{0} {1} * * {2}".format(param['minute'], param['hour'], param['week'])
        return cuonConfig

    # 取任务构造Month
    def Month(self, param):
        cuonConfig = "{0} {1} {2} * * ".format(param['minute'], param['hour'], param['where1'])
        return cuonConfig

    # 取数据列表
    def GetDataList(self, get):
        try:
            data = {}
            if get['type'] == 'databases':
                data['data'] = public.M(get['type']).where("type=?", "MySQL").field('name,ps').select()
            else:
                data['data'] = public.M(get['type']).field('name,ps').select()
            for i in data['data']:
                if 'ps' in i:
                    try:
                        if i['ps'] is None: continue
                        i['ps'] = public.xsssec(i['ps'])  # 防止数据库为空时，xss防御报错  2020-11-25
                    except:
                        pass
            data['orderOpt'] = []
            import json
            tmp = public.readFile('data/libList.conf')
            if not tmp: return data
            libs = json.loads(tmp)
            for lib in libs:
                if not 'opt' in lib: continue
                filename = 'plugin/{}'.format(lib['opt'])
                if not os.path.exists(filename): continue
                tmp = {}
                tmp['name'] = lib['name']
                tmp['value'] = lib['opt']
                data['orderOpt'].append(tmp)
            return data
        except:
            return public.returnMsg(False,traceback.format_exc())

    # 取任务日志
    def GetLogs(self, get):
        try:
            id = get['id']
            echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
            if not os.path.exists(logFile): return public.returnMsg(False, 'CRONTAB_TASKLOG_EMPTY')
            log = public.GetNumLines(logFile, 2000)
            return public.returnMsg(True, public.xsssec(log))
        except:
            pass

    # 清理任务日志
    def DelLogs(self, get):
        try:
            id = get['id']
            echo = public.M('crontab').where("id=?", (id,)).getField('echo')
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo + '.log'
            os.remove(logFile)
            return public.returnMsg(True, 'CRONTAB_TASKLOG_CLOSE')
        except:
            return public.returnMsg(False, 'CRONTAB_TASKLOG_CLOSE_ERR')

    # 删除计划任务
    def DelCrontab(self, get):
        try:
            id = get['id']
            find = public.M('crontab').where("id=?", (id,)).field('name,echo').find()
            if not find: return public.returnMsg(False, '指定任务不存在!')
            if not self.remove_for_crond(find['echo']): return public.returnMsg(False,
                                                                                '无法写入文件，请检查是否开启了系统加固功能!')
            cronPath = public.GetConfigValue('setup_path') + '/cron'
            sfile = cronPath + '/' + find['echo']
            if os.path.exists(sfile): os.remove(sfile)
            sfile = cronPath + '/' + find['echo'] + '.log'
            if os.path.exists(sfile): os.remove(sfile)

            public.M('crontab').where("id=?", (id,)).delete()
            public.add_security_logs("删除计划任务", "删除计划任务:" + find['name'])
            public.WriteLog('TYPE_CRON', 'CRONTAB_DEL', (find['name'],))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except:
            return public.returnMsg(False, 'DEL_ERROR')

    # 从crond删除
    def remove_for_crond(self, echo):
        file = self.get_cron_file()
        if not os.path.exists(file):
            return False
        conf = public.readFile(file)
        if not conf: return False
        if conf.find(str(echo)) == -1: return True
        rep = ".+" + str(echo) + ".+\n"
        conf = re.sub(rep, "", conf)
        try:
            if not public.writeFile(file, conf): return False
        except:
            return False
        self.CrondReload()
        return True

    # 取执行脚本
    def GetShell(self, param):
        # try:
        type = param['sType']
        if not 'echo' in param:
            cronName = public.md5(public.md5(str(time.time()) + '_bt'))
        else:
            cronName = param['echo']
        if type == 'toFile':
            shell = param.sFile
        else:
            head = "#!/bin/bash\nPATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin\nexport PATH\n"
            log = '-access_log'
            python_bin = "{} -u".format(public.get_python_bin())
            if public.get_webserver() == 'nginx':
                log = '.log'
            if type in ['site', 'path'] and param['sBody'] != 'undefined' and len(param['sBody']) > 1:
                exclude_files = ','.join([n.strip() for n in param['sBody'].split('\n') if n.strip()])
                head += f'export BT_EXCLUDE="{exclude_files}"\n'
            attach_param = " " + cronName
            wheres = {
                'path': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/backup.py path " + param['sName'] + " " + str(
                    param['save']) + attach_param,
                'site': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/backup.py site " + param['sName'] + " " + str(
                    param['save']) + attach_param,
                'database': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/backup.py database " + param['sName'] + " " + str(
                    param['save']) + attach_param,
                'logs': head + python_bin + " " + public.GetConfigValue('setup_path') + "/panel/script/logsBackup " +
                        param['sName'] + " " + str(param['save']),
                'rememory': head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
                'sync_time': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/sync_time.py {}".format(param['sName']),
                'webshell': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] + ' ' + param['urladdress']
            }
            # 取消插件调用计划任务
            # if param['backupTo'] != 'localhost':
            #     cfile = public.GetConfigValue('setup_path') + "/panel/plugin/" + param['backupTo'] + "/" + param[
            #         'backupTo'] + "_main.py"
            #     if not os.path.exists(cfile): cfile = public.GetConfigValue('setup_path') + "/panel/script/backup_" + \
            #                                           param['backupTo'] + ".py"
            #     wheres = {
            #         'path': head + python_bin + " " + cfile + " path " + param['sName'] + " " + str(
            #             param['save']) + attach_param,
            #         'site': head + python_bin + " " + cfile + " site " + param['sName'] + " " + str(
            #             param['save']) + attach_param,
            #         'database': head + python_bin + " " + cfile + " database " + param['sName'] + " " + str(
            #             param['save']) + attach_param,
            #         'logs': head + python_bin + " " + public.GetConfigValue(
            #             'setup_path') + "/panel/script/logsBackup " + param['sName'] + " " + str(param['save']),
            #         'rememory': head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
            #         'webshell': head + python_bin + " " + public.GetConfigValue(
            #             'setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] + ' ' + param[
            #                         'urladdress']
            #     }

            try:
                shell = wheres[type]
            except:
                if type == 'toUrl':
                    shell = head + "curl -sS --connect-timeout 10 -m 3600 '" + param['urladdress'] + "'"
                else:
                    shell = head + param['sBody'].replace("\r\n", "\n")

            shell += '''
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
'''
        cronPath = public.GetConfigValue('setup_path') + '/cron'
        if not os.path.exists(cronPath): public.ExecShell('mkdir -p ' + cronPath)
        file = cronPath + '/' + cronName
        public.writeFile(file, self.CheckScript(shell))
        public.ExecShell('chmod 750 ' + file)
        return cronName
        # except Exception as ex:
        # return public.returnMsg(False, 'FILE_WRITE_ERR' + str(ex))

    # 检查脚本
    def CheckScript(self, shell):
        keys = ['shutdown', 'init 0', 'mkfs', 'passwd', 'chpasswd', '--stdin', 'mkfs.ext', 'mke2fs']
        for key in keys:
            shell = shell.replace(key, '[***]')
        return shell

    # 重载配置
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'):
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")

    # 将Shell脚本写到文件
    def WriteShell(self, config):
        u_file = '/var/spool/cron/crontabs/root'
        file = self.get_cron_file()
        if not os.path.exists(file): public.writeFile(file, '')
        conf = public.readFile(file)
        if type(conf) == bool: return public.returnMsg(False, '读取文件失败!')
        conf += config + "\n"
        if public.writeFile(file, conf):
            if not os.path.exists(u_file):
                public.ExecShell("chmod 600 '" + file + "' && chown root.root " + file)
            else:
                public.ExecShell("chmod 600 '" + file + "' && chown root.crontab " + file)
            return True
        return public.returnMsg(False, '文件写入失败,请检查是否开启系统加固功能!')

    # 立即执行任务
    def StartTask(self, get):
        echo = public.M('crontab').where('id=?', (get.id,)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell('nohup ' + execstr + ' >> ' + execstr + '.log 2>&1 &')
        return public.returnMsg(True, 'CRONTAB_TASK_EXEC')

    # 获取计划任务文件位置
    def get_cron_file(self):
        u_path = '/var/spool/cron/crontabs'
        u_file = u_path + '/root'
        c_file = '/var/spool/cron/root'
        cron_path = c_file
        if not os.path.exists(u_path):
            cron_path = c_file

        if os.path.exists("/usr/bin/apt-get"):
            cron_path = u_file
        elif os.path.exists('/usr/bin/yum'):
            cron_path = c_file

        if cron_path == u_file:
            if not os.path.exists(u_path):
                os.makedirs(u_path, 472)
                public.ExecShell("chown root:crontab {}".format(u_path))
        if not os.path.exists(cron_path):
            public.writeFile(cron_path, "")
        return cron_path

    def modify_project_log_split(self, cronInfo, get):

        def _test_project_type(self, project_type):
            if project_type == "Node项目":
                return "nodojsModel"
            elif project_type == "Java项目":
                return "javaModel"
            elif project_type == "GO项目":
                return "goModel"
            elif project_type == "其他项目":
                return "otherModel"
            elif project_type == "Python项目":
                return "pythonModel"
            else:
                return None

        def the_init(self, cronInfo, get: dict):
            self.get = get
            self.cronInfo = cronInfo
            self.msg = ""
            self.flag = False
            name = get["name"]
            if name.find("运行日志切割") != -1:
                try:
                    project_type, project_name = name.split("]", 2)[1].split("[", 1)
                    project_type = self._test_project_type(project_type)
                except:
                    self.project_type = None
                    return
            else:
                self.project_type = None
                return

            self.project_type = project_type
            self.project_name = project_name
            conf_path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
            data = json.loads(public.readFile(conf_path))
            self.log_size = int(data[self.project_name]["log_size"]) / 1024 / 1024

        def modify(self):
            from importlib import import_module
            if not self.project_type:
                return False
            if self.cronInfo["type"] != self.get['type']:
                self.msg = "运行日志切割不能修改执行周期的方式"
                return True
            get = public.dict_obj()
            get.name = self.project_name
            get.log_size = self.log_size
            if get.log_size != 0:
                get.hour = "2"
                get.minute = str(self.get['where1'])
            else:
                get.hour = str(self.get['hour'])
                get.minute = str(self.get['minute'])
            get.num = str(self.get["save"])

            model = import_module(".{}".format(self.project_type), package="projectModel")

            res = getattr(model.main(), "mamger_log_split")(get)
            self.msg = res["msg"]
            self.flag = res["status"]

            return True

        attr = {
            "__init__": the_init,
            "_test_project_type": _test_project_type,
            "modify": modify,
        }
        return type("ProjectLog", (object,), attr)(cronInfo, get)

    # 检查指定的url是否通
    def check_url_connecte(self, get):
        end_time = 0
        if 'url' not in get or get['url'] == '':
            return public.returnMsg(False, '请传入url!')
        try:
            start_time = time.time()
            response = requests.get(get.url, timeout=3)
            response.encoding = 'utf-8'
            end_time = time.time()
            if response.status_code == 200:
                return {'status': True, 'status_code': response.status_code,
                        'txt': public.xsssec(response.text),
                        'time': str(int(round(end_time - start_time, 2) * 1000)) + 'ms'}
            else:
                return {'status': False, 'status_code': response.status_code, 'txt': public.xsssec(response.text),
                        'time': str(int(round(end_time - start_time, 2) * 1000)) + 'ms'}
        except requests.exceptions.RequestException:
            return {'status': False, 'status_code': '', 'txt': '访问异常',
                    'time': '0ms'}

    # 获取各个类型数据库
    def GetDatabases(self, get):
        db_type = getattr(get, "db_type", "mysql")

        crontab_databases = public.M("crontab").field("id,sName").where("LOWER(type)=LOWER(?)", (db_type)).select()
        for db in crontab_databases:
            db["sName"] = set(db["sName"].split(","))

        if db_type == "redis":
            database_list = []
            cron_id = None
            for db in crontab_databases:
                if db_type in db["sName"]:
                    cron_id = db["id"]
                    break
            database_list.append({"name": "本地数据库", "ps": "", "cron_id": cron_id})
            return database_list

        databases = public.M("databases").field("name,ps").where("LOWER(type)=LOWER(?)", (db_type)).select()

        for database in databases:
            if database.get("name") is None: continue

            database["cron_id"] = []
            for db in crontab_databases:
                if database["name"] in db["sName"]:
                    database["cron_id"].append(db["id"])
        return databases
