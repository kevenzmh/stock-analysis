#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
简易回测脚本 - Windows兼容版
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# 导入策略
import CeLue
try:
    import CeLue_improved
    USE_IMPROVED = True
except ImportError:
    USE_IMPROVED = False

import user_config as ucfg

# 回测参数
START_DATE = '2023-01-01'
END_DATE = '2025-01-20'
INITIAL_CAPITAL = 1000000
POSITION_SIZE = 100000

class SimpleBacktest:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.positions = {}
        self.trades = []
        
    def buy(self, code, price, date):
        if self.cash < POSITION_SIZE:
            return False
        shares = int(POSITION_SIZE / price / 100) * 100
        if shares == 0:
            return False
        cost = shares * price * 1.0003
        if cost > self.cash:
            return False
        self.cash -= cost
        self.positions[code] = {'shares': shares, 'cost': price, 'buy_date': date}
        self.trades.append(('BUY', date, code, price, shares))
        return True
    
    def sell(self, code, price, date):
        if code not in self.positions:
            return False
        pos = self.positions[code]
        revenue = pos['shares'] * price * 0.9987
        profit = revenue - (pos['shares'] * pos['cost'] * 1.0003)
        profit_rate = (price / pos['cost'] - 1) * 100
        self.cash += revenue
        hold_days = (pd.to_datetime(date) - pd.to_datetime(pos['buy_date'])).days
        self.trades.append(('SELL', date, code, price, profit, profit_rate, hold_days))
        del self.positions[code]
        return True
    
    def get_value(self, prices):
        pos_value = sum(pos['shares'] * prices.get(code, pos['cost']) 
                       for code, pos in self.positions.items())
        return self.cash + pos_value

def main():
    print("\n" + "=" * 70)
    print("策略回测演示")
    print("=" * 70)
    
    status = "改进版" if USE_IMPROVED else "原始版"
    print(f"\n策略: {status}")
    print(f"期间: {START_DATE} - {END_DATE}")
    print(f"本金: {INITIAL_CAPITAL:,} 元")
    
    # 测试股票
    test_stocks = ['000001', '600036', '000002', '600519', '000858']
    print(f"\n测试股票: {', '.join(test_stocks)}")
    print("(完整回测会测试4000+只股票)\n")
    
    # 加载HS300
    print("[1/4] 加载沪深300...")
    df_hs300 = pd.read_csv(ucfg.tdx['csv_index'] + '/000300.csv',
                           encoding='gbk', dtype={'code': str})
    df_hs300['date'] = pd.to_datetime(df_hs300['date'])
    df_hs300.set_index('date', drop=False, inplace=True)
    HS300_信号 = CeLue.策略HS300(df_hs300)
    print("完成\n")
    
    # 加载股票
    print("[2/4] 加载股票数据...")
    stock_data = {}
    for i, code in enumerate(test_stocks, 1):
        try:
            print(f"  [{i}/{len(test_stocks)}] {code}...", end='')
            pkl_file = ucfg.tdx['pickle'] + os.sep + code + '.pkl'
            if os.path.exists(pkl_file):
                df = pd.read_pickle(pkl_file)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', drop=False, inplace=True)
                df = df.loc[START_DATE:END_DATE]
                buy = CeLue.策略2(df, HS300_信号)
                sell = CeLue.卖策略(df, buy)
                df['buy'] = buy
                df['sell'] = sell
                stock_data[code] = df
                print(" OK")
            else:
                print(" 文件不存在")
        except Exception as e:
            print(f" 错误: {str(e)[:30]}")
    
    print(f"\n成功加载 {len(stock_data)} 只\n")
    
    if not stock_data:
        print("无可用数据")
        return
    
    # 回测
    print("[3/4] 运行回测...")
    bt = SimpleBacktest()
    all_dates = sorted(set().union(*[set(df.index) for df in stock_data.values()]))
    history = []
    
    for i, date in enumerate(all_dates[:500]):  # 限制500天
        if i % 100 == 0:
            print(f"  处理第 {i} 天...")
        
        date_str = date.strftime('%Y-%m-%d')
        prices = {c: stock_data[c].loc[date, 'close'] 
                 for c in stock_data if date in stock_data[c].index}
        
        # 卖出
        for code in list(bt.positions.keys()):
            if code in stock_data and date in stock_data[code].index:
                if stock_data[code].loc[date, 'sell']:
                    bt.sell(code, stock_data[code].loc[date, 'close'], date_str)
        
        # 买入
        for code in stock_data:
            if code not in bt.positions and date in stock_data[code].index:
                if stock_data[code].loc[date, 'buy']:
                    bt.buy(code, stock_data[code].loc[date, 'close'], date_str)
        
        history.append((date, bt.get_value(prices)))
    
    print("完成\n")
    
    # 计算指标
    print("[4/4] 计算指标...")
    df_hist = pd.DataFrame(history, columns=['date', 'value'])
    
    total_ret = (df_hist['value'].iloc[-1] / INITIAL_CAPITAL - 1) * 100
    days = (df_hist['date'].iloc[-1] - df_hist['date'].iloc[0]).days
    annual_ret = (((df_hist['value'].iloc[-1] / INITIAL_CAPITAL) ** (365 / days)) - 1) * 100
    
    # 最大回撤
    df_hist['cummax'] = df_hist['value'].cummax()
    df_hist['dd'] = (df_hist['value'] / df_hist['cummax'] - 1) * 100
    max_dd = df_hist['dd'].min()
    
    # HS300
    hs300_df = df_hs300.loc[START_DATE:END_DATE]
    hs300_ret = (hs300_df.iloc[-1]['close'] / hs300_df.iloc[0]['close'] - 1) * 100
    
    # 交易
    sells = [t for t in bt.trades if t[0] == 'SELL']
    wins = [t for t in sells if t[4] > 0]
    win_rate = (len(wins) / len(sells) * 100) if sells else 0
    avg_profit = sum(t[5] for t in sells) / len(sells) if sells else 0
    
    print("完成\n")
    
    # 显示结果
    print("=" * 70)
    print("回测结果")
    print("=" * 70)
    print(f"\n总收益率:    {total_ret:+7.2f}%")
    print(f"年化收益:    {annual_ret:+7.2f}%")
    print(f"沪深300:     {hs300_ret:+7.2f}%")
    print(f"超额收益:    {total_ret - hs300_ret:+7.2f}%  ({'跑赢' if total_ret > hs300_ret else '跑输'})")
    print(f"最大回撤:    {max_dd:7.2f}%")
    
    print(f"\n交易次数:    {len(bt.trades)}")
    print(f"卖出次数:    {len(sells)}")
    print(f"胜率:        {win_rate:7.1f}%")
    print(f"平均收益:    {avg_profit:+7.2f}%")
    
    print("\n" + "=" * 70)
    
    # 评价
    print("\n分析:")
    if total_ret > 30 and max_dd > -25:
        print("  + 策略表现优秀")
    elif total_ret > 15:
        print("  + 策略表现良好")
    else:
        print("  - 策略表现一般")
    
    if total_ret > hs300_ret:
        print(f"  + 跑赢基准 {total_ret - hs300_ret:.1f}%")
    else:
        print(f"  - 跑输基准 {hs300_ret - total_ret:.1f}%")
    
    if win_rate > 50:
        print(f"  + 胜率良好 ({win_rate:.1f}%)")
    else:
        print(f"  - 胜率偏低 ({win_rate:.1f}%)")
    
    print("\n注意: 这是简化回测,仅供参考")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n回测中断\n")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
