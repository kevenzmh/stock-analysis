#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
高级股票量化策略 - 趋势追踪+突破组合策略

核心策略：
1. 趋势追踪策略 - MACD金叉+均线多头
2. 突破策略 - 箱体突破+放量确认
3. 动态止盈止损 - 保护利润，控制风险

策略特点：
- 顺势而为：只做上升趋势的股票
- 严格止损：最大亏损控制在8%以内
- 分批止盈：达到15%获利了结
- 大盘过滤：只在大盘向好时买入

作者：AI优化策略
更新日期：2026-01-13
"""

import numpy as np
import pandas as pd
import talib
from func_TDX import MA, SMA, CROSS, REF, HHV, LLV


# ==================== 大盘策略 ====================

def 策略HS300(df_hs300, start_date='', end_date=''):
    """
    沪深300指数策略 - 判断大盘环境
    
    策略逻辑：
    1. MA5 > MA20 > MA60 （均线多头排列）
    2. MACD DIFF > 0 （在0轴上方）
    3. 成交量稳定放大
    
    返回：True=大盘向好，可以买入；False=大盘不好，不买入
    """
    if start_date == '':
        start_date = df_hs300.index[0]
    if end_date == '':
        end_date = df_hs300.index[-1]
    
    df_hs300 = df_hs300.loc[start_date:end_date]
    
    C = df_hs300['close']
    V = df_hs300['vol']
    
    # 均线系统
    MA5 = SMA(C, 5)
    MA20 = SMA(C, 20)
    MA60 = SMA(C, 60)
    
    # MACD指标
    macd, signal, hist = talib.MACD(C.values, fastperiod=12, slowperiod=26, signalperiod=9)
    MACD_DIFF = pd.Series(macd, index=df_hs300.index)
    
    # 成交量均线
    VOL_MA5 = SMA(V, 5)
    
    # 大盘向好的条件
    条件1 = (MA5 > MA20) & (MA20 > MA60)  # 均线多头
    条件2 = MACD_DIFF > 0  # MACD在0轴上方
    条件3 = V > VOL_MA5 * 0.8  # 成交量不能太萎缩
    
    信号 = 条件1 & 条件2 & 条件3
    
    return 信号


# ==================== 初筛策略 ====================

def 策略1(df, start_date='', end_date='', mode=None):
    """
    策略1：基础筛选条件
    
    筛选目的：
    1. 排除垃圾股、仙股
    2. 排除成交清淡股票
    3. 排除过大的股票（灵活性差）
    
    筛选条件：
    - 股价 > 3元（排除低价股风险）
    - 成交额 > 3000万（有足够流动性）
    - 股价 < 300元（排除过高价股）
    - 非涨停板（避免追涨停）
    """
    if start_date == '':
        start_date = df.index[0]
    if end_date == '':
        end_date = df.index[-1]
    
    df = df.loc[start_date:end_date]
    
    O = df['open']
    H = df['high']
    L = df['low']
    C = df['close']
    V = df['vol']
    A = df['amount']
    
    if mode == 'fast':
        # 快速模式：只判断最后一天
        if len(df) < 20:
            return False
        
        # 基本条件
        条件1 = C.iloc[-1] > 3  # 股价大于3元
        条件2 = A.iloc[-1] > 30000000  # 成交额大于3000万
        条件3 = C.iloc[-1] < 300  # 股价小于300元
        
        # 排除涨停板
        昨收 = C.iloc[-2]
        今收 = C.iloc[-1]
        
        # 判断是否科创板或创业板（20%涨跌幅）
        code = df['code'].iloc[0] if 'code' in df.columns else ''
        if code.startswith('688') or code.startswith('300'):
            涨停价 = 昨收 * 1.195  # 留一点余地
        else:
            涨停价 = 昨收 * 1.095
        
        条件4 = 今收 < 涨停价  # 不是涨停板
        
        return 条件1 and 条件2 and 条件3 and 条件4
    
    else:
        # 完整模式：返回序列
        条件1 = C > 3
        条件2 = A > 30000000
        条件3 = C < 300
        
        # 排除涨停板
        昨收 = REF(C, 1)
        code = df['code'].iloc[0] if 'code' in df.columns else ''
        if code.startswith('688') or code.startswith('300'):
            涨停价 = 昨收 * 1.195
        else:
            涨停价 = 昨收 * 1.095
        
        条件4 = C < 涨停价
        
        return 条件1 & 条件2 & 条件3 & 条件4


# ==================== 核心买入策略 ====================

def 策略2(df, HS300_信号, start_date='', end_date=''):
    """
    策略2：核心买入策略（趋势追踪+突破组合）
    
    买入逻辑：
    1. 大盘环境向好（HS300策略为True）
    2. 均线多头排列（MA5>MA10>MA20>MA60）
    3. MACD金叉且在0轴附近或上方
    4. 价格突破MA20或箱体高点
    5. 成交量放大确认（>5日均量1.3倍）
    6. 位置合理（不追高）
    
    适用场景：
    - 牛市和震荡市上升阶段
    - 中短期持仓（1-6周）
    - 预期收益：10-30%
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
    H = df['high']
    L = df['low']
    V = df['vol']
    
    # ========== 均线系统 ==========
    MA5 = SMA(C, 5)
    MA10 = SMA(C, 10)
    MA20 = SMA(C, 20)
    MA60 = SMA(C, 60)
    
    # ========== MACD指标 ==========
    macd, signal, hist = talib.MACD(C.values, fastperiod=12, slowperiod=26, signalperiod=9)
    MACD_DIFF = pd.Series(macd, index=df.index)
    MACD_DEA = pd.Series(signal, index=df.index)
    MACD_HIST = pd.Series(hist, index=df.index)
    
    # ========== 成交量指标 ==========
    VOL_MA5 = SMA(V, 5)
    VOL_MA20 = SMA(V, 20)
    
    # ========== RSI指标 ==========
    rsi = talib.RSI(C.values, timeperiod=14)
    RSI = pd.Series(rsi, index=df.index)
    
    # ========== 箱体计算 ==========
    HH20 = HHV(H, 20)  # 20日最高价
    LL20 = LLV(L, 20)  # 20日最低价
    
    # ========== 策略条件 ==========
    
    # 条件1：大盘环境良好
    条件1 = HS300_信号
    
    # 条件2：均线多头排列
    条件2 = (MA5 > MA10) & (MA10 > MA20) & (MA20 > MA60)
    
    # 条件3：MACD金叉或在0轴上方
    MACD金叉 = CROSS(MACD_DIFF, MACD_DEA)
    MACD强势 = (MACD_DIFF > -0.1) & (MACD_DIFF > REF(MACD_DIFF, 1))  # DIFF>-0.1且向上
    条件3 = MACD金叉 | MACD强势
    
    # 条件4：价格突破（两种方式）
    突破MA20 = CROSS(C, MA20) | ((C > MA20) & (REF(C, 1) <= REF(MA20, 1)))
    突破箱体 = C > REF(HH20, 1)
    条件4 = 突破MA20 | 突破箱体
    
    # 条件5：成交量放大确认
    条件5 = V > VOL_MA5 * 1.3
    
    # 条件6：不在超买区（RSI<80）
    条件6 = (RSI < 80) | RSI.isna()
    
    # 条件7：价格位置合理（不追高）
    条件7 = C < MA60 * 1.35  # 距离MA60不超过35%
    
    # 条件8：股价不能太接近跌停（避免杀跌）
    昨收 = REF(C, 1)
    code = df['code'].iloc[0] if 'code' in df.columns else ''
    if code.startswith('688') or code.startswith('300'):
        跌停价 = 昨收 * 0.805
    else:
        跌停价 = 昨收 * 0.905
    条件8 = C > 跌停价 * 1.02  # 距离跌停要有2%以上
    
    # 条件9：必须通过策略1筛选
    条件9 = 策略1(df, start_date, end_date, mode='')
    
    # ========== 综合买入信号 ==========
    买入信号 = 条件1 & 条件2 & 条件3 & 条件4 & 条件5 & 条件6 & 条件7 & 条件8 & 条件9
    
    return 买入信号


# ==================== 卖出策略 ====================

def 卖策略(df, 策略2, start_date='', end_date=''):
    """
    动态止盈止损卖出策略
    
    卖出条件（满足任一即卖出）：
    1. 固定止盈：盈利达到15%
    2. 固定止损：亏损达到8%
    3. 技术止损：跌破MA10
    4. MACD止损：MACD死叉
    5. 动态止盈：从最高点回撤超过12%（保护利润）
    
    策略说明：
    - 优先保护本金（8%止损）
    - 锁定利润（15%止盈，回撤12%止盈）
    - 技术面恶化及时出局
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
    H = df['high']
    MA10 = SMA(C, 10)
    
    # MACD指标
    macd, signal, hist = talib.MACD(C.values, fastperiod=12, slowperiod=26, signalperiod=9)
    MACD_DIFF = pd.Series(macd, index=df.index)
    MACD_DEA = pd.Series(signal, index=df.index)
    
    # 找到所有买入点
    买入日期列表 = 策略2[策略2 == True].index.to_list()
    
    # 初始化卖出信号
    卖出信号 = pd.Series([False] * len(df), index=df.index)
    
    # 止盈止损参数
    固定止盈 = 0.15  # 15%
    固定止损 = 0.08  # 8%
    回撤止盈 = 0.12  # 从最高点回撤12%
    
    # 遍历每个买入点
    for 买入日期 in 买入日期列表:
        成本价 = C.loc[买入日期]
        最高价 = 成本价
        
        # 找到买入日期之后的所有日期
        后续日期 = df.loc[买入日期:].index[1:]  # 排除买入当天
        
        for 当前日期 in 后续日期:
            当前价 = C.loc[当前日期]
            当前高 = H.loc[当前日期]
            
            # 更新持仓期间最高价
            最高价 = max(最高价, 当前高)
            
            # 计算盈亏比例
            盈亏比 = (当前价 - 成本价) / 成本价
            
            # 计算从最高点的回撤
            回撤比 = (最高价 - 当前价) / 最高价 if 最高价 > 成本价 else 0
            
            # ========== 卖出条件判断 ==========
            
            # 1. 固定止盈（15%）
            if 盈亏比 >= 固定止盈:
                卖出信号[当前日期] = True
                break
            
            # 2. 固定止损（8%）
            if 盈亏比 <= -固定止损:
                卖出信号[当前日期] = True
                break
            
            # 3. 技术止损：跌破MA10
            if 当前价 < MA10.loc[当前日期]:
                卖出信号[当前日期] = True
                break
            
            # 4. MACD死叉
            if CROSS(MACD_DEA, MACD_DIFF).loc[当前日期]:
                卖出信号[当前日期] = True
                break
            
            # 5. 动态止盈：从最高点回撤超过12%（仅在盈利时）
            if 盈亏比 > 0.05 and 回撤比 > 回撤止盈:
                卖出信号[当前日期] = True
                break
    
    return 卖出信号


# ==================== 策略测试代码 ====================

if __name__ == '__main__':
    """
    策略测试代码
    用于验证策略是否能正常运行
    """
    import os
    import sys
    import user_config as ucfg
    
    print("=" * 70)
    print("高级量化策略测试")
    print("=" * 70)
    print("\n策略说明：")
    print("  买入策略：趋势追踪 + 突破确认")
    print("  卖出策略：动态止盈止损（固定15%止盈，8%止损）")
    print("  大盘过滤：仅在大盘向好时买入")
    print("\n" + "=" * 70)
    
    # 测试股票代码
    test_codes = ['000001', '600036', '000002', '600519']
    
    # ========== 1. 加载沪深300指数 ==========
    print("\n[1/3] 加载沪深300指数数据...")
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
        print(f"      [OK] 沪深300信号生成成功")
        print(f"      [OK] 最近5日信号: {HS300_信号.tail().to_list()}")
        print(f"      [OK] 当前大盘状态: {'向好' if HS300_信号.iloc[-1] else '不佳'}")
    except Exception as e:
        print(f"      [ERROR] 沪深300数据加载失败: {e}")
        print(f"      提示: 请先运行 readTDX_lday.py 生成指数数据")
        sys.exit(1)
    
    # ========== 2. 测试股票策略 ==========
    print(f"\n[2/3] 测试{len(test_codes)}只股票的策略信号...")
    print(f"\n{'股票代码':<10} {'策略1筛选':<12} {'最近买入信号':<15} {'信号日期'}")
    print("-" * 70)
    
    成功数 = 0
    买入股票 = []
    
    for code in test_codes:
        try:
            # 优先使用pickle文件（速度更快）
            pkl_file = ucfg.tdx['pickle'] + os.sep + code + '.pkl'
            csv_file = ucfg.tdx['csv_lday'] + os.sep + code + '.csv'
            
            if os.path.exists(pkl_file):
                df_stock = pd.read_pickle(pkl_file)
            elif os.path.exists(csv_file):
                df_stock = pd.read_csv(csv_file, index_col=None, encoding='gbk', dtype={'code': str})
                df_stock['date'] = pd.to_datetime(df_stock['date'], format='%Y-%m-%d')
                df_stock.set_index('date', drop=False, inplace=True)
            else:
                print(f"{code:<10} {'数据文件不存在':<12}")
                continue
            
            # 测试策略1
            result1_fast = 策略1(df_stock, mode='fast')
            
            # 测试策略2
            result2 = 策略2(df_stock, HS300_信号)
            
            # 找到最近的买入信号
            买入日期列表 = result2[result2 == True].index.to_list()
            if len(买入日期列表) > 0:
                最近日期 = 买入日期列表[-1]
                最近买入 = 最近日期.strftime('%Y-%m-%d') if hasattr(最近日期, 'strftime') else str(最近日期)[:10]
            else:
                最近买入 = '无'
            
            # 判断最后一天是否有买入信号
            今日信号 = '是[BUY]' if result2.iloc[-1] else '否'
            
            print(f"{code:<10} {'通过' if result1_fast else '未通过':<12} {今日信号:<15} {最近买入}")
            
            if result2.iloc[-1]:
                买入股票.append(code)
            
            成功数 += 1
            
        except Exception as e:
            print(f"{code:<10} 测试失败: {e}")
    
    # ========== 3. 测试总结 ==========
    print("\n" + "=" * 70)
    print(f"[3/3] 测试总结")
    print("=" * 70)
    print(f"  测试股票数: {len(test_codes)}")
    print(f"  测试成功数: {成功数}")
    print(f"  今日有买入信号的股票: {len(买入股票)}只")
    
    if len(买入股票) > 0:
        print(f"\n  今日可买入股票: {', '.join(买入股票)}")
    
    print("\n" + "=" * 70)
    print("策略测试完成！")
    print("=" * 70)
    print("\n如果以上测试通过，现在可以运行:")
    print("  1. python xuangu.py          # 选股")
    print("  2. python celue_save.py      # 生成策略信号")
    print("  3. python huice.py           # 回测策略")
    print("\n" + "=" * 70)
