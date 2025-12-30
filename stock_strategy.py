#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
智能股票选股策略系统 v2.0

特点：
1. 模块化设计，易于扩展
2. 多因子复合筛选
3. 风险控制和仓位管理
4. 支持多种技术指标组合

作者：AI助手优化版
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class StockStrategy:
    """股票策略基类"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化策略
        
        Args:
            config: 策略配置字典
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        
    def check_data_quality(self, df: pd.DataFrame) -> bool:
        """检查数据质量"""
        required_cols = ['open', 'high', 'low', 'close', 'vol', 'amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"数据缺少必要列: {missing_cols}")
            return False
        
        if len(df) < 60:
            logger.warning(f"数据长度不足: {len(df)} < 60")
            return False
        
        # 检查NaN值
        nan_count = df[required_cols].isna().sum().sum()
        if nan_count > 0:
            logger.warning(f"数据包含 {nan_count} 个NaN值")
            
        return True
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = df.copy()
        
        # 价格序列
        C = df['close']
        H = df['high']
        L = df['low']
        V = df['vol']
        
        # 移动平均线
        df['MA5'] = C.rolling(5).mean()
        df['MA10'] = C.rolling(10).mean()
        df['MA20'] = C.rolling(20).mean()
        df['MA60'] = C.rolling(60).mean()
        
        # 指数移动平均线
        df['EMA12'] = C.ewm(span=12, adjust=False).mean()
        df['EMA26'] = C.ewm(span=26, adjust=False).mean()
        df['EMA50'] = C.ewm(span=50, adjust=False).mean()
        
        # 成交量指标
        df['VOL_MA5'] = V.rolling(5).mean()
        df['VOL_MA10'] = V.rolling(10).mean()
        df['VOL_RATIO'] = V / df['VOL_MA5']
        
        # MACD
        df['MACD_DIF'] = df['EMA12'] - df['EMA26']
        df['MACD_DEA'] = df['MACD_DIF'].ewm(span=9, adjust=False).mean()
        df['MACD'] = 2 * (df['MACD_DIF'] - df['MACD_DEA'])
        
        # RSI
        delta = C.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # 布林带
        df['BB_MID'] = C.rolling(20).mean()
        bb_std = C.rolling(20).std()
        df['BB_UPPER'] = df['BB_MID'] + 2 * bb_std
        df['BB_LOWER'] = df['BB_MID'] - 2 * bb_std
        df['BB_POSITION'] = (C - df['BB_LOWER']) / (df['BB_UPPER'] - df['BB_LOWER'])
        
        # 涨跌幅
        df['CHANGE'] = C.pct_change()
        df['CHANGE_5'] = C.pct_change(5)
        df['CHANGE_20'] = C.pct_change(20)
        
        # 波动率
        df['VOLATILITY'] = C.rolling(20).std() / C.rolling(20).mean()
        
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号（子类需实现）"""
        raise NotImplementedError


class TrendFollowingStrategy(StockStrategy):
    """趋势跟踪策略（改进版）"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        
        # 默认配置
        self.default_config = {
            'min_price': 5,  # 最低股价
            'min_amount': 50_000_000,  # 最低成交额
            'max_market_cap': 500_000_000_000,  # 最大市值
            'min_market_cap': 10_000_000_000,  # 最小市值
            'volume_ratio_threshold': 1.5,  # 成交量放大倍数
            'max_up_limit': 0.095,  # 最大涨幅限制（排除涨停）
            'rsi_oversold': 30,  # RSI超卖
            'rsi_overbought': 70,  # RSI超买
            'bb_position_threshold': 0.3,  # 布林带位置阈值
            'min_holding_days': 3,  # 最小持有天数
            'max_holding_days': 20,  # 最大持有天数
        }
        
        # 更新配置
        self.config = {**self.default_config, **self.config}
        
    def market_environment_analysis(self, df_hs300: pd.DataFrame) -> Dict:
        """
        分析市场环境
        
        Returns:
            市场状态字典
        """
        if len(df_hs300) < 60:
            return {'trend': 'unknown', 'condition': 'neutral'}
            
        C = df_hs300['close']
        
        # 计算市场趋势指标
        MA20 = C.rolling(20).mean()
        MA60 = C.rolling(60).mean()
        
        # 趋势判断
        trend_up = C.iloc[-1] > MA20.iloc[-1] > MA60.iloc[-1]
        trend_down = C.iloc[-1] < MA20.iloc[-1] < MA60.iloc[-1]
        
        # 波动率
        volatility = C.rolling(20).std().iloc[-1] / C.rolling(20).mean().iloc[-1]
        
        # 市场状态
        if trend_up and volatility < 0.02:
            return {'trend': 'bull', 'condition': 'stable'}
        elif trend_up and volatility >= 0.02:
            return {'trend': 'bull', 'condition': 'volatile'}
        elif trend_down and volatility < 0.02:
            return {'trend': 'bear', 'condition': 'stable'}
        elif trend_down and volatility >= 0.02:
            return {'trend': 'bear', 'condition': 'volatile'}
        else:
            return {'trend': 'sideways', 'condition': 'neutral'}
    
    def screen_stocks(self, df: pd.DataFrame) -> pd.Series:
        """
        股票筛选（初选）
        
        Returns:
            筛选结果布尔序列
        """
        if not self.check_data_quality(df):
            return pd.Series([False] * len(df), index=df.index)
        
        C = df['close']
        A = df['amount']
        
        # 基础筛选条件
        conditions = []
        
        # 1. 价格条件
        conditions.append(C > self.config['min_price'])
        
        # 2. 成交额条件
        conditions.append(A > self.config['min_amount'])
        
        # 3. 市值条件（如果有）
        if '流通市值' in df.columns:
            market_cap = df['流通市值']
            conditions.append(market_cap.between(
                self.config['min_market_cap'], 
                self.config['max_market_cap']
            ))
        
        # 4. 排除涨跌停
        if 'high_limit' in df.columns and 'low_limit' in df.columns:
            # 如果有涨跌停价列
            conditions.append(C < df['high_limit'] * 0.99)
            conditions.append(C > df['low_limit'] * 1.01)
        else:
            # 估算涨跌停
            prev_close = C.shift(1)
            code = df['code'].iloc[0] if 'code' in df.columns else ''
            
            if code.startswith('688') or code.startswith('300'):
                high_limit = prev_close * 1.2
                low_limit = prev_close * 0.8
            else:
                high_limit = prev_close * 1.1
                low_limit = prev_close * 0.9
            
            conditions.append(C < high_limit * 0.99)
            conditions.append(C > low_limit * 1.01)
        
        # 5. 换手率条件（如果有）
        if 'turnover_rate' in df.columns:
            conditions.append(df['turnover_rate'] > 1.0)
        
        # 组合所有条件
        screened = pd.Series([True] * len(df), index=df.index)
        for condition in conditions:
            screened = screened & condition
            
        return screened
    
    def generate_buy_signals(self, df: pd.DataFrame, market_status: Dict) -> pd.Series:
        """
        生成买入信号
        
        Args:
            df: 股票数据
            market_status: 市场状态
            
        Returns:
            买入信号布尔序列
        """
        df = self.calculate_indicators(df)
        
        # 根据市场状态调整策略
        if market_status['trend'] == 'bear':
            logger.info("熊市环境，减少买入信号")
            # 熊市使用更严格的条件
            volume_ratio_threshold = self.config['volume_ratio_threshold'] * 1.2
            rsi_threshold = 40  # RSI需要更低
        else:
            volume_ratio_threshold = self.config['volume_ratio_threshold']
            rsi_threshold = 30
        
        # 买入条件
        conditions = []
        
        # 条件1: 趋势向上（短期均线在长期均线之上）
        conditions.append(df['MA5'] > df['MA20'])
        conditions.append(df['MA20'] > df['MA60'])
        
        # 条件2: 价格突破重要均线
        conditions.append(df['close'] > df['MA20'])
        conditions.append(df['close'] > df['MA60'])
        
        # 条件3: 成交量放大
        conditions.append(df['VOL_RATIO'] > volume_ratio_threshold)
        
        # 条件4: MACD金叉或向上
        conditions.append(df['MACD_DIF'] > df['MACD_DEA'])
        conditions.append(df['MACD'] > df['MACD'].shift(1))
        
        # 条件5: RSI处于合理区间（不超买）
        conditions.append(df['RSI'] > rsi_threshold)
        conditions.append(df['RSI'] < self.config['rsi_overbought'] - 10)
        
        # 条件6: 布林带位置合理（不在上轨）
        conditions.append(df['BB_POSITION'] < 0.8)
        
        # 条件7: 波动率适中
        conditions.append(df['VOLATILITY'].between(0.01, 0.05))
        
        # 条件8: 近期涨幅适中（不追高）
        conditions.append(df['CHANGE_5'].abs() < 0.15)
        
        # 组合条件
        buy_signal = pd.Series([True] * len(df), index=df.index)
        for condition in conditions:
            buy_signal = buy_signal & condition
        
        # 确保是突破信号（价格创新高或突破关键位）
        price_break = (df['close'] > df['close'].rolling(20).max().shift(1))
        ma_break = (df['close'] > df['MA20'].shift(1)) & (df['close'].shift(1) <= df['MA20'].shift(1))
        
        buy_signal = buy_signal & (price_break | ma_break)
        
        return buy_signal
    
    def generate_sell_signals(self, df: pd.DataFrame, buy_signals: pd.Series) -> pd.Series:
        """
        生成卖出信号
        
        Args:
            df: 股票数据
            buy_signals: 买入信号
            
        Returns:
            卖出信号布尔序列
        """
        df = self.calculate_indicators(df)
        
        sell_conditions = []
        
        # 止损条件
        # 1. 价格跌破重要均线
        sell_conditions.append(df['close'] < df['MA10'])
        
        # 2. 价格跌破买入价的止损位
        buy_prices = self._calculate_buy_prices(df, buy_signals)
        stop_loss = buy_prices * 0.95  # 5%止损
        sell_conditions.append(df['close'] < stop_loss)
        
        # 止盈条件
        # 3. 盈利超过目标
        profit_target = buy_prices * 1.15  # 15%止盈
        sell_conditions.append(df['close'] > profit_target)
        
        # 4. RSI超买
        sell_conditions.append(df['RSI'] > self.config['rsi_overbought'])
        
        # 5. 布林带上轨
        sell_conditions.append(df['BB_POSITION'] > 0.95)
        
        # 6. 成交量萎缩（跌破均量线）
        sell_conditions.append(df['vol'] < df['VOL_MA5'] * 0.7)
        
        # 7. 持有时间过长（时间止损）
        hold_days = self._calculate_hold_days(buy_signals)
        sell_conditions.append(hold_days > self.config['max_holding_days'])
        
        # 组合卖出条件
        sell_signal = pd.Series([False] * len(df), index=df.index)
        for condition in sell_conditions:
            sell_signal = sell_signal | condition
        
        # 确保卖出信号在买入之后
        sell_signal = sell_signal & self._calculate_position_status(buy_signals, sell_signal)
        
        return sell_signal
    
    def _calculate_buy_prices(self, df: pd.DataFrame, buy_signals: pd.Series) -> pd.Series:
        """计算买入价格序列"""
        buy_prices = pd.Series(np.nan, index=df.index)
        
        for i in range(len(df)):
            if buy_signals.iloc[i]:
                buy_prices.iloc[i] = df['close'].iloc[i]
        
        # 向前填充买入价格
        buy_prices = buy_prices.ffill()
        
        return buy_prices
    
    def _calculate_hold_days(self, buy_signals: pd.Series) -> pd.Series:
        """计算持有天数"""
        hold_days = pd.Series(0, index=buy_signals.index)
        
        current_hold = 0
        for i in range(len(buy_signals)):
            if buy_signals.iloc[i]:
                current_hold = 0
            else:
                current_hold += 1
            hold_days.iloc[i] = current_hold
        
        return hold_days
    
    def _calculate_position_status(self, buy_signals: pd.Series, sell_signals: pd.Series) -> pd.Series:
        """计算持仓状态"""
        position = pd.Series(False, index=buy_signals.index)
        in_position = False
        
        for i in range(len(buy_signals)):
            if buy_signals.iloc[i] and not in_position:
                in_position = True
            elif sell_signals.iloc[i] and in_position:
                in_position = False
            
            position.iloc[i] = in_position
        
        return position


class MultiFactorStrategy(StockStrategy):
    """多因子综合策略"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        
        # 因子权重配置
        self.factor_weights = {
            'trend': 0.3,      # 趋势因子
            'momentum': 0.25,  # 动量因子
            'volume': 0.2,     # 成交量因子
            'volatility': 0.15,# 波动率因子
            'value': 0.1,      # 价值因子（如果有）
        }
    
    def calculate_factors(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """计算各种因子"""
        df = self.calculate_indicators(df)
        
        factors = {}
        
        # 1. 趋势因子
        trend_strength = (
            (df['MA5'] > df['MA20']).astype(int) * 0.3 +
            (df['MA20'] > df['MA60']).astype(int) * 0.4 +
            (df['close'] > df['MA60']).astype(int) * 0.3
        )
        factors['trend'] = trend_strength
        
        # 2. 动量因子
        momentum_1m = df['close'].pct_change(20)  # 20日动量
        momentum_1w = df['close'].pct_change(5)   # 5日动量
        factors['momentum'] = momentum_1m * 0.6 + momentum_1w * 0.4
        
        # 3. 成交量因子
        volume_ratio = df['VOL_RATIO']
        volume_trend = (df['vol'] > df['VOL_MA10']).astype(int)
        factors['volume'] = volume_ratio * 0.7 + volume_trend * 0.3
        
        # 4. 波动率因子（低波动为好）
        volatility = df['VOLATILITY']
        # 标准化并反转，使得低波动得分高
        factors['volatility'] = 1 - (volatility / volatility.max())
        
        # 5. 价值因子（如果有估值数据）
        if 'pe_ratio' in df.columns:
            pe = df['pe_ratio']
            # 排除异常值，PE在10-30之间为佳
            pe_score = pd.Series(0, index=df.index)
            pe_score[(pe > 10) & (pe < 30)] = 1
            pe_score[(pe > 5) & (pe < 10)] = 0.8
            pe_score[(pe > 30) & (pe < 50)] = 0.5
            factors['value'] = pe_score
        else:
            factors['value'] = pd.Series(0.5, index=df.index)
        
        return factors
    
    def generate_signals(self, df: pd.DataFrame, threshold: float = 0.7) -> pd.Series:
        """生成综合信号"""
        # 先确保技术指标已计算
        df = self.calculate_indicators(df)
        
        factors = self.calculate_factors(df)
        
        # 计算综合得分
        total_score = pd.Series(0, index=df.index)
        for factor_name, weight in self.factor_weights.items():
            factor_score = factors[factor_name]
            # 标准化到0-1之间
            if factor_score.max() > factor_score.min():
                factor_score_norm = (factor_score - factor_score.min()) / (factor_score.max() - factor_score.min())
            else:
                factor_score_norm = factor_score
                
            total_score += factor_score_norm * weight
        
        # 生成买入信号（得分高于阈值）
        buy_signal = total_score > threshold
        
        # 添加额外条件
        # 1. 成交量放大
        volume_condition = df['vol'] > df['VOL_MA5'] * 1.2
        
        # 2. 价格在均线之上  
        price_condition = (df['close'] > df['MA20']) & (df['close'] > df['MA60'])
        
        # 3. RSI合理
        if 'RSI' in df.columns:
            rsi_condition = (df['RSI'] > 40) & (df['RSI'] < 80)
        else:
            rsi_condition = pd.Series(True, index=df.index)
        
        buy_signal = buy_signal & volume_condition & price_condition & rsi_condition
        
        return buy_signal


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self.strategies = {}
        self.results = {}
        
    def register_strategy(self, name: str, strategy: StockStrategy):
        """注册策略"""
        self.strategies[name] = strategy
        logger.info(f"注册策略: {name}")
        
    def run_strategy(self, name: str, df: pd.DataFrame, **kwargs) -> Dict:
        """运行单个策略"""
        if name not in self.strategies:
            raise ValueError(f"策略 '{name}' 未注册")
        
        strategy = self.strategies[name]
        results = {
            'buy_signals': None,
            'sell_signals': None,
            'scores': None,
            'metadata': {}
        }
        
        try:
            if hasattr(strategy, 'generate_buy_signals'):
                # 趋势跟踪策略
                market_status = kwargs.get('market_status', {'trend': 'neutral', 'condition': 'stable'})
                buy_signals = strategy.generate_buy_signals(df, market_status)
                sell_signals = strategy.generate_sell_signals(df, buy_signals)
                
                results['buy_signals'] = buy_signals
                results['sell_signals'] = sell_signals
                
                # 计算信号统计
                buy_count = buy_signals.sum()
                sell_count = sell_signals.sum()
                
                results['metadata'] = {
                    'buy_signals_count': int(buy_count),
                    'sell_signals_count': int(sell_count),
                    'last_signal': 'BUY' if buy_signals.iloc[-1] else ('SELL' if sell_signals.iloc[-1] else 'HOLD')
                }
            else:
                # 多因子策略
                buy_signals = strategy.generate_signals(df)
                results['buy_signals'] = buy_signals
                results['metadata'] = {
                    'buy_signals_count': int(buy_signals.sum())
                }
                
        except Exception as e:
            logger.error(f"策略 {name} 执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        self.results[name] = results
        return results
    
    def run_all(self, df: pd.DataFrame, **kwargs) -> Dict:
        """运行所有策略"""
        all_results = {}
        
        for name in self.strategies:
            logger.info(f"执行策略: {name}")
            results = self.run_strategy(name, df, **kwargs)
            all_results[name] = results
            
        return all_results


# 使用示例
if __name__ == '__main__':
    print("="*60)
    print("股票策略系统测试")
    print("="*60)
    
    # 创建策略管理器
    manager = StrategyManager()
    
    # 注册策略
    trend_strategy = TrendFollowingStrategy()
    multi_factor_strategy = MultiFactorStrategy()
    
    manager.register_strategy('趋势跟踪', trend_strategy)
    manager.register_strategy('多因子', multi_factor_strategy)
    
    # 模拟数据（实际使用时替换为真实数据）
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='B')
    np.random.seed(42)
    
    # 生成模拟股票数据
    n_days = len(dates)
    base_price = 100
    returns = np.random.normal(0.0005, 0.02, n_days)
    price = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'date': dates,
        'open': price * 0.99,
        'high': price * 1.02,
        'low': price * 0.98,
        'close': price,
        'vol': np.random.randint(1000000, 10000000, n_days),
        'amount': price * np.random.randint(1000000, 10000000, n_days),
        'code': '000001'
    })
    df.set_index('date', inplace=True)
    
    # 模拟市场状态
    market_status = {'trend': 'bull', 'condition': 'stable'}
    
    # 运行策略
    print("\n运行趋势跟踪策略...")
    results = manager.run_strategy('趋势跟踪', df, market_status=market_status)
    
    if results['buy_signals'] is not None:
        buy_count = results['buy_signals'].sum()
        print(f"  买入信号数量: {buy_count}")
        print(f"  最后一天信号: {results['metadata']['last_signal']}")
    
    print("\n运行多因子策略...")
    results2 = manager.run_strategy('多因子', df)
    
    if results2['buy_signals'] is not None:
        buy_count2 = results2['buy_signals'].sum()
        print(f"  买入信号数量: {buy_count2}")
    
    print("\n" + "="*60)
    print("策略测试完成")
    print("="*60)
    
    # 保存策略配置
    import json
    
    config = {
        'trend_strategy': trend_strategy.config,
        'multi_factor_weights': multi_factor_strategy.factor_weights
    }
    
    with open('strategy_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("\n策略配置已保存到: strategy_config.json")