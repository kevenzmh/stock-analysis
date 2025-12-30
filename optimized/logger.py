#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志管理模块 - 优化版
提供统一的日志管理功能

作者: 优化版 2024
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """日志管理类"""
    
    def __init__(self, name: str = "stock-analysis", 
                 log_dir: str = "logs",
                 level: int = logging.INFO):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            level: 日志级别
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if self.logger.handlers:
            return
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, msg: str):
        """调试日志"""
        self.logger.debug(msg)
    
    def info(self, msg: str):
        """信息日志"""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """警告日志"""
        self.logger.warning(msg)
    
    def error(self, msg: str):
        """错误日志"""
        self.logger.error(msg)
    
    def exception(self, msg: str):
        """异常日志(带堆栈信息)"""
        self.logger.exception(msg)


# 全局日志器实例
_default_logger: Optional[Logger] = None


def get_logger(name: str = "stock-analysis") -> Logger:
    """
    获取日志器实例
    
    Args:
        name: 日志器名称
        
    Returns:
        Logger实例
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = Logger(name)
    return _default_logger


def set_log_level(level: int):
    """设置日志级别"""
    logger = get_logger()
    logger.logger.setLevel(level)


if __name__ == '__main__':
    # 测试日志功能
    logger = get_logger()
    
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    
    try:
        1 / 0
    except Exception as e:
        logger.exception("捕获到异常")
