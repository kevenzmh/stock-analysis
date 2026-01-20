#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
简化回测演示脚本

说明：
由于完整回测需要：
1. 生成所有股票的历史策略信号（耗时较长）
2. 安装rqalpha回测框架
3. 下载完整的历史数据

本脚本提供一个简化的演示，展示策略的基本效果。

运行方法：
    python demo_backtest.py
"""

import os
import sys
import pandas as pd
import numpy as np
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import track
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from datetime import datetime

# 导入策略
import CeLue
try:
    import CeLue_improved
    USE_IMPROVED = True
except ImportError:
    USE_IMPROVED = False

import user_config as ucfg

console = Console()

# 回测参数
START_DATE = '2023-01-01'
END_DATE = '2025-01-20'
INITIAL_CAPITAL = 1000000  # 初始资金100万
POSITION_SIZE = 100000  # 每只股票买入10万

class SimpleBacktest:
    """简化的回测类"""
    
    def __init__(self, initial_capital=INITIAL_CAPITAL):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {股票代码: {'shares': 数量, 'cost': 成本价}}
        self.history = []  # 每日净值记录
        self.trades = []  # 交易记录
        
    def get_portfolio_value(self, date, prices):
        """计算当前组合总价值"""
        position_value = 0
        for code, pos in self.positions.items():
            if code in prices:
                position_value += pos['shares'] * prices[code]
        return self.cash + position_value
    
    def buy(self, code, price, date):
        """买入股票"""
        if self.cash < POSITION_SIZE:
            return False
        
        shares = int(POSITION_SIZE / price / 100) * 100  # 100股为一手
        if shares == 0:
            return False
        
        cost = shares * price * 1.0003  # 加上手续费0.03%
        
        if cost > self.cash:
            return False
        
        self.cash -= cost
        self.positions[code] = {
            'shares': shares,
            'cost': price,
            'buy_date': date
        }
        
        self.trades.append({
            'date': date,
            'code': code,
            'action': 'BUY',
            'price': price,
            'shares': shares,
            'amount': cost
        })
        return True
    
    def sell(self, code, price, date):
        """卖出股票"""
        if code not in self.positions:
            return False
        
        pos = self.positions[code]
        revenue = pos['shares'] * price * 0.9987  # 扣除手续费和印花税
        profit = revenue - (pos['shares'] * pos['cost'] * 1.0003)
        profit_rate = (price / pos['cost'] - 1) * 100
        
        self.cash += revenue
        
        self.trades.append({
            'date': date,
            'code': code,
            'action': 'SELL',
            'price': price,
            'shares': pos['shares'],
            'amount': revenue,
            'profit': profit,
            'profit_rate': profit_rate,
            'hold_days': (pd.to_datetime(date) - pd.to_datetime(pos['buy_date'])).days
        })
        
        del self.positions[code]
        return True


def run_simple_backtest(test_stocks=None):
    """运行简化回测"""
    
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]简化回测演示[/bold cyan]")
    console.print("=" * 70 + "\n")
    
    if USE_IMPROVED:
        console.print("[green]OK 使用改进版策略[/green]")
    else:
        console.print("[yellow]OK 使用原始策略[/yellow]")
    
    console.print(f"[cyan]回测区间: {START_DATE} 至 {END_DATE}[/cyan]")
    console.print(f"[cyan]初始资金: {INITIAL_CAPITAL:,} 元[/cyan]")
    console.print(f"[cyan]单股仓位: {POSITION_SIZE:,} 元[/cyan]\n")
    
    # 测试股票列表（如果没指定，使用默认的）
    if test_stocks is None:
        test_stocks = ['000001', '600036', '000002', '600519', '000858', 
                      '601318', '600000', '000333', '002415', '600276']
    
    console.print(f"[yellow]测试股票数: {len(test_stocks)} 只[/yellow]")
    console.print(f"[dim]注: 完整回测会测试所有{4000}+只股票[/dim]\n")
    
    # 加载沪深300
    console.print("[1/5] 加载沪深300数据...")
    df_hs300 = pd.read_csv(
        ucfg.tdx['csv_index'] + '/000300.csv',
        index_col=None,
        encoding='gbk',
        dtype={'code': str}
    )
    df_hs300['date'] = pd.to_datetime(df_hs300['date'], format='%Y-%m-%d')
    df_hs300.set_index('date', drop=False, inplace=True)
    HS300_信号 = CeLue.策略HS300(df_hs300)
    console.print("[green]✓ 沪深300信号生成完成[/green]\n")
    
    # 初始化回测
    backtest = SimpleBacktest()
    
    # 加载测试股票数据
    console.print("[2/5] 加载测试股票数据...")
    stock_data = {}
    available_stocks = []
    
    for code in track(test_stocks, description="加载中..."):
        try:
            pkl_file = ucfg.tdx['pickle'] + os.sep + code + '.pkl'
            if os.path.exists(pkl_file):
                df = pd.read_pickle(pkl_file)
                df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
                df.set_index('date', drop=False, inplace=True)
                df = df.loc[START_DATE:END_DATE]
                
                # 生成策略信号
                buy_signal = CeLue.策略2(df, HS300_信号)
                sell_signal = CeLue.卖策略(df, buy_signal)
                
                df['buy_signal'] = buy_signal
                df['sell_signal'] = sell_signal
                
                stock_data[code] = df
                available_stocks.append(code)
        except Exception as e:
            console.print(f"[yellow]⚠️  {code}: {str(e)[:30]}...[/yellow]")
            continue
    
    console.print(f"[green]✓ 成功加载 {len(available_stocks)} 只股票[/green]\n")
    
    if len(available_stocks) == 0:
        console.print("[red]❌ 没有可用的股票数据，无法回测[/red]")
        return
    
    # 运行回测
    console.print("[3/5] 运行回测...")
    
    # 获取所有交易日
    all_dates = sorted(set().union(*[set(df.index) for df in stock_data.values()]))
    
    for date in track(all_dates, description="回测中..."):
        date_str = date.strftime('%Y-%m-%d')
        
        # 获取当日价格
        current_prices = {}
        for code in available_stocks:
            if date in stock_data[code].index:
                current_prices[code] = stock_data[code].loc[date, 'close']
        
        # 卖出信号
        for code in list(backtest.positions.keys()):
            if date in stock_data[code].index:
                if stock_data[code].loc[date, 'sell_signal']:
                    price = stock_data[code].loc[date, 'close']
                    backtest.sell(code, price, date_str)
        
        # 买入信号
        for code in available_stocks:
            if code not in backtest.positions:
                if date in stock_data[code].index:
                    if stock_data[code].loc[date, 'buy_signal']:
                        price = stock_data[code].loc[date, 'close']
                        backtest.buy(code, price, date_str)
        
        # 记录每日净值
        portfolio_value = backtest.get_portfolio_value(date_str, current_prices)
        backtest.history.append({
            'date': date,
            'value': portfolio_value,
            'cash': backtest.cash,
            'positions': len(backtest.positions)
        })
    
    console.print("[green]✓ 回测完成[/green]\n")
    
    # 计算回测指标
    console.print("[4/5] 计算回测指标...")
    
    df_history = pd.DataFrame(backtest.history)
    df_history.set_index('date', inplace=True)
    
    # 计算收益率
    total_return = (df_history['value'].iloc[-1] / INITIAL_CAPITAL - 1) * 100
    days = (df_history.index[-1] - df_history.index[0]).days
    annual_return = (((df_history['value'].iloc[-1] / INITIAL_CAPITAL) ** (365 / days)) - 1) * 100
    
    # 计算最大回撤
    df_history['cummax'] = df_history['value'].cummax()
    df_history['drawdown'] = (df_history['value'] / df_history['cummax'] - 1) * 100
    max_drawdown = df_history['drawdown'].min()
    
    # 计算沪深300收益
    hs300_start = df_hs300.loc[START_DATE:END_DATE].iloc[0]['close']
    hs300_end = df_hs300.loc[START_DATE:END_DATE].iloc[-1]['close']
    hs300_return = (hs300_end / hs300_start - 1) * 100
    
    # 交易统计
    df_trades = pd.DataFrame(backtest.trades)
    sell_trades = df_trades[df_trades['action'] == 'SELL']
    win_trades = sell_trades[sell_trades['profit'] > 0]
    
    win_rate = len(win_trades) / len(sell_trades) * 100 if len(sell_trades) > 0 else 0
    avg_profit_rate = sell_trades['profit_rate'].mean() if len(sell_trades) > 0 else 0
    avg_hold_days = sell_trades['hold_days'].mean() if len(sell_trades) > 0 else 0
    
    console.print("[green]✓ 指标计算完成[/green]\n")
    
    # 显示结果
    console.print("[5/5] 显示回测结果...")
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]📊 回测结果[/bold cyan]")
    console.print("=" * 70 + "\n")
    
    # 收益指标表
    result_table = Table(title="收益指标", show_header=True, header_style="bold magenta")
    result_table.add_column("指标", style="cyan", width=20)
    result_table.add_column("数值", style="yellow", width=20)
    result_table.add_column("评价", style="green", width=25)
    
    result_table.add_row(
        "总收益率",
        f"{total_return:+.2f}%",
        "优秀" if total_return > 50 else "良好" if total_return > 20 else "一般"
    )
    
    result_table.add_row(
        "年化收益率",
        f"{annual_return:+.2f}%",
        "优秀" if annual_return > 20 else "良好" if annual_return > 10 else "一般"
    )
    
    result_table.add_row(
        "沪深300收益",
        f"{hs300_return:+.2f}%",
        "-"
    )
    
    result_table.add_row(
        "超额收益",
        f"{total_return - hs300_return:+.2f}%",
        "跑赢" if total_return > hs300_return else "跑输"
    )
    
    result_table.add_row(
        "最大回撤",
        f"{max_drawdown:.2f}%",
        "优秀" if max_drawdown > -20 else "良好" if max_drawdown > -30 else "较大"
    )
    
    console.print(result_table)
    
    # 交易统计表
    trade_table = Table(title="\n交易统计", show_header=True, header_style="bold magenta")
    trade_table.add_column("指标", style="cyan", width=20)
    trade_table.add_column("数值", style="yellow", width=20)
    
    trade_table.add_row("总交易次数", f"{len(df_trades)}")
    trade_table.add_row("买入次数", f"{len(df_trades[df_trades['action'] == 'BUY'])}")
    trade_table.add_row("卖出次数", f"{len(sell_trades)}")
    trade_table.add_row("胜率", f"{win_rate:.1f}%")
    trade_table.add_row("平均收益率", f"{avg_profit_rate:+.2f}%")
    trade_table.add_row("平均持仓天数", f"{avg_hold_days:.1f} 天")
    
    console.print(trade_table)
    
    # 绘制净值曲线
    console.print("\n[yellow]正在生成净值曲线图...[/yellow]")
    
    plt.figure(figsize=(12, 6))
    plt.plot(df_history.index, df_history['value'], label='策略净值', linewidth=2)
    plt.axhline(y=INITIAL_CAPITAL, color='r', linestyle='--', label='初始资金', alpha=0.5)
    
    # 添加沪深300对比
    hs300_values = []
    for date in df_history.index:
        if date in df_hs300.index:
            hs300_value = INITIAL_CAPITAL * (df_hs300.loc[date, 'close'] / hs300_start)
            hs300_values.append(hs300_value)
        else:
            hs300_values.append(hs300_values[-1] if hs300_values else INITIAL_CAPITAL)
    
    plt.plot(df_history.index, hs300_values, label='沪深300', linewidth=2, alpha=0.7)
    
    plt.xlabel('日期')
    plt.ylabel('净值（元）')
    plt.title(f'回测净值曲线 ({START_DATE} 至 {END_DATE})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_file = 'backtest_result.png'
    plt.savefig(output_file, dpi=150)
    console.print(f"[green]✓ 净值曲线已保存到: {output_file}[/green]")
    
    # 保存交易明细
    if len(sell_trades) > 0:
        sell_trades.to_csv('trade_details.csv', index=False, encoding='gbk')
        console.print(f"[green]✓ 交易明细已保存到: trade_details.csv[/green]")
    
    console.print("\n" + "=" * 70)
    console.print("[bold green]✅ 回测演示完成！[/bold green]")
    console.print("=" * 70 + "\n")
    
    # 总结建议
    console.print("[bold yellow]💡 投资建议：[/bold yellow]")
    
    if total_return > 30 and max_drawdown > -25:
        console.print("[green]• 策略表现优秀，收益高且回撤可控[/green]")
    elif total_return > 15:
        console.print("[green]• 策略表现良好，建议小资金试验[/green]")
    else:
        console.print("[yellow]• 策略表现一般，建议优化参数或观望[/yellow]")
    
    if win_rate > 50:
        console.print(f"[green]• 胜率{win_rate:.1f}%，策略稳定性较好[/green]")
    else:
        console.print(f"[yellow]• 胜率{win_rate:.1f}%，需要提高选股精准度[/yellow]")
    
    if total_return > hs300_return:
        console.print(f"[green]• 跑赢基准{total_return - hs300_return:.2f}%，策略有效[/green]")
    else:
        console.print(f"[red]• 跑输基准{hs300_return - total_return:.2f}%，建议改进策略[/red]")
    
    console.print("\n[cyan]注意: 这是简化回测，仅供参考。完整回测请运行:[/cyan]")
    console.print("[yellow]  python run_backtest.py regenerate[/yellow]\n")


if __name__ == '__main__':
    try:
        run_simple_backtest()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  回测被用户中断[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]❌ 回测失败: {e}[/red]")
        import traceback
        traceback.print_exc()
