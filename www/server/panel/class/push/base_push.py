#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | Author: baozi
# +-------------------------------------------------------------------
from typing import List, Dict, Tuple

import public,panelPush

try:
    from BTPanel import cache
except :
    from cachelib import SimpleCache
    cache = SimpleCache()

class metaclass(type):
    def __new__(cls, name, *args, **kwargs):
        push_cls = super().__new__(cls, name, *args, **kwargs)
        if name == "base_push":
            return push_cls
        else:
            push_cls.all_push_model.append(push_cls)
        return push_cls

class base_push(metaclass=metaclass):
    all_push_model = []

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        raise NotImplementedError

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        raise NotImplementedError

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        raise NotImplementedError

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        raise NotImplementedError

    #返回这个告警类型可以设置的任务模板，返回形式为列表套用字典
    def get_task_template(self) -> Tuple[str, List[Dict]]:
        # 返回这个告警类型可以设置的任务模板，返回形式为列表套用字典
        raise NotImplementedError

    # 返回到前端信息的钩子, 默认为返回传入信息（即：当前设置的任务的信息）
    def get_view_msg(self, task_id: str, task_data: dict) -> dict:
        return task_data