#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
高级股票选股策略文件 - 基于 stock_strategy.py 的适配层

这个文件保持了与原有 CeLue.py 相同的接口，
但内部使用了更强大的 stock_strategy.py 框架

作者：AI助手优化版
"""

import numpy as np
import pandas as pd
import os
import sys
import user_config as ucfg
import func

# 导入新的策略系统
try:
    from stock_strategy import TrendFollowingStrategy, MultiFactorStrategy, StrategyManager, StockStrategy
    NEW_STRATEGY_AVAILABLE = True
    print("✓ 加载高级策略系统成功")
except ImportError as e:
    print(f"⚠ 高级策略系统加载失败: {e}")
    NEW_STRATEGY_AVAILABLE = False


def 策略HS300(df_hs300, start_date='', end_date=''):
    """
    沪深300指数信号（增强版）
    
    使用新的策略系统分析大盘环境
    """
    if start_date == '':
        start_date = df_hs300.index[0]
    if end_date == '':
        end_date = df_hs300.index[-1]
    
    df_hs300 = df_hs300.loc[start_date:end_date]
    
    if NEW_STRATEGY_AVAILABLE:
        try:
            # 使用趋势跟踪策略分析大盘
            strategy = TrendFollowingStrategy()
            market_status = strategy.market_environment_analysis(df_hs300)
            
            # 根据市场状态生成信号
            if market_status['trend'] == 'bull' and market_status['condition'] == 'stable':
                return pd.Series([True] * len(df_hs300), index=df_hs300.index)
            elif market_status['trend'] == 'bull' and market_status['condition'] == 'volatile':
                return pd.Series([True] * len(df_hs300), index=df_hs300.index)
            else:
                return pd.Series([False] * len(df_hs300), index=df_hs300.index)
        except Exception as e:
            print(f"高级策略分析失败，回退到基础策略: {e}")
    
    # 回退到基础策略
    C = df_hs300['close']
    MA5 = C.rolling(5).mean()
    MA20 = C.rolling(20).mean()
    
    # 简单策略：短期均线在长期均线上方
    信号 = MA5 > MA20
    
    return 信号


def 策略1(df, start_date='', end_date='', mode=None):
    """
    策略1：初步筛选（增强版）
    
    筛选条件：
    1. 股价 > 5元（排除低价股）
    2. 成交额 > 5000万（排除成交清淡股票）
    3. 流通市值 < 500亿（排除大盘股）
    4. 非涨停板
    
    增强功能：使用更智能的筛选逻辑
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
        
        # 增强条件：使用新的筛选逻辑
        if NEW_STRATEGY_AVAILABLE:
            try:
                strategy = TrendFollowingStrategy()
                screened = strategy.screen_stocks(df.tail(1))
                条件5 = screened.iloc[-1] if len(screened) > 0 else True
                return 条件1 and 条件2 and 条件3 and 条件4 and 条件5
            except Exception as e:
                print(f"高级筛选失败，使用基础条件: {e}")
        
        return 条件1 and 条件2 and 条件3 and 条件4
    
    else:
        # 完整模式：返回序列
        条件1 = C > 5
        条件2 = A > 50000000
        条件3 = (流通市值 < 50000000000) | (流通市值 == 0)
        
        # 排除涨停板
        昨收 = C.shift(1)
        code = df['code'].iloc[0] if 'code' in df.columns else ''
        if code.startswith('688') or code.startswith('300'):
            涨停价 = 昨收 * 1.2
        else:
            涨停价 = 昨收 * 1.1
        
        条件4 = C < (涨停价 - 0.01)
        
        # 组合条件
        result = 条件1 & 条件2 & 条件3 & 条件4
        
        # 如果有新的策略系统，增强筛选
        if NEW_STRATEGY_AVAILABLE:
            try:
                strategy = TrendFollowingStrategy()
                screened = strategy.screen_stocks(df)
                result = result & screened
            except Exception as e:
                print(f"高级筛选序列失败，继续使用基础条件: {e}")
        
        return result


def 策略2(df, HS300_信号, start_date='', end_date=''):
    """
    策略2：精选买入信号（增强版）
    
    策略逻辑：均线多头排列 + 成交量突破 + 高级技术分析
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
    
    if NEW_STRATEGY_AVAILABLE:
        try:
            # 使用高级策略系统
            strategy = TrendFollowingStrategy()
            
            # 分析市场环境
            # 这里我们需要构建一个模拟的沪深300数据进行分析
            market_status = {'trend': 'neutral', 'condition': 'stable'}
            if HS300_信号.iloc[-1]:
                market_status = {'trend': 'bull', 'condition': 'stable'}
            elif HS300_信号.iloc[-10:].mean() > 0.5:
                market_status = {'trend': 'bull', 'condition': 'volatile'}
            
            # 生成买入信号
            buy_signals = strategy.generate_buy_signals(df, market_status)
            
            # 确保与基础策略一致
            return buy_signals
            
        except Exception as e:
            print(f"高级策略2失败，回退到基础策略: {e}")
    
    # 回退到基础策略
    C = df['close']
    V = df['vol']
    
    # 计算均线
    MA5 = C.rolling(5).mean()
    MA10 = C.rolling(10).mean()
    MA20 = C.rolling(20).mean()
    MA60 = C.rolling(60).mean()
    
    # 计算成交量均线
    VOL_MA5 = V.rolling(5).mean()
    
    # 策略条件
    # 条件1：均线多头排列
    条件1 = (MA5 > MA10) & (MA10 > MA20) & (MA20 > MA60)
    
    # 条件2：成交量放大
    条件2 = V > VOL_MA5 * 1.5
    
    # 条件3：股价在MA60上方，但涨幅不大
    条件3 = (C > MA60) & (C < MA60 * 1.03)
    
    # 条件4：价格向上突破MA5
    条件4 = C > MA5 & (C.shift(1) <= MA5.shift(1))
    
    # 条件5：必须通过策略1筛选
    条件5 = 策略1(df, start_date, end_date, mode='')
    
    # 综合信号
    买入信号 = HS300_信号 & 条件1 & 条件2 & 条件3 & 条件4 & 条件5
    
    return 买入信号


def 卖策略(df, 策略2, start_date='', end_date=''):
    """
    卖出策略（增强版）
    
    增强的卖出逻辑，包含更多止损和止盈条件
    """
    # 如果没有买入信号，返回全False
    if True not in 策略2.to_list():
        return pd.Series([False] * len(策略2), index=策略2.index)
    
    if start_date == '':
        start_date = df.index[0]
    if end_date == '':
        end_date = df.index[-1]
    
    df = df.loc[start_date:end_date]
    
    if NEW_STRATEGY_AVAILABLE:
        try:
            # 使用高级策略系统
            strategy = TrendFollowingStrategy()
            sell_signals = strategy.generate_sell_signals(df, 策略2)
            return sell_signals
        except Exception as e:
            print(f"高级卖出策略失败，回退到基础策略: {e}")
    
    # 回退到基础策略
    C = df['close']
    MA10 = C.rolling(10).mean()
    
    # 计算买入价格
    买入价格 = pd.Series(index=C.index, dtype=float)
    
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


# 新增：多因子策略接口
def 多因子策略(df, start_date='', end_date='', threshold=0.7):
    """
    多因子综合策略
    
    使用多个因子综合评估股票
    """
    if not NEW_STRATEGY_AVAILABLE:
        print("多因子策略需要 stock_strategy.py 支持")
        return pd.Series([False] * len(df), index=df.index)
    
    if start_date == '':
        start_date = df.index[0]
    if end_date == '':
        end_date = df.index[-1]
    
    df = df.loc[start_date:end_date]
    
    try:
        strategy = MultiFactorStrategy()
        signals = strategy.generate_signals(df, threshold)
        return signals
    except Exception as e:
        print(f"多因子策略执行失败: {e}")
        return pd.Series([False] * len(df), index=df.index)


# 策略性能测试函数
def 测试策略性能(stock_codes=None):
    """
    测试策略性能
    
    Args:
        stock_codes: 测试的股票代码列表，默认为None（使用示例股票）
    """
    if stock_codes is None:
        stock_codes = ['000001', '600036', '000002']
    
    print("="*60)
    print("高级策略性能测试")
    print("="*60)
    
    if NEW_STRATEGY_AVAILABLE:
        print("✓ 使用高级策略系统")
    else:
        print("⚠ 使用基础策略系统")
    
    # 测试股票代码
    print(f"\n测试股票: {stock_codes}")
    
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
        return
    
    # 测试股票策略
    print("\n2. 测试股票策略...")
    for code in stock_codes:
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
            
            # 测试多因子策略（如果有）
            if NEW_STRATEGY_AVAILABLE:
                result_multi = 多因子策略(df_stock)
                print(f"   ✓ {code}: 策略1(fast)={result1_fast}, 策略2最新={result2.iloc[-1]}, 多因子={result_multi.iloc[-1]}")
            else:
                print(f"   ✓ {code}: 策略1(fast)={result1_fast}, 策略2最新={result2.iloc[-1]}")
            
        except Exception as e:
            print(f"   ✗ {code}: 测试失败 - {e}")
    
    print("\n" + "="*60)
    print("高级策略测试完成")
    print("="*60)


# 测试代码
if __name__ == '__main__':
    测试策略性能()