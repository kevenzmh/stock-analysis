#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
新策略系统回测框架

特点：
1. 集成新策略系统（stock_strategy.py）
2. 支持多种回测模式
3. 详细的策略分析报告
4. 与现有数据源兼容

作者：AI助手优化版
"""

import os
import sys
import time
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入策略系统
from stock_strategy import (
    TrendFollowingStrategy, 
    MultiFactorStrategy, 
    StrategyManager,
    StockStrategy
)

# 导入用户配置
try:
    import user_config as ucfg
except ImportError:
    print("警告：无法导入user_config.py，使用默认配置")
    ucfg = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('stock_backtest.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataManager:
    """数据管理器"""
    
    def __init__(self):
        self.data_path = self._get_data_path()
        self.cache = {}
    
    def _get_data_path(self) -> str:
        """获取数据路径"""
        if ucfg and hasattr(ucfg, 'tdx') and 'csv_gbbq' in ucfg.tdx:
            return ucfg.tdx['csv_gbbq']
        else:
            # 默认路径
            return "C:/Users/king/tdx/cache/"  # 需要根据实际情况调整
    
    def load_stock_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载股票数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            股票数据DataFrame
        """
        cache_key = f"{stock_code}_{start_date}_{end_date}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 尝试从不同格式加载数据
        file_formats = [
            f"{stock_code}.csv",
            f"{stock_code}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.csv",
            f"{stock_code}_{start_date.replace('-', '')}.csv"
        ]
        
        for filename in file_formats:
            file_path = os.path.join(self.data_path, filename)
            if os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path, encoding='gbk')
                    df['date'] = pd.to_datetime(df['date'])
                    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                    df.set_index('date', inplace=True)
                    
                    # 确保列名标准化
                    df = self._standardize_columns(df)
                    
                    self.cache[cache_key] = df
                    logger.info(f"加载股票数据成功: {stock_code} ({len(df)}条记录)")
                    return df
                    
                except Exception as e:
                    logger.warning(f"加载文件 {filename} 失败: {e}")
                    continue
        
        # 如果没有找到数据文件，生成模拟数据用于测试
        logger.warning(f"未找到股票数据文件 {stock_code}，生成模拟数据")
        df = self._generate_mock_data(stock_code, start_date, end_date)
        self.cache[cache_key] = df
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        column_mapping = {
            '日期': 'date',
            '股票代码': 'code',
            '开盘价': 'open',
            '最高价': 'high', 
            '最低价': 'low',
            '收盘价': 'close',
            '成交量': 'vol',
            '成交额': 'amount',
            '涨跌': 'change',
            '涨跌幅': 'pct_change',
            '换手率': 'turnover_rate',
            '流通市值': '流通市值'
        }
        
        df_renamed = df.copy()
        for old_name, new_name in column_mapping.items():
            if old_name in df_renamed.columns:
                df_renamed.rename(columns={old_name: new_name}, inplace=True)
        
        # 确保基础列存在
        required_cols = ['open', 'high', 'low', 'close', 'vol', 'amount']
        for col in required_cols:
            if col not in df_renamed.columns:
                logger.warning(f"缺少必要列: {col}")
        
        # 添加代码列
        if 'code' not in df_renamed.columns:
            df_renamed['code'] = '000001'  # 默认代码
        
        return df_renamed
    
    def _generate_mock_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟股票数据"""
        dates = pd.date_range(start_date, end_date, freq='B')  # 工作日
        n_days = len(dates)
        
        # 生成模拟价格数据
        np.random.seed(hash(stock_code) % 2**32)  # 基于股票代码生成种子
        base_price = 10 + np.random.random() * 90  # 10-100之间的基础价格
        
        returns = np.random.normal(0.001, 0.025, n_days)  # 日收益率
        price_series = base_price * np.exp(np.cumsum(returns))
        
        # 生成价格范围
        high_price = price_series * (1 + np.random.uniform(0.001, 0.05, n_days))
        low_price = price_series * (1 - np.random.uniform(0.001, 0.05, n_days))
        open_price = np.roll(price_series, 1)
        open_price[0] = price_series[0]
        
        # 生成成交量
        vol = np.random.randint(1000000, 50000000, n_days)
        
        df = pd.DataFrame({
            'date': dates,
            'code': stock_code,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': price_series,
            'vol': vol,
            'amount': price_series * vol,
            'pct_change': returns,
            'change': price_series * returns
        })
        
        df.set_index('date', inplace=True)
        return df
    
    def load_market_data(self, market_symbol: str = "000300", start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        加载市场数据（如沪深300指数）
        
        Args:
            market_symbol: 市场指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            市场数据DataFrame
        """
        if not start_date:
            start_date = "2013-01-01"
        if not end_date:
            end_date = "2022-12-31"
        
        return self.load_stock_data(market_symbol, start_date, end_date)


class StockBacktest:
    """股票策略回测引擎"""
    
    def __init__(self, 
                 initial_capital: float = 10000000,
                 start_date: str = "2013-01-01",
                 end_date: str = "2022-12-31"):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            start_date: 回测开始日期
            end_date: 回测结束日期
        """
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.end_date = end_date
        
        self.data_manager = DataManager()
        self.strategy_manager = StrategyManager()
        self.results = {}
        
        # 回测状态
        self.portfolio_value = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.trade_history = []
        self.daily_returns = []
        
    def add_strategy(self, name: str, strategy: StockStrategy, config: Dict = None):
        """添加策略"""
        if config:
            strategy.config.update(config)
        
        self.strategy_manager.register_strategy(name, strategy)
        logger.info(f"添加策略: {name}")
    
    def run_backtest(self, stock_codes: List[str], strategy_name: str = None) -> Dict:
        """
        运行回测
        
        Args:
            stock_codes: 股票代码列表
            strategy_name: 策略名称（如果为None则运行所有策略）
            
        Returns:
            回测结果
        """
        logger.info(f"开始回测: {stock_codes} | 期间: {self.start_date} ~ {self.end_date}")
        
        # 获取回测日期范围
        trading_dates = pd.date_range(self.start_date, self.end_date, freq='B')
        
        # 如果指定了策略名称，只运行该策略
        strategies_to_run = [strategy_name] if strategy_name else list(self.strategy_manager.strategies.keys())
        
        results = {}
        
        for strategy_name in strategies_to_run:
            logger.info(f"运行策略: {strategy_name}")
            
            # 重置回测状态
            self._reset_portfolio()
            
            strategy_results = {
                'daily_portfolio': [],
                'trades': [],
                'signals': {},
                'performance': {}
            }
            
            for date in trading_dates:
                date_str = date.strftime('%Y-%m-%d')
                daily_result = self._process_daily_trading(date_str, stock_codes, strategy_name)
                
                if daily_result:
                    strategy_results['daily_portfolio'].append(daily_result)
                    
                    # 记录交易
                    if daily_result.get('trades'):
                        strategy_results['trades'].extend(daily_result['trades'])
            
            # 计算性能指标
            strategy_results['performance'] = self._calculate_performance(strategy_results['daily_portfolio'])
            results[strategy_name] = strategy_results
        
        self.results = results
        return results
    
    def _reset_portfolio(self):
        """重置投资组合状态"""
        self.portfolio_value = self.initial_capital
        self.cash = self.initial_capital
        self.positions = {}
        self.trade_history = []
        self.daily_returns = []
    
    def _process_daily_trading(self, date: str, stock_codes: List[str], strategy_name: str) -> Optional[Dict]:
        """处理单日交易"""
        daily_signals = {}
        trades = []
        
        # 获取市场环境
        market_data = self.data_manager.load_market_data("000300", date, date)
        if len(market_data) > 0:
            market_status = {'trend': 'bull', 'condition': 'stable'}  # 简化版市场环境分析
        else:
            market_status = {'trend': 'neutral', 'condition': 'stable'}
        
        # 为每只股票生成信号
        for stock_code in stock_codes:
            try:
                stock_data = self.data_manager.load_stock_data(stock_code, date, date)
                if len(stock_data) == 0:
                    continue
                
                # 获取策略结果
                strategy_result = self.strategy_manager.run_strategy(
                    strategy_name, 
                    stock_data, 
                    market_status=market_status
                )
                
                buy_signals = strategy_result['buy_signals']
                sell_signals = strategy_result['sell_signals']
                
                if buy_signals is not None and len(buy_signals) > 0:
                    daily_signals[stock_code] = {
                        'buy': buy_signals.iloc[-1] if len(buy_signals) > 0 else False,
                        'sell': sell_signals.iloc[-1] if sell_signals is not None and len(sell_signals) > 0 else False,
                        'metadata': strategy_result.get('metadata', {})
                    }
                    
                    # 执行交易
                    current_price = stock_data['close'].iloc[-1]
                    
                    # 买入逻辑
                    if daily_signals[stock_code]['buy'] and stock_code not in self.positions:
                        trade_result = self._execute_buy(stock_code, current_price, date)
                        if trade_result:
                            trades.append(trade_result)
                    
                    # 卖出逻辑
                    elif daily_signals[stock_code]['sell'] and stock_code in self.positions:
                        trade_result = self._execute_sell(stock_code, current_price, date)
                        if trade_result:
                            trades.append(trade_result)
                
            except Exception as e:
                logger.error(f"处理股票 {stock_code} 时出错: {e}")
                continue
        
        # 计算当日投资组合价值
        portfolio_value = self.cash
        for stock_code, position in self.positions.items():
            try:
                stock_data = self.data_manager.load_stock_data(stock_code, date, date)
                if len(stock_data) > 0:
                    current_price = stock_data['close'].iloc[-1]
                    portfolio_value += position['quantity'] * current_price
            except:
                continue
        
        self.portfolio_value = portfolio_value
        
        # 记录当日数据
        daily_return = (portfolio_value / self.initial_capital) - 1
        self.daily_returns.append(daily_return)
        
        return {
            'date': date,
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'positions_count': len(self.positions),
            'signals': daily_signals,
            'trades': trades,
            'daily_return': daily_return
        }
    
    def _execute_buy(self, stock_code: str, price: float, date: str) -> Optional[Dict]:
        """执行买入交易"""
        # 简化版：每次买入固定金额
        buy_amount = min(self.cash * 0.1, 100000)  # 最多买入10万或10%现金
        
        if buy_amount < 1000:  # 最小交易金额
            return None
        
        quantity = int(buy_amount / price)
        total_cost = quantity * price
        
        if total_cost <= self.cash:
            self.cash -= total_cost
            
            if stock_code in self.positions:
                self.positions[stock_code]['quantity'] += quantity
                self.positions[stock_code]['cost'] += total_cost
                self.positions[stock_code]['avg_price'] = self.positions[stock_code]['cost'] / self.positions[stock_code]['quantity']
            else:
                self.positions[stock_code] = {
                    'quantity': quantity,
                    'cost': total_cost,
                    'avg_price': price,
                    'buy_date': date
                }
            
            return {
                'type': 'BUY',
                'stock_code': stock_code,
                'quantity': quantity,
                'price': price,
                'amount': total_cost,
                'date': date
            }
        
        return None
    
    def _execute_sell(self, stock_code: str, price: float, date: str) -> Optional[Dict]:
        """执行卖出交易"""
        if stock_code not in self.positions:
            return None
        
        position = self.positions[stock_code]
        quantity = position['quantity']
        total_proceeds = quantity * price
        
        # 计算收益
        cost = position['cost']
        pnl = total_proceeds - cost
        pnl_pct = (price / position['avg_price']) - 1
        
        # 更新现金和持仓
        self.cash += total_proceeds
        del self.positions[stock_code]
        
        return {
            'type': 'SELL',
            'stock_code': stock_code,
            'quantity': quantity,
            'price': price,
            'amount': total_proceeds,
            'cost': cost,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'date': date
        }
    
    def _calculate_performance(self, daily_portfolio: List[Dict]) -> Dict:
        """计算策略性能指标"""
        if not daily_portfolio:
            return {}
        
        df_portfolio = pd.DataFrame(daily_portfolio)
        df_portfolio['date'] = pd.to_datetime(df_portfolio['date'])
        df_portfolio.set_index('date', inplace=True)
        
        # 计算收益率
        total_return = (df_portfolio['portfolio_value'].iloc[-1] / self.initial_capital) - 1
        
        # 计算年化收益率
        trading_days = len(daily_portfolio)
        years = trading_days / 252  # 假设一年252个交易日
        annualized_return = (1 + total_return) ** (1/years) - 1
        
        # 计算最大回撤
        peak = df_portfolio['portfolio_value'].expanding().max()
        drawdown = (df_portfolio['portfolio_value'] - peak) / peak
        max_drawdown = drawdown.min()
        
        # 计算夏普比率
        returns = df_portfolio['portfolio_value'].pct_change().dropna()
        if returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 计算胜率
        profitable_trades = len([t for t in self.trade_history if t.get('pnl', 0) > 0])
        total_trades = len([t for t in self.trade_history if t.get('type') == 'SELL'])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'final_value': df_portfolio['portfolio_value'].iloc[-1],
            'trading_days': trading_days
        }
    
    def save_results(self, filename: str = None):
        """保存回测结果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_results_{timestamp}.pkl"
        
        filepath = os.path.join("backtest_results", filename)
        
        # 确保目录存在
        os.makedirs("backtest_results", exist_ok=True)
        
        # 保存结果
        with open(filepath, 'wb') as f:
            pickle.dump(self.results, f)
        
        logger.info(f"回测结果已保存: {filepath}")
        
        # 同时保存为CSV格式便于查看
        self._save_csv_summary(filepath.replace('.pkl', '.csv'))
    
    def _save_csv_summary(self, csv_path: str):
        """保存CSV格式的汇总报告"""
        summary_data = []
        
        for strategy_name, result in self.results.items():
            perf = result['performance']
            summary_data.append({
                'strategy': strategy_name,
                'total_return': f"{perf.get('total_return', 0):.2%}",
                'annualized_return': f"{perf.get('annualized_return', 0):.2%}",
                'max_drawdown': f"{perf.get('max_drawdown', 0):.2%}",
                'sharpe_ratio': f"{perf.get('sharpe_ratio', 0):.2f}",
                'win_rate': f"{perf.get('win_rate', 0):.2%}",
                'total_trades': perf.get('total_trades', 0),
                'final_value': f"{perf.get('final_value', 0):,.2f}",
                'trading_days': perf.get('trading_days', 0)
            })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"CSV汇总报告已保存: {csv_path}")


def run_example_backtest():
    """运行示例回测"""
    print("=" * 60)
    print("股票策略系统回测示例")
    print("=" * 60)
    
    # 创建回测引擎
    backtest = StockBacktest(
        initial_capital=10000000,  # 1000万初始资金
        start_date="2020-01-01",
        end_date="2023-12-31"
    )
    
    # 添加策略
    trend_strategy = TrendFollowingStrategy({
        'min_price': 5,
        'volume_ratio_threshold': 1.8,
        'max_holding_days': 15
    })
    
    multi_strategy = MultiFactorStrategy()
    multi_strategy.factor_weights.update({
        'trend': 0.4,
        'momentum': 0.3,
        'volume': 0.3
    })
    
    backtest.add_strategy("趋势跟踪", trend_strategy)
    backtest.add_strategy("多因子策略", multi_strategy)
    
    # 测试股票列表
    test_stocks = ['000001', '000002', '600519', '600036', '000858']
    
    # 运行回测
    results = backtest.run_backtest(test_stocks)
    
    # 显示结果
    print("\n回测结果汇总:")
    print("-" * 60)
    
    for strategy_name, result in results.items():
        perf = result['performance']
        print(f"\n策略: {strategy_name}")
        print(f"  总收益率: {perf.get('total_return', 0):.2%}")
        print(f"  年化收益率: {perf.get('annualized_return', 0):.2%}")
        print(f"  最大回撤: {perf.get('max_drawdown', 0):.2%}")
        print(f"  夏普比率: {perf.get('sharpe_ratio', 0):.2f}")
        print(f"  胜率: {perf.get('win_rate', 0):.2%}")
        print(f"  交易次数: {perf.get('total_trades', 0)}")
        print(f"  最终价值: {perf.get('final_value', 0):,.2f}")
    
    # 保存结果
    backtest.save_results()
    
    print("\n" + "=" * 60)
    print("回测完成！结果已保存到 backtest_results 目录")
    print("=" * 60)


if __name__ == '__main__':
    run_example_backtest()