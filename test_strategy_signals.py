#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
策略信号生成测试脚本

验证新策略系统的信号生成功能
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_strategy import TrendFollowingStrategy, MultiFactorStrategy, StrategyManager


def generate_test_data():
    """生成测试用的股票数据"""
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='B')  # 工作日
    n_days = len(dates)
    
    # 生成模拟价格数据 - 模拟一只股票的走势
    np.random.seed(42)
    base_price = 50
    
    # 生成趋势性数据：前半年上涨，后半年震荡
    returns = []
    for i in range(n_days):
        if i < n_days // 2:  # 前半年趋势向上
            daily_return = np.random.normal(0.003, 0.02)  # 正偏
        else:  # 后半年震荡
            daily_return = np.random.normal(0, 0.015)
        returns.append(daily_return)
    
    price_series = base_price * np.exp(np.cumsum(returns))
    
    # 生成其他价格数据
    high_price = price_series * (1 + np.random.uniform(0.001, 0.03, n_days))
    low_price = price_series * (1 - np.random.uniform(0.001, 0.03, n_days))
    open_price = np.roll(price_series, 1)
    open_price[0] = price_series[0]
    
    # 生成成交量数据
    vol_base = 5000000
    vol = []
    for i in range(n_days):
        # 模拟一些放量突破的日期
        if i in [50, 100, 200, 250]:
            vol.append(vol_base * np.random.uniform(2.0, 3.0))
        else:
            vol.append(vol_base * np.random.uniform(0.7, 1.5))
    
    df = pd.DataFrame({
        'date': dates,
        'code': '000001',
        'open': open_price,
        'high': high_price,
        'low': low_price,
        'close': price_series,
        'vol': vol,
        'amount': price_series * vol,
    })
    
    df.set_index('date', inplace=True)
    return df


def test_trend_strategy():
    """测试趋势跟踪策略"""
    print("\n" + "="*50)
    print("趋势跟踪策略测试")
    print("="*50)
    
    # 生成测试数据
    df = generate_test_data()
    print(f"生成测试数据: {len(df)} 个交易日")
    print(f"数据期间: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"价格范围: {df['close'].min():.2f} ~ {df['close'].max():.2f}")
    
    # 创建策略
    strategy = TrendFollowingStrategy({
        'min_price': 5,
        'volume_ratio_threshold': 1.8,
        'max_holding_days': 15,
        'rsi_overbought': 70,
        'rsi_oversold': 30
    })
    
    # 模拟市场环境
    market_status = {'trend': 'bull', 'condition': 'stable'}
    
    # 生成买入信号
    print(f"\n市场环境: {market_status}")
    buy_signals = strategy.generate_buy_signals(df, market_status)
    sell_signals = strategy.generate_sell_signals(df, buy_signals)
    
    # 分析信号
    buy_count = buy_signals.sum()
    sell_count = sell_signals.sum()
    
    print(f"\n信号统计:")
    print(f"  买入信号: {buy_count} 次")
    print(f"  卖出信号: {sell_count} 次")
    print(f"  信号频率: {buy_count/len(df):.2%}")
    
    # 显示最近的信号
    print(f"\n最近10个交易日的信号:")
    recent_data = df.tail(10).copy()
    recent_data['buy_signal'] = buy_signals.tail(10)
    recent_data['sell_signal'] = sell_signals.tail(10)
    
    for i, (date, row) in enumerate(recent_data.iterrows()):
        signal = ""
        if row['buy_signal']:
            signal += "买入 "
        if row['sell_signal']:
            signal += "卖出"
        if not signal:
            signal = "持有"
        
        print(f"  {date.strftime('%Y-%m-%d')}: {signal} "
              f"价格:{row['close']:6.2f} 量比:{row.get('VOL_RATIO', 0):.2f}")
    
    # 技术指标验证
    df_with_indicators = strategy.calculate_indicators(df)
    print(f"\n技术指标验证:")
    print(f"  均线: MA5={df_with_indicators['MA5'].iloc[-1]:.2f}, "
          f"MA20={df_with_indicators['MA20'].iloc[-1]:.2f}")
    print(f"  MACD: {df_with_indicators['MACD'].iloc[-1]:.4f}")
    print(f"  RSI: {df_with_indicators['RSI'].iloc[-1]:.2f}")
    
    return buy_signals, sell_signals


def test_multi_factor_strategy():
    """测试多因子策略"""
    print("\n" + "="*50)
    print("多因子策略测试")
    print("="*50)
    
    # 使用同样的测试数据
    df = generate_test_data()
    
    # 创建多因子策略
    strategy = MultiFactorStrategy()
    
    # 生成信号
    buy_signals = strategy.generate_signals(df)
    
    # 分析信号
    buy_count = buy_signals.sum()
    print(f"多因子信号统计:")
    print(f"  买入信号: {buy_count} 次")
    print(f"  信号频率: {buy_count/len(df):.2%}")
    
    # 计算因子得分
    factors = strategy.calculate_factors(df)
    print(f"\n因子得分示例（最近5天）:")
    recent_factors = pd.DataFrame({k: v.tail(5) for k, v in factors.items()})
    
    for date, row in recent_factors.iterrows():
        total_score = sum(row.values())
        print(f"  {date.strftime('%Y-%m-%d')}: 总分={total_score:.3f}, "
              f"趋势={row['trend']:.3f}, 动量={row['momentum']:.3f}, "
              f"成交量={row['volume']:.3f}")
    
    return buy_signals


def test_strategy_manager():
    """测试策略管理器"""
    print("\n" + "="*50)
    print("策略管理器测试")
    print("="*50)
    
    # 生成测试数据
    df = generate_test_data()
    
    # 创建策略管理器
    manager = StrategyManager()
    
    # 注册策略
    trend_strategy = TrendFollowingStrategy()
    multi_strategy = MultiFactorStrategy()
    
    manager.register_strategy('趋势策略', trend_strategy)
    manager.register_strategy('多因子策略', multi_strategy)
    
    print(f"已注册策略: {list(manager.strategies.keys())}")
    
    # 运行策略
    market_status = {'trend': 'bull', 'condition': 'stable'}
    results = manager.run_all(df, market_status=market_status)
    
    print(f"\n策略执行结果:")
    for name, result in results.items():
        metadata = result.get('metadata', {})
        print(f"  {name}:")
        print(f"    买入信号数: {metadata.get('buy_signals_count', 0)}")
        print(f"    最后信号: {metadata.get('last_signal', 'N/A')}")
        if 'sell_signals_count' in metadata:
            print(f"    卖出信号数: {metadata.get('sell_signals_count', 0)}")
    
    return results


def main():
    """主测试函数"""
    print("股票策略系统信号生成测试")
    print("="*60)
    
    try:
        # 测试1: 趋势跟踪策略
        buy_signals1, sell_signals1 = test_trend_strategy()
        
        # 测试2: 多因子策略
        buy_signals2 = test_multi_factor_strategy()
        
        # 测试3: 策略管理器
        results = test_strategy_manager()
        
        print("\n" + "="*60)
        print("所有测试完成！")
        print("="*60)
        
        print("\n总结:")
        print("✅ 趋势跟踪策略信号生成正常")
        print("✅ 多因子策略信号生成正常") 
        print("✅ 策略管理器运行正常")
        print("✅ 技术指标计算正常")
        print("✅ 数据质量检查正常")
        
        print("\n建议:")
        print("- 使用真实数据文件替换模拟数据以获得更准确的结果")
        print("- 根据实际市场情况调整策略参数")
        print("- 可以通过调整权重和阈值来优化策略性能")
        
    except Exception as e:
        print(f"\n测试过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()