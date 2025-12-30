#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据读取模块 - 优化版
提供通达信数据文件的读取功能

作者: wking (原作者)
优化: 2024
"""

import struct
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from .logger import get_logger

logger = get_logger()


class FinancialDataReader:
    """财务数据读取器"""
    
    @staticmethod
    def read_financial_data(file_path: str) -> pd.DataFrame:
        """
        读取通达信财务数据文件
        
        Args:
            file_path: DAT文件路径
            
        Returns:
            DataFrame格式的财务数据
        """
        try:
            with open(file_path, 'rb') as f:
                # 读取文件头
                header_format = '<1hI1H3L'
                header_size = struct.calcsize(header_format)
                header_data = f.read(header_size)
                header = struct.unpack(header_format, header_data)
                
                max_count = header[2]  # 股票数量
                report_date = header[1]  # 报告日期
                report_size = header[4]  # 报告大小
                report_fields_count = int(report_size / 4)
                
                # 读取股票数据
                stock_item_size = struct.calcsize("<6s1c1L")
                report_format = f'<{report_fields_count}f'
                
                results = []
                for stock_idx in range(max_count):
                    # 读取股票代码信息
                    f.seek(header_size + stock_idx * stock_item_size)
                    stock_item_data = f.read(stock_item_size)
                    stock_item = struct.unpack("<6s1c1L", stock_item_data)
                    
                    code = stock_item[0].decode("utf-8").strip()
                    data_offset = stock_item[2]
                    
                    # 读取财务数据
                    f.seek(data_offset)
                    info_data = f.read(struct.calcsize(report_format))
                    
                    if len(info_data) == struct.calcsize(report_format):
                        fin_data = list(struct.unpack(report_format, info_data))
                        fin_data.insert(0, code)
                        results.append(fin_data)
                
                df = pd.DataFrame(results)
                logger.debug(f"读取财务数据: {len(df)} 条记录")
                return df
                
        except Exception as e:
            logger.exception(f"读取财务数据失败: {e}")
            raise


class DayDataReader:
    """日线数据读取器"""
    
    @staticmethod
    def read_day_data(file_path: str) -> pd.DataFrame:
        """
        读取通达信日线数据文件(.day)
        
        Args:
            file_path: DAY文件路径
            
        Returns:
            DataFrame格式的日线数据
        """
        try:
            path = Path(file_path)
            stock_code = path.stem[2:]  # 去掉sh/sz前缀
            
            # 读取二进制数据
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # 每条记录32字节
            record_size = 32
            num_records = len(data) // record_size
            
            results = []
            for i in range(num_records):
                offset = i * record_size
                record = struct.unpack('IIIIIfII', data[offset:offset + record_size])
                
                # 解析数据
                date_int = record[0]
                date_str = f"{date_int//10000:04d}-{(date_int//100)%100:02d}-{date_int%100:02d}"
                
                results.append({
                    'date': date_str,
                    'code': stock_code,
                    'open': record[1] / 100.0,
                    'high': record[2] / 100.0,
                    'low': record[3] / 100.0,
                    'close': record[4] / 100.0,
                    'vol': record[6],
                    'amount': float(record[5]),
                })
            
            df = pd.DataFrame(results)
            logger.debug(f"读取日线数据: {stock_code}, {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.exception(f"读取日线数据失败: {e}")
            raise
    
    @staticmethod
    def batch_read_day_data(file_paths: list, 
                           progress_callback=None) -> dict:
        """
        批量读取日线数据
        
        Args:
            file_paths: 文件路径列表
            progress_callback: 进度回调函数
            
        Returns:
            {stock_code: DataFrame} 字典
        """
        results = {}
        
        for i, file_path in enumerate(file_paths):
            try:
                df = DayDataReader.read_day_data(file_path)
                stock_code = Path(file_path).stem[2:]
                results[stock_code] = df
                
                if progress_callback:
                    progress_callback(i + 1, len(file_paths))
                    
            except Exception as e:
                logger.error(f"读取失败: {file_path}, {e}")
                continue
        
        return results


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, max_size: int = 1000):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
        """
        self.max_size = max_size
        self.cache = {}
        self.access_count = {}
    
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            DataFrame或None
        """
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key].copy()
        return None
    
    def put(self, key: str, data: pd.DataFrame):
        """
        存入缓存
        
        Args:
            key: 缓存键
            data: 数据
        """
        # 如果缓存已满,删除访问次数最少的项
        if len(self.cache) >= self.max_size:
            min_key = min(self.access_count, key=self.access_count.get)
            del self.cache[min_key]
            del self.access_count[min_key]
        
        self.cache[key] = data.copy()
        self.access_count[key] = 0
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_count.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


if __name__ == '__main__':
    # 测试数据读取器
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        
        if file_path.endswith('.dat'):
            reader = FinancialDataReader()
            df = reader.read_financial_data(file_path)
            print(f"读取财务数据: {len(df)} 条")
            print(df.head())
            
        elif file_path.endswith('.day'):
            reader = DayDataReader()
            df = reader.read_day_data(file_path)
            print(f"读取日线数据: {len(df)} 条")
            print(df.head())
            print(df.tail())
    else:
        print("用法: python data_reader.py <文件路径>")
