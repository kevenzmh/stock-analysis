#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
股票选股策略文件

这是一个简单但完整的策略示例，用于首次运行测试
策略逻辑：均线多头排列 + 成交量放大

作者：基于模板创建
"""

import numpy as np
import pandas as pd
import talib
from func_TDX import MA, SMA, CROSS, REF


def 策略HS300(df_hs300, start_date='', end_date=''):
    """
    沪深300指数信号
    用于判断大盘环境，决定是否买入
    
    策略：简单的MA5 > MA20判断
    """
    if start_date == '':
        start_date = df_hs300.index[0]
    if end_date == '':
        end_date = df_hs300.index[-1]
    
    df_hs300 = df_hs300.loc[start_date:end_date]
    
    C = df_hs300['close']
    MA5 = SMA(C, 5)
    MA20 = SMA(C, 20)
    
    # 简单策略：短期均线在长期均线上方
    信号 = MA5 > MA20
    
    return 信号


def 策略1(df, start_date='', end_date='', mode=None):
    """
    策略1：初步筛选
    
    筛选条件：
    1. 股价 > 5元（排除低价股）
    2. 成交额 > 5000万（排除成交清淡股票）
    3. 流通市值 < 500亿（排除大盘股）
    4. 非涨停板
    
    参数:
        df: 股票数据DataFrame
        start_date: 开始日期
        end_date: 结束日期
        mode: 'fast' 为快速模式，仅判断最后一天
    
    返回:
        布尔值或布尔序列
    """
    if start_date == '':
        start_date = df.index[0]
    if end_date == '':
        end_date = df.index[-1]
    
    df = df.loc[start_date:end_date]
    
    # 获取数据
    O = df['open']
    H = df['high']
    L = df['low']
    C = df['close']
    V = df['vol']
    A = df['amount']
    
    # 判断是否有流通市值列
    if '流通市值' in df.columns:
        流通市值 = df['流通市值']
    else:
        流通市值 = pd.Series([0] * len(df), index=df.index)
    
    if mode == 'fast':
        # 快速模式：只判断最后一天
        if len(df) < 20:
            return False
        
        # 基本条件
        条件1 = C.iloc[-1] > 5  # 股价大于5元
        条件2 = A.iloc[-1] > 50000000  # 成交额大于5000万
        条件3 = 流通市值.iloc[-1] < 50000000000 if 流通市值.iloc[-1] > 0 else True  # 流通市值小于500亿
        
        # 排除涨停板
        昨收 = C.iloc[-2]
        今收 = C.iloc[-1]
        
        # 判断是否科创板或创业板（20%涨跌幅）
        code = df['code'].iloc[0] if 'code' in df.columns else ''
        if code.startswith('688') or code.startswith('300'):
            涨停价 = 昨收 * 1.2
        else:
            涨停价 = 昨收 * 1.1
        
        条件4 = 今收 < (涨停价 - 0.01)  # 不是涨停板
        
        return 条件1 and 条件2 and 条件3 and 条件4
    
    else:
        # 完整模式：返回序列
        条件1 = C > 5
        条件2 = A > 50000000
        条件3 = (流通市值 < 50000000000) | (流通市值 == 0)
        
        # 排除涨停板
        昨收 = REF(C, 1)
        code = df['code'].iloc[0] if 'code' in df.columns else ''
        if code.startswith('688') or code.startswith('300'):
            涨停价 = 昨收 * 1.2
        else:
            涨停价 = 昨收 * 1.1
        
        条件4 = C < (涨停价 - 0.01)
        
        return 条件1 & 条件2 & 条件3 & 条件4


def 策略2(df, HS300_信号, start_date='', end_date=''):
    """
    策略2：精选买入信号
    
    策略逻辑：均线多头排列 + 成交量突破
    1. MA5 > MA10 > MA20 > MA60（均线多头）
    2. 今日成交量 > 5日平均成交量 * 1.5（放量）
    3. 股价在MA60上方且涨幅不超过3%（位置合理）
    4. 结合沪深300信号
    
    参数:
        df: 股票数据DataFrame
        HS300_信号: 沪深300信号序列
        start_date: 开始日期
        end_date: 结束日期
    
    返回:
        布尔序列
    """
    if start_date == '':
        start_date = df.index[0]
    if end_date == '':
        end_date = df.index[-1]
    
    df = df.loc[start_date:end_date]
    
    # 数据不足，返回全False序列
    if len(df) < 60:
        return pd.Series([False] * len(df), index=df.index)
    
    # 重建HS300信号，匹配股票交易日
    HS300_信号 = pd.Series(HS300_信号, index=df.index, dtype=bool).fillna(False)
    
    # 获取数据
    C = df['close']
    V = df['vol']
    
    # 计算均线
    MA5 = SMA(C, 5)
    MA10 = SMA(C, 10)
    MA20 = SMA(C, 20)
    MA60 = SMA(C, 60)
    
    # 计算成交量均线
    VOL_MA5 = SMA(V, 5)
    
    # 策略条件
    # 条件1：均线多头排列
    条件1 = (MA5 > MA10) & (MA10 > MA20) & (MA20 > MA60)
    
    # 条件2：成交量放大
    条件2 = V > VOL_MA5 * 1.5
    
    # 条件3：股价在MA60上方，但涨幅不大
    条件3 = (C > MA60) & (C < MA60 * 1.03)
    
    # 条件4：价格向上突破MA5
    条件4 = CROSS(C, MA5)
    
    # 条件5：必须通过策略1筛选
    条件5 = 策略1(df, start_date, end_date, mode='')
    
    # 综合信号
    买入信号 = HS300_信号 & 条件1 & 条件2 & 条件3 & 条件4 & 条件5
    
    return 买入信号


def 卖策略(df, 策略2, start_date='', end_date=''):
    """
    卖出策略
    
    卖出条件：
    1. 跌破MA10
    2. 或盈利超过10%
    3. 或亏损超过5%
    
    参数:
        df: 股票数据DataFrame
        策略2: 买入信号序列
        start_date: 开始日期
        end_date: 结束日期
    
    返回:
        卖出信号序列
    """
    # 如果没有买入信号，返回全False
    if True not in 策略2.to_list():
        return pd.Series([False] * len(策略2), index=策略2.index)
    
    if start_date == '':
        start_date = df.index[0]
    if end_date == '':
        end_date = df.index[-1]
    
    df = df.loc[start_date:end_date]
    
    C = df['close']
    MA10 = SMA(C, 10)
    
    # 计算买入价格
    买入价格 = pd.Series(index=C.index, dtype=float)
    盈亏比例 = pd.Series(index=C.index, dtype=float)
    
    # 找到所有买入点
    买入日期列表 = 策略2[策略2 == True].index.to_list()
    
    for 买入日期 in 买入日期列表[::-1]:  # 倒序处理
        买入价格.loc[买入日期] = C.loc[买入日期]
        买入价格.fillna(method='ffill', inplace=True)
        
        # 计算盈亏比例
        盈亏比例 = C / 买入价格 - 1
        
    # 卖出条件
    卖出条件1 = C < MA10  # 跌破MA10
    卖出条件2 = 盈亏比例 > 0.10  # 盈利超过10%
    卖出条件3 = 盈亏比例 < -0.05  # 亏损超过5%
    
    # 生成卖出信号
    卖出信号 = pd.Series([False] * len(df), index=df.index)
    
    for 买入日期 in 买入日期列表[::-1]:
        # 在买入日期之后查找第一个卖出点
        后续数据 = (卖出条件1 | 卖出条件2 | 卖出条件3).loc[买入日期:]
        
        for k, v in 后续数据.items():
            if k != 买入日期 and v:  # 排除买入当天
                卖出信号[k] = True
                break
    
    return 卖出信号


# 测试代码
if __name__ == '__main__':
    """
    策略测试代码
    用于验证策略是否能正常运行
    """
    import os
    import time
    import user_config as ucfg
    import func
    
    print("="*60)
    print("策略测试")
    print("="*60)
    
    # 测试股票代码
    test_codes = ['000001', '600036', '000002']
    
    # 加载沪深300指数
    print("\n1. 加载沪深300指数...")
    try:
        df_hs300 = pd.read_csv(
            ucfg.tdx['csv_index'] + '/000300.csv',
            index_col=None,
            encoding='gbk',
            dtype={'code': str}
        )
        df_hs300['date'] = pd.to_datetime(df_hs300['date'], format='%Y-%m-%d')
        df_hs300.set_index('date', drop=False, inplace=True)
        
        HS300_信号 = 策略HS300(df_hs300)
        print(f"   ✓ 沪深300信号生成成功")
        print(f"   当前信号: {HS300_信号.iloc[-1]}")
    except Exception as e:
        print(f"   ✗ 沪深300数据加载失败: {e}")
        print("   提示: 请先运行 readTDX_lday.py 生成指数数据")
        exit(1)
    
    # 测试股票策略
    print("\n2. 测试股票策略...")
    for code in test_codes:
        try:
            csv_file = ucfg.tdx['csv_lday'] + os.sep + code + '.csv'
            
            if not os.path.exists(csv_file):
                print(f"   ⚠ {code}: 数据文件不存在")
                continue
            
            df_stock = pd.read_csv(csv_file, index_col=None, encoding='gbk', dtype={'code': str})
            df_stock['date'] = pd.to_datetime(df_stock['date'], format='%Y-%m-%d')
            df_stock.set_index('date', drop=False, inplace=True)
            
            # 测试策略1
            result1_fast = 策略1(df_stock, mode='fast')
            result1_full = 策略1(df_stock, mode='')
            
            # 测试策略2
            result2 = 策略2(df_stock, HS300_信号)
            
            # 测试卖策略
            result_sell = 卖策略(df_stock, result2)
            
            print(f"   ✓ {code}: 策略1(fast)={result1_fast}, 策略2最新={result2.iloc[-1]}")
            
        except Exception as e:
            print(f"   ✗ {code}: 测试失败 - {e}")
    
    print("\n" + "="*60)
    print("策略测试完成")
    print("="*60)
    print("\n如果以上测试通过，说明策略文件可以正常使用！")
    print("现在可以运行: python xuangu.py")
