#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化模块初始化文件

导出主要的类和函数供外部使用
"""

from .config import Config, load_legacy_config
from .logger import Logger, get_logger, set_log_level
from .downloader import Downloader, download_with_progress, verify_zip_file
from .data_reader import (
    FinancialDataReader,
    DayDataReader,
    DataCache
)
from .financial_data import FinancialDataManager

__version__ = '2.0.0'
__author__ = 'wking (原作者), 优化 2024'

__all__ = [
    # 配置管理
    'Config',
    'load_legacy_config',
    
    # 日志管理
    'Logger',
    'get_logger',
    'set_log_level',
    
    # 下载管理
    'Downloader',
    'download_with_progress',
    'verify_zip_file',
    
    # 数据读取
    'FinancialDataReader',
    'DayDataReader',
    'DataCache',
    
    # 财务数据管理
    'FinancialDataManager',
]
