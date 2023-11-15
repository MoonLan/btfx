#coding: utf-8
import sys,os
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import PluginLoader
import public
import time


def clear_hosts():
    """
    @name 清理hosts文件中的bt.cn记录
    @return:
    """
    remove = 0
    try:
        import requests
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        url = 'https://www.bt.cn/api/ip/info_json'
        res = requests.post(url, verify=False)

        if res.status_code == 404:
            remove = 1
        elif res.status_code == 200 or res.status_code == 400:
            res = res.json()
            if res != "[]":
                remove = 1
    except:
        result = public.ExecShell("curl -sS --connect-timeout 3 -m 60 -k https://www.bt.cn/api/ip/info_json")[0]
        if result != "[]":
            remove = 1

    hosts_file = '/etc/hosts'
    if remove == 1 and os.path.exists(hosts_file):
        public.ExecShell('sed -i "/www.bt.cn/d" /etc/hosts')

def flush_cache():
    '''
        @name 更新缓存
        @author hwliang
        @return void
    '''
    try:
        start_time = time.time()
        res = PluginLoader.get_plugin_list(1)
        spath = '{}/data/pay_type.json'.format(public.get_panel_path())
        public.downloadFile(public.get_url() + '/install/lib/pay_type.json',spath)
        import plugin_deployment
        plugin_deployment.plugin_deployment().GetCloudList(None)

        timeout = time.time() - start_time
        if 'ip' in res and res['ip']:
            public.print_log("缓存更新成功,耗时: %.2f 秒" % timeout)
        else:
            if isinstance(res,dict) and not 'msg' in res: res['msg'] = '连接服务器失败!'
            public.print_log("缓存更新失败: {}".format(res['msg']))
    except:
        public.print_log("缓存更新失败: {}".format(public.get_error_info()))



def flush_msg_json():
    """
    @name 更新消息json
    """
    try:
        public.print_log("开始更新消息json...")
        spath = '{}/data/msg.json'.format(public.get_panel_path())
        public.downloadFile(public.get_url() + '/linux/panel/msg/msg.json',spath)
        public.print_log("更新消息json成功")
    except:
        public.print_log("更新消息json失败: {}".format(public.get_error_info()))

if __name__ == '__main__':
    tip_date_tie = '/tmp/.fluah_time'
    if os.path.exists(tip_date_tie):
        last_time = int(public.readFile(tip_date_tie))
        timeout = time.time() - last_time
        if timeout < 3600:
            print("执行间隔过短，退出 - {}!".format(timeout))
            sys.exit()
    clear_hosts()
    flush_cache()
    flush_msg_json()
    public.writeFile(tip_date_tie,str(int(time.time())))
