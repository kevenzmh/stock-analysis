#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测结果查看器
查看和分析回测结果

运行方式: python view_backtest_results.py
"""

import os
import sys
import pickle
from pathlib import Path
import pandas as pd

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"{msg}")
    print(f"{'='*70}{Colors.END}\n")

def print_metric(name, value, is_good=None):
    """打印指标"""
    if is_good is True:
        color = Colors.GREEN
    elif is_good is False:
        color = Colors.RED
    else:
        color = Colors.CYAN
    
    print(f"{name:.<40} {color}{value}{Colors.END}")

def format_percentage(value):
    """格式化百分比"""
    return f"{value*100:.2f}%"

def format_number(value):
    """格式化数字"""
    return f"{value:,.2f}"

def load_latest_result():
    """加载最新的回测结果"""
    result_dir = Path('rq_result')
    
    if not result_dir.exists():
        print(f"{Colors.RED}回测结果目录不存在{Colors.END}")
        print("请先运行回测: python huice.py")
        return None
    
    # 查找所有pkl文件
    pkl_files = list(result_dir.glob('*.pkl'))
    
    if not pkl_files:
        print(f"{Colors.RED}未找到回测结果文件{Colors.END}")
        return None
    
    # 按修改时间排序，获取最新的
    latest_file = max(pkl_files, key=lambda p: p.stat().st_mtime)
    
    print(f"{Colors.BLUE}加载回测结果:{Colors.END} {latest_file.name}")
    
    try:
        with open(latest_file, 'rb') as f:
            result = pickle.load(f)
        return result, latest_file
    except Exception as e:
        print(f"{Colors.RED}加载失败: {e}{Colors.END}")
        return None

def display_summary(summary):
    """显示回测摘要"""
    print_header("回测摘要")
    
    # 基本信息
    print(f"{Colors.BOLD}时间范围:{Colors.END}")
    print_metric("开始日期", summary['start_date'])
    print_metric("结束日期", summary['end_date'])
    
    # 收益指标
    print(f"\n{Colors.BOLD}收益指标:{Colors.END}")
    
    total_returns = summary['total_returns']
    print_metric("总收益率", format_percentage(total_returns), 
                is_good=total_returns > 0)
    
    annual_returns = summary['annualized_returns']
    print_metric("年化收益率", format_percentage(annual_returns),
                is_good=annual_returns > 0.1)
    
    # 基准对比
    print(f"\n{Colors.BOLD}基准对比:{Colors.END}")
    
    benchmark_returns = summary['benchmark_total_returns']
    print_metric("基准总收益", format_percentage(benchmark_returns))
    
    benchmark_annual = summary['benchmark_annualized_returns']
    print_metric("基准年化收益", format_percentage(benchmark_annual))
    
    alpha = summary['alpha']
    print_metric("Alpha (超额收益)", format_percentage(alpha),
                is_good=alpha > 0)
    
    beta = summary['beta']
    print_metric("Beta (波动相关性)", f"{beta:.4f}")
    
    # 风险指标
    print(f"\n{Colors.BOLD}风险指标:{Colors.END}")
    
    sharpe = summary['sharpe']
    print_metric("夏普比率", f"{sharpe:.4f}",
                is_good=sharpe > 1)
    
    max_dd = summary['max_drawdown']
    print_metric("最大回撤", format_percentage(max_dd),
                is_good=max_dd > -0.3)
    
    volatility = summary['volatility']
    print_metric("波动率", format_percentage(volatility))
    
    # 交易统计
    if 'total_trades' in summary:
        print(f"\n{Colors.BOLD}交易统计:{Colors.END}")
        print_metric("总交易次数", f"{summary['total_trades']}")
        
        if 'win_rate' in summary:
            win_rate = summary['win_rate']
            print_metric("胜率", format_percentage(win_rate),
                        is_good=win_rate > 0.5)

def display_trades(trades_df):
    """显示交易明细"""
    print_header("交易明细")
    
    if trades_df is None or len(trades_df) == 0:
        print("无交易记录")
        return
    
    print(f"总交易数: {len(trades_df)}")
    print()
    
    # 显示最近10笔交易
    print(f"{Colors.BOLD}最近10笔交易:{Colors.END}")
    
    recent_trades = trades_df.tail(10)
    
    # 格式化显示
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 20)
    
    print(recent_trades[['order_book_id', 'side', 'filled_quantity', 
                         'avg_price', 'transaction_cost']].to_string())
    
    # 统计买卖次数
    buy_count = len(trades_df[trades_df['side'] == 'BUY'])
    sell_count = len(trades_df[trades_df['side'] == 'SELL'])
    
    print(f"\n{Colors.GREEN}买入次数: {buy_count}{Colors.END}")
    print(f"{Colors.RED}卖出次数: {sell_count}{Colors.END}")

def display_positions(result):
    """显示持仓统计"""
    print_header("持仓统计")
    
    if 'stock_positions' not in result:
        print("无持仓数据")
        return
    
    positions = result['stock_positions']
    
    if positions is None or len(positions) == 0:
        print("无持仓记录")
        return
    
    print(f"持仓记录数: {len(positions)}")
    
    # 计算持仓统计
    if 'quantity' in positions.columns:
        # 统计持有过的股票
        unique_stocks = positions[positions['quantity'] > 0]['order_book_id'].nunique() if 'order_book_id' in positions.columns else 0
        print(f"持有过的股票数: {unique_stocks}")

def analyze_performance(result):
    """分析策略表现"""
    print_header("策略表现分析")
    
    summary = result['summary']
    
    # 收益评价
    print(f"{Colors.BOLD}收益评价:{Colors.END}")
    
    total_returns = summary['total_returns']
    if total_returns > 0.5:
        print(f"{Colors.GREEN}✓ 总收益优秀 (>50%){Colors.END}")
    elif total_returns > 0.2:
        print(f"{Colors.YELLOW}○ 总收益良好 (20%-50%){Colors.END}")
    elif total_returns > 0:
        print(f"{Colors.YELLOW}○ 总收益一般 (0%-20%){Colors.END}")
    else:
        print(f"{Colors.RED}✗ 策略亏损{Colors.END}")
    
    # 风险评价
    print(f"\n{Colors.BOLD}风险评价:{Colors.END}")
    
    max_dd = summary['max_drawdown']
    if max_dd > -0.1:
        print(f"{Colors.GREEN}✓ 回撤控制优秀 (<10%){Colors.END}")
    elif max_dd > -0.2:
        print(f"{Colors.YELLOW}○ 回撤控制良好 (10%-20%){Colors.END}")
    elif max_dd > -0.3:
        print(f"{Colors.YELLOW}○ 回撤一般 (20%-30%){Colors.END}")
    else:
        print(f"{Colors.RED}✗ 回撤较大 (>30%){Colors.END}")
    
    sharpe = summary['sharpe']
    if sharpe > 2:
        print(f"{Colors.GREEN}✓ 风险调整收益优秀 (夏普>2){Colors.END}")
    elif sharpe > 1:
        print(f"{Colors.YELLOW}○ 风险调整收益良好 (夏普1-2){Colors.END}")
    elif sharpe > 0:
        print(f"{Colors.YELLOW}○ 风险调整收益一般 (夏普0-1){Colors.END}")
    else:
        print(f"{Colors.RED}✗ 风险调整收益较差 (夏普<0){Colors.END}")
    
    # 综合评价
    print(f"\n{Colors.BOLD}综合评价:{Colors.END}")
    
    score = 0
    if total_returns > 0.2: score += 2
    elif total_returns > 0: score += 1
    
    if max_dd > -0.2: score += 2
    elif max_dd > -0.3: score += 1
    
    if sharpe > 1: score += 2
    elif sharpe > 0: score += 1
    
    alpha = summary['alpha']
    if alpha > 0: score += 1
    
    if score >= 6:
        print(f"{Colors.GREEN}★★★★★ 策略表现优秀{Colors.END}")
    elif score >= 4:
        print(f"{Colors.YELLOW}★★★☆☆ 策略表现良好{Colors.END}")
    elif score >= 2:
        print(f"{Colors.YELLOW}★★☆☆☆ 策略表现一般{Colors.END}")
    else:
        print(f"{Colors.RED}★☆☆☆☆ 策略需要改进{Colors.END}")
    
    # 建议
    print(f"\n{Colors.BOLD}优化建议:{Colors.END}")
    
    if total_returns < 0:
        print("• 策略亏损，建议重新审视选股逻辑")
    
    if max_dd < -0.3:
        print("• 回撤较大，建议增加止损条件")
    
    if sharpe < 1:
        print("• 夏普比率较低，建议优化风险收益比")
    
    if alpha < 0:
        print("• Alpha为负，建议优化选股时机或标的")
    
    if score >= 4:
        print(f"{Colors.GREEN}• 策略表现不错，可以考虑实盘测试{Colors.END}")

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*22 + "回测结果查看器" + " "*22 + "║")
    print("╚" + "═"*68 + "╝")
    print(f"{Colors.END}\n")
    
    # 加载回测结果
    result_data = load_latest_result()
    
    if result_data is None:
        return 1
    
    result, result_file = result_data
    
    # 显示各部分
    display_summary(result['summary'])
    
    if 'trades' in result:
        display_trades(result['trades'])
    
    display_positions(result)
    
    analyze_performance(result)
    
    # 提示查看图表
    print_header("查看更多")
    
    print("查看可视化结果:")
    print(f"  浏览器打开: {Colors.GREEN}pyecharts.html{Colors.END}")
    
    print("\n查看详细数据:")
    print(f"  回测结果文件: {Colors.CYAN}{result_file}{Colors.END}")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}已退出{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}程序异常: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
