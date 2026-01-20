#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
改进版策略 - 在原策略基础上增强筛选
"""

import numpy as np
import pandas as pd
import talib
from func_TDX import MA, SMA, CROSS, REF, HHV, LLV

# 导入原策略
from CeLue import 策略HS300, 策略1 as 原策略1, 策略2 as 原策略2


def 策略1_增强版(df, start_date='', end_date='', mode=None):
    """
    增强版策略1：在原基础上增加更严格的筛选
    
    新增条件：
    1. 近20日平均成交额 > 1亿（更高的流动性）
    2. 价格在年线（MA250）之上（长期趋势向上）
    3. 近期换手率在合理区间（避免妖股）
    """
    # 先通过原策略1
    基础筛选 = 原策略1(df, start_date, end_date, mode)
    
    if mode == 'fast':
        if not 基础筛选:
            return False
        
        if len(df) < 250:
            return False
        
        # 新增条件
        A = df['amount']
        C = df['close']
        V = df['vol']
        
        # 近20日平均成交额 > 1亿
        近20日平均成交额 = A.iloc[-20:].mean()
        条件1 = 近20日平均成交额 > 100000000
        
        # 价格在年线之上
        MA250 = SMA(C, 250)
        条件2 = C.iloc[-1] > MA250.iloc[-1] if not pd.isna(MA250.iloc[-1]) else True
        
        # 换手率检查（避免过度投机）
        # 换手率 = 成交量 / 流通股本 * 100
        # 这里简化：用成交量/成交额比率来估算
        换手率估算 = (V.iloc[-1] / (A.iloc[-1] / C.iloc[-1])) * 100 if A.iloc[-1] > 0 else 0
        条件3 = 1 < 换手率估算 < 20  # 换手率在1%-20%之间
        
        return 条件1 and 条件2 and 条件3
    
    else:
        # 完整模式
        return 基础筛选  # 可以在这里扩展为序列模式


def 策略2_精选版(df, HS300_信号, start_date='', end_date='', top_n=30):
    """
    在策略2基础上进行精选
    返回: (买入信号, 得分)
    - 买入信号: True/False
    - 得分: 0-100分的综合评分
    """
    # 获取原策略2结果
    买入信号 = 原策略2(df, HS300_信号, start_date, end_date)
    
    # 如果没有买入信号，直接返回
    if not 买入信号.iloc[-1]:
        return False, 0
    
    # 计算信号强度得分（0-100分）
    C = df['close']
    V = df['vol']
    H = df['high']
    L = df['low']
    
    得分 = 0
    
    # 1. 均线排列紧密度（20分）
    MA5 = SMA(C, 5)
    MA10 = SMA(C, 10)
    MA20 = SMA(C, 20)
    MA60 = SMA(C, 60)
    
    均线紧密度 = ((MA5.iloc[-1] - MA60.iloc[-1]) / MA60.iloc[-1]) * 100
    if 均线紧密度 < 15:  # 均线越紧密，突破后动能越强
        得分 += 20 - 均线紧密度
    
    # 2. 成交量放大程度（20分）
    VOL_MA5 = SMA(V, 5)
    量比 = V.iloc[-1] / VOL_MA5.iloc[-1] if VOL_MA5.iloc[-1] > 0 else 1
    得分 += min(20, 量比 * 10)  # 量比越大得分越高
    
    # 3. MACD强度（20分）
    macd, signal, hist = talib.MACD(C.values, fastperiod=12, slowperiod=26, signalperiod=9)
    MACD_HIST = hist[-1]
    得分 += min(20, abs(MACD_HIST) * 100)
    
    # 4. RSI动能（20分）
    rsi = talib.RSI(C.values, timeperiod=14)
    RSI = rsi[-1]
    # RSI在50-70之间最佳
    if 50 <= RSI <= 70:
        得分 += 20
    elif 40 <= RSI < 50:
        得分 += 15
    elif 70 < RSI <= 80:
        得分 += 10
    
    # 5. 价格位置（20分）
    价格位置 = (C.iloc[-1] - L.iloc[-20:].min()) / (H.iloc[-20:].max() - L.iloc[-20:].min())
    if 0.4 <= 价格位置 <= 0.7:  # 在20日区间的中上部最佳
        得分 += 20
    elif 0.2 <= 价格位置 < 0.4:
        得分 += 15
    
    return True, min(100, 得分)


# 辅助函数：选出得分最高的N只股票
def 精选股票(股票得分字典, top_n=30):
    """
    从股票得分字典中选出得分最高的N只
    
    参数：
        股票得分字典: {股票代码: 得分}
        top_n: 选出前N只
    
    返回：
        排序后的股票列表
    """
    sorted_stocks = sorted(股票得分字典.items(), key=lambda x: x[1], reverse=True)
    return [code for code, score in sorted_stocks[:top_n]]


if __name__ == '__main__':
    print("=" * 70)
    print("改进版策略说明")
    print("=" * 70)
    print("\n策略1增强：")
    print("  - 提高成交额门槛到1亿（更高流动性）")
    print("  - 要求价格在年线之上（长期趋势）")
    print("  - 限制换手率（避免过度投机）")
    print("\n策略2精选：")
    print("  - 为每只股票评分（0-100分）")
    print("  - 综合考虑：均线紧密度、量比、MACD、RSI、价格位置")
    print("  - 最终只选出得分最高的30只股票")
    print("\n" + "=" * 70)
