#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 简单的RQAlpha测试脚本
from rqalpha.apis import *
from rqalpha import run_func

def init(context):
    context.s1 = "000001.XSHE"
    logger.info("策略初始化完成")

def before_trading(context):
    pass

def handle_bar(context, bar_dict):
    # 简单的买入持有策略
    order_percent(context.s1, 1)

def after_trading(context):
    pass

__config__ = {
    "base": {
        "start_date": "2022-01-01",
        "end_date": "2022-01-31",
        "data_bundle_path": "C:\\Users\\zhaomh\\.rqalpha\\bundle",
        "strategy_file": "test_rqalpha.py",
        "frequency": "1d",
        "matching_type": "current_bar",
        "run_type": "b",
        "accounts": {
            "stock": 100000,
        },
    },
    "extra": {
        "log_level": "info",
    },
    "mod": {
        "sys_analyser": {
            "enabled": True,
            "benchmark": "000300.XSHG",
        },
    },
}

if __name__ == "__main__":
    run_func(**globals())