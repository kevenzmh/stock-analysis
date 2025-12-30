# 股票策略回测系统使用指南

## 概述

本项目包含两套完整的股票策略回测系统：

1. **原有回测框架** (`huice.py`) - 基于 rqalpha 的专业回测引擎
2. **新策略回测系统** (`stock_backtest.py`) - 基于新策略系统的回测框架

## 系统架构

### 新策略系统结构

```
stock_strategy.py
├── StockStrategy (基类)
│   ├── 数据质量检查
│   ├── 技术指标计算
│   └── 信号生成框架
├── TrendFollowingStrategy (趋势跟踪策略)
│   ├── 市场环境分析
│   ├── 股票筛选
│   ├── 买入信号生成
│   └── 卖出信号生成
├── MultiFactorStrategy (多因子策略)
│   ├── 因子计算
│   ├── 权重配置
│   └── 综合评分
└── StrategyManager (策略管理器)
    ├── 策略注册
    ├── 策略执行
    └── 结果管理
```

### 回测框架结构

```
stock_backtest.py
├── DataManager (数据管理器)
│   ├── 股票数据加载
│   ├── 市场数据获取
│   └── 数据标准化
├── StockBacktest (回测引擎)
│   ├── 策略管理
│   ├── 交易执行
│   ├── 性能计算
│   └── 结果输出
└── 运行示例
```

## 快速开始

### 1. 基础使用

```python
from stock_backtest import StockBacktest, TrendFollowingStrategy, MultiFactorStrategy

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

backtest.add_strategy("趋势跟踪", trend_strategy)

# 运行回测
stock_codes = ['000001', '000002', '600519', '600036', '000858']
results = backtest.run_backtest(stock_codes)

# 保存结果
backtest.save_results()
```

### 2. 高级配置

```python
# 多因子策略配置
multi_strategy = MultiFactorStrategy()
multi_strategy.factor_weights.update({
    'trend': 0.4,      # 趋势因子权重
    'momentum': 0.3,   # 动量因子权重
    'volume': 0.2,     # 成交量因子权重
    'volatility': 0.1  # 波动率因子权重
})

# 趋势跟踪策略详细配置
trend_config = {
    'min_price': 5,                    # 最低股价
    'min_amount': 50_000_000,         # 最低成交额
    'max_market_cap': 500_000_000_000, # 最大市值
    'min_market_cap': 10_000_000_000,  # 最小市值
    'volume_ratio_threshold': 1.5,     # 成交量放大倍数
    'max_up_limit': 0.095,            # 最大涨幅限制
    'rsi_oversold': 30,               # RSI超卖阈值
    'rsi_overbought': 70,             # RSI超买阈值
    'bb_position_threshold': 0.3,     # 布林带位置阈值
    'min_holding_days': 3,            # 最小持有天数
    'max_holding_days': 20            # 最大持有天数
}

trend_strategy = TrendFollowingStrategy(trend_config)
```

## 策略详解

### 趋势跟踪策略

**核心逻辑：**
1. 市场环境分析 - 判断当前市场趋势状态
2. 股票筛选 - 基于价格、成交额、市值等基础条件
3. 买入信号 - 多重技术指标确认
4. 卖出信号 - 止损止盈和时间控制

**技术指标组合：**
- 移动平均线：MA5, MA10, MA20, MA60
- MACD：dif, dea, macd
- RSI：相对强弱指标
- 布林带：价格位置和带宽
- 成交量：量比和移动均量

**信号条件：**
```
买入信号 = (均线多头排列) AND (价格突破) AND (成交量放大) AND 
          (MACD向上) AND (RSI合理) AND (布林带位置适中) AND 
          (波动率正常) AND (涨幅适中)
```

### 多因子策略

**因子体系：**
1. **趋势因子** (30%): 均线排列和价格位置
2. **动量因子** (25%): 短期和中期动量
3. **成交量因子** (20%): 成交量放大和趋势
4. **波动率因子** (15%): 低波动偏好
5. **价值因子** (10%): PE估值（如果有数据）

**综合评分：**
```python
total_score = trend_factor * 0.3 + momentum_factor * 0.25 + 
              volume_factor * 0.2 + volatility_factor * 0.15 + 
              value_factor * 0.1

buy_signal = total_score > threshold
```

## 回测结果分析

### 性能指标

| 指标 | 说明 | 计算方法 |
|------|------|----------|
| 总收益率 | 期间总收益 | (最终价值/初始资金) - 1 |
| 年化收益率 | 按年计算的收益率 | (1+总收益率)^(1/年数) - 1 |
| 最大回撤 | 最大跌幅 | min((当前价值-历史峰值)/历史峰值) |
| 夏普比率 | 风险调整后收益 | (平均收益/收益标准差) * √252 |
| 胜率 | 盈利交易占比 | 盈利交易数/总交易数 |

### 结果文件

运行回测后会在 `backtest_results/` 目录下生成：

1. **PKL文件**: 完整回测结果（包含所有详细数据）
2. **CSV文件**: 策略性能汇总表
3. **日志文件**: 运行日志记录

```python
# 加载回测结果
import pickle
with open('backtest_results/backtest_results_20241230_143022.pkl', 'rb') as f:
    results = pickle.load(f)

# 查看策略性能
for strategy_name, result in results.items():
    performance = result['performance']
    print(f"策略: {strategy_name}")
    print(f"总收益率: {performance['total_return']:.2%}")
    print(f"年化收益率: {performance['annualized_return']:.2%}")
    print(f"最大回撤: {performance['max_drawdown']:.2%}")
    print(f"夏普比率: {performance['sharpe_ratio']:.2f}")
```

## 与原有系统对比

| 特性 | 新策略系统 | 原有huice.py |
|------|------------|--------------|
| 数据源 | 支持多种格式，自动回退 | 依赖特定格式 |
| 策略管理 | 模块化，易扩展 | 硬编码策略 |
| 技术指标 | 内置完整指标库 | 需要单独计算 |
| 风险控制 | 多重止损止盈 | 基础止损 |
| 结果分析 | 详细性能指标 | 基本收益统计 |
| 使用复杂度 | 简单易用 | 需要理解rqalpha |

## 最佳实践

### 1. 策略选择建议

**牛市环境：**
```python
market_config = {'trend': 'bull', 'condition': 'stable'}
trend_strategy = TrendFollowingStrategy({
    'volume_ratio_threshold': 1.5,  # 降低阈值
    'rsi_overbought': 75,          # 提高超买线
    'max_holding_days': 25         # 延长持有
})
```

**熊市环境：**
```python
trend_strategy = TrendFollowingStrategy({
    'volume_ratio_threshold': 2.0,  # 提高阈值
    'rsi_overbought': 65,          # 降低超买线
    'max_holding_days': 10         # 缩短持有
})
```

### 2. 风险管理

```python
# 设置严格的止损止盈
trend_strategy.config.update({
    'stop_loss_pct': 0.05,    # 5%止损
    'take_profit_pct': 0.15,  # 15%止盈
    'max_position_pct': 0.2   # 单股最大仓位20%
})
```

### 3. 参数优化

```python
# 网格搜索最佳参数
param_grid = {
    'volume_ratio_threshold': [1.2, 1.5, 1.8, 2.0],
    'rsi_overbought': [65, 70, 75],
    'max_holding_days': [10, 15, 20, 25]
}

best_params = None
best_sharpe = -999

for params in param_grid:
    strategy = TrendFollowingStrategy(params)
    # 运行回测并计算夏普比率
    # ...
```

## 常见问题

### Q1: 数据文件不存在怎么办？
**A**: 系统会自动生成模拟数据进行测试。实际使用时，请确保：
- 数据文件格式正确（包含日期、开盘价、最高价、最低价、收盘价、成交量、成交额）
- 文件路径配置正确
- 日期范围覆盖回测期间

### Q2: 策略信号过于频繁？
**A**: 调整策略参数：
```python
# 降低信号频率
trend_strategy.config.update({
    'volume_ratio_threshold': 2.0,  # 提高量比阈值
    'rsi_oversold': 40,            # 提高超卖线
    'min_holding_days': 5          # 增加最小持有天数
})
```

### Q3: 如何添加新的技术指标？
**A**: 继承 `StockStrategy` 类，重写 `calculate_indicators` 方法：
```python
class CustomStrategy(StockStrategy):
    def calculate_indicators(self, df):
        df = super().calculate_indicators(df)
        # 添加自定义指标
        df['CUSTOM_INDICATOR'] = your_calculation(df)
        return df
```

### Q4: 回测结果如何解读？
**A**: 关注关键指标：
- **年化收益率**: > 15% 为优秀
- **最大回撤**: < 20% 为良好
- **夏普比率**: > 1.0 为良好
- **胜率**: > 60% 为稳定

## 扩展开发

### 添加新策略

```python
class MomentumStrategy(StockStrategy):
    def __init__(self, config=None):
        super().__init__(config)
        self.momentum_periods = config.get('momentum_periods', [5, 10, 20])
    
    def generate_buy_signals(self, df, market_status):
        df = self.calculate_indicators(df)
        
        # 计算多周期动量
        momentum_scores = []
        for period in self.momentum_periods:
            momentum = df['close'].pct_change(period)
            momentum_scores.append(momentum > 0)
        
        # 综合动量信号
        buy_signal = pd.Series(False, index=df.index)
        for score in momentum_scores:
            buy_signal = buy_signal | score
        
        return buy_signal
```

### 自定义数据源

```python
class CustomDataManager(DataManager):
    def load_stock_data(self, stock_code, start_date, end_date):
        # 实现自定义数据加载逻辑
        # 可以从API、数据库等源获取数据
        pass
```

## 联系与支持

如有技术问题，请：
1. 查看日志文件 `stock_backtest.log`
2. 检查数据文件格式和路径
3. 验证策略参数配置
4. 参考示例代码进行调整

祝您投资顺利！