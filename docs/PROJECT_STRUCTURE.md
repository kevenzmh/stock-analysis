# 项目结构说明

## 📁 完整目录结构

```
stock-analysis/
│
├── 原有文件(保持不变)
│   ├── celue_save.py          # 策略信号保存
│   ├── CeLue模板.py            # 策略模板
│   ├── func.py                 # 通用函数库
│   ├── func_TDX.py            # 通达信函数库
│   ├── huice.py                # 回测脚本
│   ├── plot.py                 # 可视化脚本
│   ├── pytdx_best_ip.py       # 最优IP选择
│   ├── readTDX_cw.py          # 财务数据读取(旧)
│   ├── readTDX_lday.py        # 日线数据读取
│   ├── user_config.py          # 用户配置(旧)
│   ├── xuangu.py               # 选股脚本
│   ├── LICENSE                 # 许可证
│   └── README.md               # 原始说明文档
│
├── 优化模块
│   ├── optimized/              # 优化模块目录 ⭐
│   │   ├── __init__.py         # 模块初始化
│   │   ├── config.py           # 配置管理 ⭐
│   │   ├── logger.py           # 日志管理 ⭐
│   │   ├── downloader.py       # 下载管理 ⭐
│   │   ├── data_reader.py      # 数据读取 ⭐
│   │   └── financial_data.py   # 财务数据管理 ⭐
│   │
│   ├── update_financial_data.py  # 财务数据更新脚本(新) ⭐
│   ├── examples.py               # 使用示例 ⭐
│   ├── config.json               # 配置文件(自动生成)
│   │
│   └── logs/                     # 日志目录(自动生成)
│       └── stock-analysis_YYYYMMDD.log
│
├── 文档
│   ├── OPTIMIZATION_README.md  # 优化说明文档 ⭐
│   ├── QUICKSTART.md           # 快速开始指南 ⭐
│   └── PROJECT_STRUCTURE.md    # 本文档 ⭐
│
└── 数据目录(user_config.py 配置)
    ├── d:/stock/通达信/         # 通达信安装目录
    ├── d:/TDXdata/lday_qfq/    # 前复权日线数据
    ├── d:/TDXdata/pickle/       # Pickle格式数据
    ├── d:/TDXdata/index/        # 指数数据
    ├── d:/TDXdata/cw/           # 财务数据
    └── d:/TDXdata/              # 股本变迁等
```

## 📋 文件说明

### 核心优化模块 (optimized/)

#### 1. `config.py` - 配置管理
**功能**: 统一的配置管理系统
- `Config` 类: 主配置管理器
- `PathConfig`: 路径配置
- `FilterConfig`: 过滤配置
- `load_legacy_config()`: 兼容旧配置

**使用场景**:
- 管理所有路径配置
- 加载/保存配置文件
- 验证配置有效性

#### 2. `logger.py` - 日志管理
**功能**: 统一的日志系统
- `Logger` 类: 日志管理器
- 文件和控制台双输出
- 自动按日期分割

**日志级别**:
- DEBUG: 调试信息
- INFO: 普通信息
- WARNING: 警告信息
- ERROR: 错误信息

#### 3. `downloader.py` - 下载管理
**功能**: 稳定的文件下载
- `Downloader` 类: 下载管理器
- 智能重试机制
- 文件完整性验证
- 进度显示

**主要方法**:
- `download()`: 下载单个文件
- `download_batch()`: 批量下载
- `verify_zip_file()`: ZIP验证
- `calculate_md5()`: MD5计算

#### 4. `data_reader.py` - 数据读取
**功能**: 通达信数据文件读取
- `FinancialDataReader`: 财务数据读取器
- `DayDataReader`: 日线数据读取器
- `DataCache`: 数据缓存管理

**支持格式**:
- `.dat`: 财务数据
- `.day`: 日线数据
- `.csv`: CSV数据
- `.pkl`: Pickle数据

#### 5. `financial_data.py` - 财务数据管理
**功能**: 一站式财务数据管理
- `FinancialDataManager`: 财务数据管理器
- 自动下载缺失文件
- 自动更新过期文件
- 处理股本变迁

**核心流程**:
1. 获取服务器文件列表
2. 检查本地文件
3. 下载缺失/更新文件
4. 解压并转换格式
5. 处理股本变迁

### 优化脚本

#### `update_financial_data.py`
**替代**: `readTDX_cw.py`
**改进**:
- 命令行参数支持
- 详细日志输出
- 更好的错误处理
- 进度实时显示

**命令行参数**:
```bash
--config FILE   # 指定配置文件
--debug         # 调试模式
--skip-gbbq     # 跳过股本变迁
```

#### `examples.py`
**功能**: 交互式示例脚本
**包含示例**:
1. 配置管理
2. 日志系统
3. 文件下载
4. 数据读取
5. 财务数据管理

### 原有脚本(保持兼容)

| 脚本 | 功能 | 状态 |
|------|------|------|
| `readTDX_cw.py` | 财务数据更新 | ✅ 可用 |
| `readTDX_lday.py` | 日线数据更新 | ✅ 可用 |
| `xuangu.py` | 选股 | ✅ 可用 |
| `celue_save.py` | 策略信号保存 | ✅ 可用 |
| `huice.py` | 回测 | ✅ 可用 |
| `plot.py` | 可视化 | ✅ 可用 |

## 🔄 工作流程

### 标准工作流程

```
1. 配置系统
   └─> user_config.py 或 config.json

2. 更新财务数据
   └─> update_financial_data.py (推荐)
   └─> 或 readTDX_cw.py (原版)

3. 更新日线数据
   └─> readTDX_lday.py

4. 执行选股
   └─> xuangu.py

5. 策略回测(可选)
   ├─> celue_save.py (保存信号)
   ├─> huice.py (回测)
   └─> plot.py (可视化)
```

### 优化模块工作流程

```
Config (配置)
   ↓
Logger (日志)
   ↓
Downloader (下载)
   ↓
DataReader (读取)
   ↓
FinancialDataManager (管理)
```

## 📊 数据流向

```
通达信服务器
    ↓ (下载)
ZIP文件 → DAT文件
    ↓ (解压和读取)
DataFrame
    ↓ (保存)
PKL文件 / CSV文件
    ↓ (读取)
策略分析
    ↓
选股结果
```

## 🎯 模块依赖关系

```
update_financial_data.py
    ↓
financial_data.py
    ├─> config.py
    ├─> logger.py
    ├─> downloader.py
    └─> data_reader.py

xuangu.py (原脚本)
    ├─> user_config.py
    ├─> func.py
    ├─> func_TDX.py
    └─> CeLue.py (用户策略)
```

## 🔧 扩展点

### 1. 添加新的数据源
在 `data_reader.py` 中添加新的读取器类

### 2. 添加新的下载策略
在 `downloader.py` 中扩展 `Downloader` 类

### 3. 添加新的策略
创建新的策略文件,参考 `CeLue模板.py`

### 4. 自定义配置
创建自己的 `config.json` 文件

## 📝 使用建议

### 新用户
1. 阅读 `QUICKSTART.md`
2. 运行 `examples.py`
3. 使用 `update_financial_data.py --debug`

### 老用户
1. 继续使用原有脚本
2. 逐步迁移到优化模块
3. 利用新的日志功能

### 开发者
1. 查看 `optimized/` 源代码
2. 扩展现有功能
3. 提交改进建议

## 🚀 性能优化建议

1. **使用Pickle格式**: 比CSV快3-5倍
2. **启用数据缓存**: 减少重复读取
3. **多进程处理**: 充分利用CPU
4. **固态硬盘**: 显著提升I/O性能

## 🔍 调试技巧

1. **开启调试模式**: `--debug`
2. **查看日志文件**: `logs/*.log`
3. **使用示例脚本**: `examples.py`
4. **分步测试**: 单独测试各个模块

## 💻 开发规范

### 代码风格
- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串

### 目录组织
- `optimized/`: 优化模块
- `logs/`: 日志文件
- `docs/`: 文档(可选)

### 命名规范
- 类名: PascalCase
- 函数名: snake_case
- 常量: UPPER_CASE

## 📚 相关文档

- [QUICKSTART.md](QUICKSTART.md) - 快速开始
- [OPTIMIZATION_README.md](OPTIMIZATION_README.md) - 优化说明
- [README.md](README.md) - 原始文档

## 🎓 学习路径

1. 了解项目结构 (本文档)
2. 快速开始 (QUICKSTART.md)
3. 深入了解优化 (OPTIMIZATION_README.md)
4. 运行示例 (examples.py)
5. 阅读源代码 (optimized/)
6. 自定义扩展

---

**提示**: 这个项目结构图可以帮助你快速定位所需功能!
