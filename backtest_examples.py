#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
股票策略回测使用示例

演示如何使用新的股票策略回测系统，包括：
1. 基础回测流程
2. 多种策略配置
3. 结果分析
4. 参数调优

作者：AI助手优化版
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stock_backtest import StockBacktest, TrendFollowingStrategy, MultiFactorStrategy


def demo_basic_backtest():
    """基础回测示例"""
    print("\n" + "="*60)
    print("基础回测示例")
    print("="*60)
    
    # 创建回测引擎
    backtest = StockBacktest(
        initial_capital=10000000,  # 1000万初始资金
        start_date="2022-01-01",   # 回测开始日期
        end_date="2023-12-31"      # 回测结束日期
    )
    
    # 配置趋势跟踪策略
    trend_config = {
        'min_price': 5,                    # 最低股价5元
        'volume_ratio_threshold': 1.8,     # 成交量放大1.8倍
        'max_holding_days': 15,            # 最大持有15天
        'rsi_overbought': 70,              # RSI超买线70
        'rsi_oversold': 30                 # RSI超卖线30
    }
    
    trend_strategy = TrendFollowingStrategy(trend_config)
    backtest.add_strategy("趋势跟踪策略", trend_strategy)
    
    # 测试股票列表（包含不同行业的代表股票）
    stock_codes = [
        '000001',  # 平安银行
        '000002',  # 万科A
        '600519',  # 贵州茅台
        '600036',  # 招商银行
        '000858',  # 五粮液
        '600887',  # 伊利股份
        '000725',  # 京东方A
        '002415',  # 海康威视
    ]
    
    print(f"测试股票数量: {len(stock_codes)}")
    print(f"股票列表: {', '.join(stock_codes)}")
    print(f"回测期间: {backtest.start_date} ~ {backtest.end_date}")
    print(f"初始资金: {backtest.initial_capital:,} 元")
    
    # 运行回测
    print("\n正在运行回测...")
    results = backtest.run_backtest(stock_codes, strategy_name="趋势跟踪策略")
    
    # 分析结果
    print("\n回测结果:")
    print("-" * 60)
    
    for strategy_name, result in results.items():
        perf = result['performance']
        trades = result['trades']
        
        print(f"\n策略名称: {strategy_name}")
        print(f"总收益率: {perf.get('total_return', 0):.2%}")
        print(f"年化收益率: {perf.get('annualized_return', 0):.2%}")
        print(f"最大回撤: {perf.get('max_drawdown', 0):.2%}")
        print(f"夏普比率: {perf.get('sharpe_ratio', 0):.2f}")
        print(f"胜率: {perf.get('win_rate', 0):.2%}")
        print(f"交易次数: {perf.get('total_trades', 0)}")
        print(f"最终价值: {perf.get('final_value', 0):,.2f} 元")
        print(f"交易天数: {perf.get('trading_days', 0)} 天")
        
        # 显示部分交易记录
        if trades:
            print(f"\n部分交易记录:")
            recent_trades = trades[-5:]  # 显示最近5笔交易
            for i, trade in enumerate(recent_trades, 1):
                pnl_info = f"PnL:{trade.get('pnl', 0):,.0f}" if trade['type'] == 'SELL' else ''
                print(f"  {i}. {trade['date']} {trade['type']} {trade['stock_code']} "
                      f"{trade['quantity']}股 @{trade['price']:.2f} "
                      f"金额:{trade['amount']:,.0f} {pnl_info}")
    
    # 保存结果
    backtest.save_results("demo_basic.pkl")
    
    return results


def demo_multiple_strategies():
    """多策略对比示例"""
    print("\n" + "="*60)
    print("多策略对比示例")
    print("="*60)
    
    # 创建回测引擎
    backtest = StockBacktest(
        initial_capital=5000000,   # 500万初始资金
        start_date="2021-01-01",
        end_date="2023-12-31"
    )
    
    # 策略1: 保守型趋势跟踪
    conservative_trend = TrendFollowingStrategy({
        'min_price': 10,
        'volume_ratio_threshold': 2.5,     # 严格的成交量要求
        'max_holding_days': 10,            # 短期持有
        'rsi_overbought': 65,              # 较早止盈
        'rsi_oversold': 35,                # 较保守的买入
        'bb_position_threshold': 0.2       # 接近下轨才买入
    })
    
    # 策略2: 激进型趋势跟踪
    aggressive_trend = TrendFollowingStrategy({
        'min_price': 3,                    # 允许低价股
        'volume_ratio_threshold': 1.2,     # 较低的成交量要求
        'max_holding_days': 25,            # 长期持有
        'rsi_overbought': 80,              # 更高的止盈线
        'rsi_oversold': 25,                # 更激进的买入
        'bb_position_threshold': 0.8       # 接近上轨也买入
    })
    
    # 策略3: 多因子策略
    multi_factor = MultiFactorStrategy()
    multi_factor.factor_weights.update({
        'trend': 0.5,      # 重视趋势
        'momentum': 0.3,   # 重视动量
        'volume': 0.2      # 重视成交量
    })
    
    # 注册策略
    backtest.add_strategy("保守型趋势", conservative_trend)
    backtest.add_strategy("激进型趋势", aggressive_trend)
    backtest.add_strategy("多因子策略", multi_factor)
    
    # 股票池
    growth_stocks = ['000001', '600519', '600036', '000858', '002415']
    
    print(f"股票池: {', '.join(growth_stocks)}")
    print(f"对比策略: 3种策略")
    
    # 运行所有策略
    print("\n正在运行多策略对比...")
    results = backtest.run_backtest(growth_stocks)
    
    # 对比分析
    print("\n多策略对比结果:")
    print("-" * 80)
    print(f"{'策略名称':<12} {'总收益率':<10} {'年化收益率':<10} {'最大回撤':<10} {'夏普比率':<8} {'胜率':<8} {'交易次数':<8}")
    print("-" * 80)
    
    strategy_rankings = []
    for strategy_name, result in results.items():
        perf = result['performance']
        
        total_return = perf.get('total_return', 0)
        annualized_return = perf.get('annualized_return', 0)
        max_drawdown = perf.get('max_drawdown', 0)
        sharpe_ratio = perf.get('sharpe_ratio', 0)
        win_rate = perf.get('win_rate', 0)
        total_trades = perf.get('total_trades', 0)
        
        print(f"{strategy_name:<12} {total_return:<9.2%} {annualized_return:<9.2%} "
              f"{max_drawdown:<9.2%} {sharpe_ratio:<7.2f} {win_rate:<7.2%} {total_trades:<7}")
        
        # 计算综合评分（可自定义权重）
        composite_score = (annualized_return * 0.4 - abs(max_drawdown) * 0.3 + 
                          sharpe_ratio * 0.2 + win_rate * 0.1)
        strategy_rankings.append((strategy_name, composite_score))
    
    # 排序并显示最佳策略
    strategy_rankings.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n策略排名（综合评分）:")
    for i, (name, score) in enumerate(strategy_rankings, 1):
        print(f"  {i}. {name}: {score:.3f}")
    
    # 保存结果
    backtest.save_results("demo_multi_strategy.pkl")
    
    return results


def demo_parameter_optimization():
    """参数优化示例"""
    print("\n" + "="*60)
    print("参数优化示例")
    print("="*60)
    
    # 定义参数网格
    param_combinations = [
        {'volume_ratio_threshold': 1.2, 'max_holding_days': 10, 'rsi_overbought': 65},
        {'volume_ratio_threshold': 1.5, 'max_holding_days': 15, 'rsi_overbought': 70},
        {'volume_ratio_threshold': 1.8, 'max_holding_days': 20, 'rsi_overbought': 75},
        {'volume_ratio_threshold': 2.0, 'max_holding_days': 25, 'rsi_overbought': 80},
        {'volume_ratio_threshold': 2.5, 'max_holding_days': 30, 'rsi_overbought': 85},
    ]
    
    # 测试股票
    test_stocks = ['000001', '600519', '600036']
    
    # 存储优化结果
    optimization_results = []
    
    print(f"参数组合数量: {len(param_combinations)}")
    print(f"测试股票: {', '.join(test_stocks)}")
    
    for i, params in enumerate(param_combinations, 1):
        print(f"\n测试参数组合 {i}/{len(param_combinations)}: {params}")
        
        # 创建回测引擎
        backtest = StockBacktest(
            initial_capital=1000000,  # 100万用于参数测试
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        # 创建策略
        strategy = TrendFollowingStrategy(params)
        backtest.add_strategy(f"策略_{i}", strategy)
        
        # 运行回测
        results = backtest.run_backtest(test_stocks, strategy_name=f"策略_{i}")
        
        # 提取性能指标
        if results:
            strategy_result = list(results.values())[0]
            perf = strategy_result['performance']
            
            optimization_results.append({
                'params': params,
                'total_return': perf.get('total_return', 0),
                'annualized_return': perf.get('annualized_return', 0),
                'max_drawdown': perf.get('max_drawdown', 0),
                'sharpe_ratio': perf.get('sharpe_ratio', 0),
                'win_rate': perf.get('win_rate', 0),
                'total_trades': perf.get('total_trades', 0),
                'final_value': perf.get('final_value', 0)
            })
    
    # 找到最佳参数
    if optimization_results:
        # 按夏普比率排序
        best_result = max(optimization_results, key=lambda x: x['sharpe_ratio'])
        
        print(f"\n最佳参数组合（按夏普比率）:")
        print(f"参数: {best_result['params']}")
        print(f"总收益率: {best_result['total_return']:.2%}")
        print(f"年化收益率: {best_result['annualized_return']:.2%}")
        print(f"最大回撤: {best_result['max_drawdown']:.2%}")
        print(f"夏普比率: {best_result['sharpe_ratio']:.2f}")
        print(f"胜率: {best_result['win_rate']:.2%}")
        print(f"交易次数: {best_result['total_trades']}")
        
        # 保存优化结果
        df_optimization = pd.DataFrame(optimization_results)
        df_optimization.to_csv('parameter_optimization_results.csv', index=False, encoding='utf-8-sig')
        print(f"\n优化结果已保存到: parameter_optimization_results.csv")
    
    return optimization_results


def main():
    """主函数：运行所有示例"""
    print("股票策略回测系统 - 使用示例")
    print("=" * 80)
    
    try:
        # 示例1: 基础回测
        demo_basic_backtest()
        
        # 示例2: 多策略对比（注释掉以节省时间）
        # demo_multiple_strategies()
        
        # 示例3: 参数优化（注释掉以节省时间）
        # demo_parameter_optimization()
        
        print("\n" + "=" * 80)
        print("示例运行完成！")
        print("=" * 80)
        print("\n生成的文件:")
        print("- backtest_results/demo_basic.pkl: 基础回测结果")
        print("- backtest_results/demo_basic.csv: 回测汇总表")
        print("- stock_backtest.log: 运行日志")
        
        print("\n查看结果的Python代码:")
        print("""
import pickle
import pandas as pd

# 加载结果
with open('backtest_results/demo_basic.pkl', 'rb') as f:
    results = pickle.load(f)

# 查看策略性能
for strategy_name, result in results.items():
    perf = result['performance']
    print(f"策略: {strategy_name}")
    print(f"  总收益率: {perf['total_return']:.2%}")
    print(f"  夏普比率: {perf['sharpe_ratio']:.2f}")
    print(f"  最大回撤: {perf['max_drawdown']:.2%}")
""")
        
    except Exception as e:
        print(f"\n运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()