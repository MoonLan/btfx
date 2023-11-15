# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <2020-08-04>
# +-------------------------------------------------------------------

import os, sys, json, time, public, datetime


class panelWarning:
    __path = '/www/server/panel/data/warning'
    __ignore = __path + '/ignore'
    __result = __path + '/result'
    __risk = __path + '/risk'
    _vuln_ignore = __path + '/ignore.json'
    _vuln_result = __path + '/result.json'
    __repair_count = __path + '/repair_count.json'
    __vul_list = __path + '/high_risk_vul-9.json'
    __report = '/www/server/panel/data/warning_report'
    vul_num = 0

    def __init__(self):
        if not os.path.exists(self.__ignore):
            os.makedirs(self.__ignore, 384)
        if not os.path.exists(self.__result):
            os.makedirs(self.__result, 384)
        if not os.path.exists(self.__risk):
            os.makedirs(self.__risk, 384)
        if not os.path.exists(self.__path):
            os.makedirs(self.__path, 384)
        if not os.path.exists(self.__report):
            os.makedirs(self.__report, 384)

        if not os.path.exists(self._vuln_ignore):
            result = []
            public.WriteFile(self._vuln_ignore, json.dumps(result))
        if not os.path.exists(self._vuln_result):
            result = []
            public.WriteFile(self._vuln_result, json.dumps(result))
        self.compare_md5()

    def get_list(self, args):
        p = public.get_modules('class/safe_warning')
        data = {
            'security': [],
            'risk': [],
            'ignore': []
        }
        public.WriteFile(self.__path + '/bar.txt', "0")  # 扫描进度条归零
        bar_num = 0  # 进度条初始化
        bar_limit = 0  # 进度条限制
        self.system_scan()
        for m_name in p.__dict__.keys():
            bar = ("%.2f" % (float(bar_num) / float(len(p.__dict__.keys())) * 50 + 50))
            #  通过进度条限制，防止写文件频繁占用高
            if int(float(bar)) >= bar_limit:
                public.WriteFile(self.__path + '/bar.txt', bar)
                bar_limit += 10
            bar_num += 1
            ignore_file = self.__ignore + '/' + m_name + '.pl'
            # 忽略的检查项
            if p[m_name]._level == 0: continue

            m_info = {
                'title': p[m_name]._title,
                'm_name': m_name,
                'ps': p[m_name]._ps,
                'version': p[m_name]._version,
                'level': p[m_name]._level,
                'ignore': p[m_name]._ignore,
                'date': p[m_name]._date,
                'tips': p[m_name]._tips,
                'help': p[m_name]._help
            }
            try:
                m_info['remind'] = p[m_name]._remind
            except:
                pass
            result_file = self.__result + '/' + m_name + '.pl'

            try:
                s_time = time.time()
                m_info['status'], m_info['msg'] = p[m_name].check_run()
                m_info['taking'] = round(time.time() - s_time, 6)
                m_info['check_time'] = int(time.time())
                public.writeFile(result_file, json.dumps(
                    [m_info['status'], m_info['msg'], m_info['check_time'], m_info['taking']], ))
            except:
                continue

            m_info['ignore'] = os.path.exists(ignore_file)
            if m_info['ignore']:
                data['ignore'].append(m_info)
            else:
                if m_info['status']:
                    data['security'].append(m_info)
                else:
                    risk_file = self.__risk + '/' + m_name + '.pl'
                    public.writeFile(risk_file, json.dumps(m_info))
                    data['risk'].append(m_info)

        vuln_result = self.get_vuln_result()
        data['risk'] = data['risk'] + vuln_result['risk']
        data['ignore'] = data['ignore'] + vuln_result['ignore']

        vuln_is_autofix = []
        for vr in vuln_result['risk']:
            if not vr["reboot"]:
                vuln_is_autofix.append(vr["cve_id"])
        data['risk'] = sorted(data['risk'], key=lambda x: x['level'], reverse=True)
        data['security'] = sorted(data['security'], key=lambda x: x['level'], reverse=True)
        data['ignore'] = sorted(data['ignore'], key=lambda x: x['level'], reverse=True)

        # 获取支持一键修复的列表
        try:
            is_autofix = public.read_config("safe_autofix")
        except:
            is_autofix = []
        data['is_autofix'] = is_autofix + vuln_is_autofix
        data['check_time'] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        # 将结果输出一份到报告目录下
        with open("/www/server/panel/data/warning_report/data.json", "w") as f:
            json.dump(data, f)
        self.record_times()
        public.WriteFile(self.__path + '/bar.txt', "100")  # 扫描进度条归零
        return data

    def sync_rule(self):
        '''
            @name 从云端同步规则
            @author hwliang<2020-08-05>
            @return void
        '''
        # try:
        #     dep_path = '/www/server/panel/class/safe_warning'
        #     local_version_file = self.__path + '/version.pl'
        #     last_sync_time = local_version_file = self.__path + '/last_sync.pl'
        #     if os.path.exists(dep_path):
        #         if os.path.exists(last_sync_time):
        #             if int(public.readFile(last_sync_time)) > time.time():
        #                 return
        #     else:
        #         if os.path.exists(local_version_file): os.remove(local_version_file)

        #     download_url = public.get_url()
        #     version_url = download_url + '/install/warning/version.txt'
        #     cloud_version = public.httpGet(version_url)
        #     if cloud_version: cloud_version = cloud_version.strip()

        #     local_version = public.readFile(local_version_file)
        #     if local_version:
        #         if cloud_version == local_version:
        #             return

        #     tmp_file = '/tmp/bt_safe_warning.zip'
        #     public.ExecShell('wget -O {} {} -T 5'.format(tmp_file,download_url + '/install/warning/safe_warning.zip'))
        #     if not os.path.exists(tmp_file):
        #         return

        #     if os.path.getsize(tmp_file) < 2129:
        #         os.remove(tmp_file)
        #         return

        #     if not os.path.exists(dep_path):
        #         os.makedirs(dep_path,384)
        #     public.ExecShell("unzip -o {} -d {}/ >/dev/null".format(tmp_file,dep_path))
        #     public.writeFile(local_version_file,cloud_version)
        #     public.writeFile(last_sync_time,str(int(time.time() + 7200)))
        #     if os.path.exists(tmp_file): os.remove(tmp_file)
        #     public.ExecShell("chmod -R 600 {}".format(dep_path))
        # except:
        #     pass

    def set_ignore(self, args):
        '''
            @name 设置指定项忽略状态
            @author hwliang<2020-08-04>
            @param dict_obj {
                m_name<string> 模块名称
            }
            @return dict
        '''
        m_name = args.m_name.strip()
        ignore_file = self.__ignore + '/' + m_name + '.pl'
        if os.path.exists(ignore_file):
            os.remove(ignore_file)
        else:
            public.writeFile(ignore_file, '1')
        return public.returnMsg(True, '设置成功!')

    def check_find(self, args):
        '''
            @name 检测指定项
            @author hwliang<2020-08-04>
            @param dict_obj {
                m_name<string> 模块名称
            }
            @return dict
        '''
        try:
            m_name = args.m_name.strip()
            p = public.get_modules('class/safe_warning')
            m_info = {
                'title': p[m_name]._title,
                'm_name': m_name,
                'ps': p[m_name]._ps,
                'version': p[m_name]._version,
                'level': p[m_name]._level,
                'ignore': p[m_name]._ignore,
                'date': p[m_name]._date,
                'tips': p[m_name]._tips,
                'help': p[m_name]._help
            }

            # 解决已经在忽略列表中，但是如果仍然需要检查的话可以检查
            ignore_file = self.__ignore + '/' + m_name + '.pl'
            if os.path.exists(ignore_file):
                from cachelib import SimpleCache
                cache = SimpleCache(5000)
                ikey = 'warning_list'
                cache.delete(ikey)
                os.remove(ignore_file)

            result_file = self.__result + '/' + m_name + '.pl'
            s_time = time.time()
            m_info['status'], m_info['msg'] = p[m_name].check_run()
            m_info['taking'] = round(time.time() - s_time, 4)
            m_info['check_time'] = int(time.time())
            public.writeFile(result_file, json.dumps(
                [m_info['status'], m_info['msg'], m_info['check_time'], m_info['taking']]))
            return public.returnMsg(True, '已重新检测')
        except:
            return public.returnMsg(False, '检测失败')

    def system_scan(self):
        '''
        一键扫描系统
        :param get:
        :return: dict
        '''
        self.compare_md5()
        sys_version = self.get_sys_version()
        # if sys_version == 'None':
        #     return public.returnMsg(False, '当前系统暂不支持')
        sys_product = self.get_sys_product()
        # if not os.path.exists(self.__vul_list):
        #     return public.returnMsg(False, "扫描失败")
        vul_list = self.get_vul_list()

        new_risk_list = []
        new_ignore_list = []
        # error_list = []
        result_dict = {}
        # cp_list = []
        vul_count = 0
        ignore_list = self.get_ignore_list()
        reboot_count = 0
        self.vul_num = len(vul_list)
        bar_num = 0  # 进度条初始化
        bar_limit = 0  # 进度条限制
        for vul in vul_list:
            bar = ("%.2f" % (float(bar_num)/float(self.vul_num)*50))
            # 限制进度条，限制写文件频率
            if int(float(bar)) >= bar_limit:
                public.WriteFile(self.__path+'/bar.txt', bar)
                bar_limit += 10
            bar_num += 1
            vul_count += 1
            for v in vul["affected_list"]:
                if v["manufacturer"] == sys_version:
                    tmp = 1  # 默认命中
                    if not 'affected' in v: continue
                    if "Up to (excluding)" in v['affected']:
                        arr = v['affected'].split("Up to (excluding)\n                                                ")
                    elif "Up to (including)" in v['affected']:
                        arr = v['affected'].split("Up to (including)\n                                                ")
                    else:
                        continue
                    if len(arr) < 2: continue
                    vul_version = arr[1]
                    try:
                        for soft in v["softname"]:
                            # 该规则没有更新，直接跳过
                            if soft == 'NONE':
                                tmp = 0
                                break
                            compare_result = self.version_compare(sys_product[soft], vul_version)
                            if compare_result >= 0:
                                tmp = 0  # 当有一个软件包版本不在漏洞范围内，则不命中
                                break
                        if tmp == 1:
                            # softname_list = [soft+'-'+sys_product[soft] for soft in v["softname"]]
                            # softname_list = [{soft: sys_product[soft]} for soft in v["softname"]]
                            softname_dict = {}
                            for soft in v["softname"]:
                                softname_dict[soft] = sys_product[soft]
                            level = self.get_score_risk(vul["score"])
                            vul_dict = {key: vul[key] for key in ["cve_id", "vuln_name", "vuln_time", "vuln_solution"]}
                            vul_dict["level"] = level
                            vul_dict["soft_name"] = softname_dict
                            vul_dict["vuln_version"] = vul_version
                            vul_dict["check_time"] = int(time.time())
                            vul_dict["reboot"] = ""
                            if "kernel" in [k for k in v["softname"]]:
                                vul_dict["reboot"] = "该漏洞属于内核漏洞，需要自行升级内核版本，建议升级之前做好快照以及备份\n可联系客服人工处理"
                                reboot_count += 1
                            if vul["cve_id"] in ignore_list:
                                new_ignore_list.append(vul_dict)
                                break
                            new_risk_list.append(vul_dict)
                            break
                        # cp_list.append(vul["cve_id"]+':    '+str([soft+'-'+sys_product[soft] for soft in v["softname"]])+'  >=  '+vul_version)
                    except Exception as e:
                        # error_list.append(vul["cve_id"]+':    '+str(e))
                        break
            result_dict["vul_count"] = vul_count
        result_dict["risk"] = new_risk_list
        result_dict["ignore"] = new_ignore_list
        # result_dict["reboot"] = self.__need_reboot
        # result_dict["error"] = error_list
        # result_dict["compare"] = cp_list
        public.WriteFile(self.__path + '/system_scan_time', int(time.time()))
        public.WriteFile(self._vuln_result, json.dumps(result_dict))
        # try:
        #     public.WriteFile(self._vuln_result, json.dumps(result_dict))
        #     return public.returnMsg(True, "扫描完成")
        # except:
        #     return public.returnMsg(False, "扫描失败")

    # 版本比较
    def version_compare(self, ver_a, ver_b):
        '''
        比较版本大小
        :param ver_a: 软件版本
        :param ver_b: 漏洞版本
        :return: int 大于等于返回1或0，小于返回-1
        '''
        if "ubuntu" in self.get_sys_version() or "debian" in self.get_sys_version():
            if ver_b.startswith("1:"):
                ver_b = ver_b[2:]
            # if ver_a.startswith("1:"):
            #     ver_a = ver_a[2:]
            result = public.ExecShell("dpkg --compare-versions " + ver_a + " ge " + ver_b + " && echo true")
            if 'warning' in result[1].strip(): return None
            if 'true' in result[0].strip():
                return 1
            else:
                return -1
        return self.vercmp(ver_a, ver_b)

    def vercmp(self, first, second):
        import re
        R_NONALNUMTILDE = re.compile(br"^([^a-zA-Z0-9~]*)(.*)$")
        R_NUM = re.compile(br"^([\d]+)(.*)$")
        R_ALPHA = re.compile(br"^([a-zA-Z]+)(.*)$")
        first = first.encode("ascii", "ignore")
        second = second.encode("ascii", "ignore")
        while first or second:
            m1 = R_NONALNUMTILDE.match(first)
            m2 = R_NONALNUMTILDE.match(second)
            m1_head, first = m1.group(1), m1.group(2)
            m2_head, second = m2.group(1), m2.group(2)
            if m1_head or m2_head:
                continue

            if first.startswith(b'~'):
                if not second.startswith(b'~'):
                    return -1
                first, second = first[1:], second[1:]
                continue
            if second.startswith(b'~'):
                return 1

            if not first or not second:
                break

            m1 = R_NUM.match(first)
            if m1:
                m2 = R_NUM.match(second)
                if not m2:
                    return 1
                isnum = True
            else:
                m1 = R_ALPHA.match(first)
                m2 = R_ALPHA.match(second)
                isnum = False

            if not m1:
                return -1
            if not m2:
                return 1 if isnum else -1

            m1_head, first = m1.group(1), m1.group(2)
            m2_head, second = m2.group(1), m2.group(2)

            if isnum:
                m1_head = m1_head.lstrip(b'0')
                m2_head = m2_head.lstrip(b'0')

                m1hlen = len(m1_head)
                m2hlen = len(m2_head)
                if m1hlen < m2hlen:
                    return -1
                if m1hlen > m2hlen:
                    return 1
            if m1_head < m2_head:
                return -1
            if m1_head > m2_head:
                return 1
            continue

        m1len = len(first)
        m2len = len(second)
        if m1len == m2len == 0:
            return 0
        if m1len != 0:
            return 1
        return -1

    # 取系统版本
    def get_sys_version(self):
        '''
        获取当前系统版本
        :return: string
        '''
        sys_version = "None"
        if os.path.exists("/etc/redhat-release"):
            result = public.ReadFile("/etc/redhat-release")
            if "CentOS Linux release 7" in result:
                sys_version = "centos_7"
            elif "CentOS Linux release 8" in result or "CentOS Stream release 8" in result:
                sys_version = "centos_8"
        elif os.path.exists("/etc/debian_version"):
            result = public.ReadFile("/etc/debian_version")
            if "10." in result:
                sys_version = "debian_10"
            elif "11." in result:
                sys_version = "debian_11"
        elif os.path.exists("/etc/issue"):
            if "Ubuntu 20.04" in public.ReadFile("/etc/issue"):
                sys_version = "ubuntu_20.04"
            elif "Ubuntu 22.04" in public.ReadFile("/etc/issue"):
                sys_version = "ubuntu_22.04"
            elif "Ubuntu 18.04" in public.ReadFile("/etc/issue"):
                sys_version = "ubuntu_18.04"
        return sys_version

    # 取软件包版本
    def get_sys_product(self):
        """
        :return dict 如果系统不支持则返回str None
        """
        product_version = {}
        sys_version = self.get_sys_version()
        # if sys_version == 'None':return public.returnMsg(False,'当前系统暂不支持')
        if "centos" in sys_version:
            result = public.ExecShell('rpm -qa --qf \'%{NAME};%{VERSION}-%{RELEASE}\\n\'')[0].strip().split('\n')
        elif "ubuntu" in sys_version:
            # result1 = subprocess.check_output(['dpkg-query', '-W', '-f=${Package};${Version}\n']).decode('utf-8').strip().split('\n')
            result = public.ExecShell('dpkg-query -W -f=\'${Package};${Version}\n\'')[0].strip().split('\n')
        elif "debian" in sys_version:
            result = public.ExecShell('dpkg-query -W -f=\'${Package};${Version}\n\'')[0].strip().split('\n')
        elif sys_version == "None":
            return None
        else:
            return None
        for pkg in result:
            try:
                product_version[pkg.split(";")[0]] = pkg.split(";")[1]
            except:
                return None
        # product_version["kernel"] = subprocess.check_output(['uname', '-r']).decode('utf-8').strip().replace(".x86_64", "")
        product_version["kernel"] = public.ExecShell('uname -r')[0].strip()
        return product_version

    def get_vuln_result(self):
        '''
        获取上一次扫描结果
        :param get:
        :return: dict
        '''
        d_risk = 0
        h_risk = 0
        m_risk = 0
        vul_list = []
        if not os.path.exists(self.__vul_list):
            self.vul_num = 0
        else:
            self.vul_num = len(self.get_vul_list())
        if not os.path.exists(self._vuln_result):
            tmp_dict = {"vul_count": self.vul_num, "risk": [], "ignore": [],
                        "count": {"serious": 0, "high_risk": 0, "moderate_risk": 0}, "msg": "",
                        "repair_count": {"all_count": 0, "today_count": 0}, "all_check_time": "", "ignore_count": 0}
            if os.path.exists("/etc/redhat-release"):
                result = public.ReadFile("/etc/redhat-release")
                if "CentOS Linux release 8" in result:
                    tmp_dict[
                        "msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
            return tmp_dict
        if public.ReadFile(self._vuln_result) == '[]':
            tmp_dict = {"vul_count": self.vul_num, "risk": [], "ignore": [],
                        "count": {"serious": 0, "high_risk": 0, "moderate_risk": 0}, "msg": "",
                        "repair_count": {"all_count": 0, "today_count": 0}, "all_check_time": "", "ignore_count": 0}
            if os.path.exists("/etc/redhat-release"):
                result = public.ReadFile("/etc/redhat-release")
                if "CentOS Linux release 8" in result:
                    tmp_dict[
                        "msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
            return tmp_dict
        result_dict = json.loads(public.ReadFile(self._vuln_result))
        old_risk_list = result_dict["risk"]
        old_ignore_list = result_dict["ignore"]
        new_risk_list = old_risk_list.copy()
        new_ignore_list = old_ignore_list.copy()
        tmp_ignore_list = self.get_ignore_list()
        for cve in old_risk_list:
            if cve["cve_id"] in tmp_ignore_list:
                new_ignore_list.append(cve)
                new_risk_list.remove(cve)
        for cve_ig in old_ignore_list:
            if cve_ig["cve_id"] not in tmp_ignore_list:
                new_risk_list.append(cve_ig)
                new_ignore_list.remove(cve_ig)
        for vul in new_ignore_list + new_risk_list:
            vul_list.append(vul["cve_id"])
            if vul["cve_id"] in tmp_ignore_list:
                continue
            if vul["level"] == 3:
                d_risk += 1
            elif vul["level"] == 2:
                h_risk += 1
            elif vul["level"] == 1:
                m_risk += 1
        list_sort = [3, 2, 1]  # 排序列表
        # result_dict["risk"] = old_risk_list
        result_dict["risk"] = sorted(new_risk_list, key=lambda x: list_sort.index(x.get("level")))
        # result_dict["ignore"] = old_ignore_list
        result_dict["ignore"] = sorted(new_ignore_list, key=lambda x: list_sort.index(x.get("level")))
        # result_dict["reboot"] = self.__need_reboot
        result_dict["count"] = {"serious": d_risk, "high_risk": h_risk, "moderate_risk": m_risk}
        result_dict["msg"] = ""
        result_dict["repair_count"] = self.count_repair(vul_list)
        result_dict["all_check_time"] = public.ReadFile(self.__path + '/system_scan_time')
        result_dict["ignore_count"] = len(tmp_ignore_list)
        if os.path.exists("/etc/redhat-release"):
            result = public.ReadFile("/etc/redhat-release")
            if "CentOS Linux release 8" in result:
                result_dict[
                    "msg"] = "当前系统【centos_8】官方已停止维护，为了安全起见，建议升级至centos 8 stream\n详情参考教程：https://www.bt.cn/bbs/thread-82931-1-1.html"
        public.WriteFile(self._vuln_result, json.dumps(result_dict))
        return result_dict

    # 按分数评等级
    def get_score_risk(self, score):
        '''
        拿到分数，返回危险等级
        :param score:
        :return: int 若没有符合的分数就报错，需要捕获异常
        '''
        if float(score) >= 9.0:
            risk = 3
        elif float(score) >= 7.0:
            risk = 2
        elif float(score) >= 6.0:
            risk = 1
        return risk

    def get_vul_list(self):
        return json.loads(public.ReadFile(self.__vul_list))

    def get_ignore_list(self):
        return json.loads(public.ReadFile(self._vuln_ignore))

    def set_vuln_ignore(self, args):
        '''
        设置忽略指定cve，若已在列表里，则删除，不在列表里则添加
        :param args:
        :return: dict {status:true,msg:'设置成功/失败'}
        '''
        cve_list = json.loads(args.cve_list.strip())
        ignore_list = self.get_ignore_list()
        for cl in cve_list:
            if cl in ignore_list:
                ignore_list.remove(cl)
            else:
                ignore_list.append(cl)

        public.WriteFile(self._vuln_ignore, json.dumps(ignore_list))
        # public.WriteFile(self.__result, json.dumps(result_dict))
        return public.returnMsg(True, '设置成功!')
        # except:
        #     return public.returnMsg(False, '{}设置失败!'.format(cve_list))

    def count_repair(self, now_list):
        '''
        获取总共修复漏洞的数量以及今日修复漏洞数量
        :param now_list:
        :return: dict
        '''
        cve_dict = {}
        if not os.path.exists(self.__repair_count):
            cve_dict["all_cve"] = now_list
            cve_dict["today_cve"] = now_list
            cve_dict["time"] = int(time.time())
            public.WriteFile(self.__repair_count, json.dumps(cve_dict))
        cve_dict = json.loads(public.ReadFile(self.__repair_count))
        cve_dict["all_cve"].extend(set(now_list) - set(cve_dict["all_cve"]))
        all_count = len(cve_dict["all_cve"]) - len(now_list)
        cve_dict["today_cve"].extend(set(now_list) - set(cve_dict["today_cve"]))
        today_count = len(cve_dict["today_cve"]) - len(now_list)
        # if cve_dict["time"].split(" ")[0] != self.get_time().split(" ")[0]:
        #     cve_dict["today_cve"] = now_list
        cve_dict["time"] = int(time.time())
        public.WriteFile(self.__repair_count, json.dumps(cve_dict))
        return {"all_count": all_count, "today_count": today_count}

    def get_time(self):
        return public.format_date()

    def check_cve(self, args):
        '''
        检测单个漏洞
        :param args:
        :return: dict
        '''
        sys_product = self.get_sys_product()
        if not sys_product:
            return public.returnMsg(True, '检测失败')
        cve_id = args.cve_id.strip()
        result_dict = json.loads(public.ReadFile(self._vuln_result))
        risk_list = result_dict["risk"]
        ignore_list = result_dict["ignore"]
        tmptmp = 1
        for cve in risk_list:
            if cve["cve_id"] == cve_id:
                tmp = 1  # 默认命中漏洞
                cve["check_time"] = int(time.time())
                for soft in list(cve["soft_name"].keys()):
                    if self.version_compare(sys_product[soft], cve["vuln_version"]) >= 0:
                        tmp = 0  # 当有一个软件包不命中，则为已修复
                        tmptmp = 0
                        break
                if tmp == 0:
                    risk_list.remove(cve)
        for cve in ignore_list:
            if cve["cve_id"] == cve_id:
                tmp = 1  # 默认命中漏洞
                cve["check_time"] = int(time.time())
                for soft in list(cve["soft_name"].keys()):
                    if self.version_compare(sys_product[soft], cve["vuln_version"]) >= 0:
                        tmp = 0  # 当有一个软件包不命中，则为已修复
                        tmptmp = 0
                        break
                if tmp == 0:
                    ignore_list.remove(cve)
        result_dict["risk"] = risk_list
        result_dict["ignore"] = ignore_list
        public.WriteFile(self._vuln_result, json.dumps(result_dict))
        if tmptmp == 0:
            return public.returnMsg(True, '已重新检测')
        else:
            return public.returnMsg(True, '已重新检测')

    def compare_md5(self):
        '''
        对比md5，更新漏洞库
        :return:
        '''
        import requests
        # try:
        #    new_md5 = requests.get("https://www.bt.cn/vulscan_d11ad1fe99a5f078548b0ea355db42dc.txt").text
        # except:
        #    return 0
        # old_md5 = public.FileMd5(self.__vul_list)
        # if old_md5 != new_md5 or not os.path.exists(self.__vul_list):
        if not os.path.exists(self.__vul_list):
            try:
                public.downloadFile("https://download.bt.cn/install/src/high_risk_vul.zip",
                                    self.__path + "/high_risk_vul.zip")
                public.ExecShell("unzip -o {}/high_risk_vul.zip -d {}/".format(self.__path, self.__path))
            except:
                return 0
        return 1

    def get_logs(self, get):
        '''
        获取升级日志
        :param get:
        :return: dict
        '''
        import files
        return public.returnMsg(True, files.files().GetLastLine(self.__path + '/log.txt', 20))

    def record_times(self):
        '''
        记录近七日扫描次数
        '''
        date_obj = datetime.datetime.now()
        weekday = datetime.datetime.now().weekday()
        if not os.path.exists("/www/server/panel/data/warning_report/record.json"):
            tmp = {"scan": [], "repair": []}
            for i in range(6, -1, -1):
                last_date = (date_obj - datetime.timedelta(days=i)).strftime("%Y/%m/%d")
                tmp["scan"].append({"date": last_date, "times": 0})
                tmp["repair"].append({"date": last_date, "times": 0})
            public.WriteFile("/www/server/panel/data/warning_report/record.json", json.dumps(tmp))
        with open("/www/server/panel/data/warning_report/record.json", "r") as f:
            record = json.load(f)
        if record["scan"][weekday]["date"] == datetime.datetime.now().strftime("%Y/%m/%d"):
            record["scan"][weekday]["times"] += 1
        else:
            record["scan"][weekday]["date"] = datetime.datetime.now().strftime("%Y/%m/%d")
            record["scan"][weekday]["times"] = 1
        public.WriteFile("/www/server/panel/data/warning_report/record.json", json.dumps(record))

    def get_scan_bar(self, get):
        '''
        获取扫描进度条
        @param get:
        @return: int
        '''
        if not os.path.exists(self.__path + '/bar.txt'):return 0
        data3 = public.ReadFile(self.__path + '/bar.txt')
        if isinstance(data3, str):
            data3 = data3.strip()
            try:
                data = int(float(data3))
            except:
                data = 0
            return data
        return 0
