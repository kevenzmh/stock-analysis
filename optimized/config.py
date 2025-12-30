#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块 - 优化版
提供统一的配置管理和验证

作者: wking (原作者)
优化: 2024
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json


@dataclass
class PathConfig:
    """路径配置类"""
    tdx_path: str  # 通达信安装目录
    csv_lday: str  # 日线数据目录
    pickle: str  # pickle格式数据目录
    csv_index: str  # 指数数据目录
    csv_cw: str  # 财务数据目录
    csv_gbbq: str  # 股本变迁目录
    
    def validate(self) -> bool:
        """验证路径配置"""
        if not os.path.exists(self.tdx_path):
            print(f"错误: 通达信目录不存在: {self.tdx_path}")
            return False
        
        # 确保数据目录存在
        for path in [self.csv_lday, self.pickle, self.csv_index, 
                     self.csv_cw, self.csv_gbbq]:
            Path(path).mkdir(parents=True, exist_ok=True)
        
        return True
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式(兼容旧代码)"""
        return {
            'tdx_path': self.tdx_path,
            'csv_lday': self.csv_lday,
            'pickle': self.pickle,
            'csv_index': self.csv_index,
            'csv_cw': self.csv_cw,
            'csv_gbbq': self.csv_gbbq,
            'pytdx_ip': '218.6.170.55',
            'pytdx_port': 7709,
        }


@dataclass
class FilterConfig:
    """过滤配置类"""
    exclude_concepts: List[str] = field(default_factory=lambda: ["ST板块"])
    exclude_industries: List[str] = field(default_factory=lambda: ["T1002"])
    exclude_kcb: bool = True  # 排除科创板
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'exclude_concepts': self.exclude_concepts,
            'exclude_industries': self.exclude_industries,
            'exclude_kcb': self.exclude_kcb,
        }


class Config:
    """统一配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径,如果为None则使用默认配置
        """
        self.config_file = config_file or "config.json"
        self.debug = False
        
        # 默认路径配置
        self.paths = PathConfig(
            tdx_path='d:/stock/通达信',
            csv_lday='d:/TDXdata/lday_qfq',
            pickle='d:/TDXdata/pickle',
            csv_index='d:/TDXdata/index',
            csv_cw='d:/TDXdata/cw',
            csv_gbbq='d:/TDXdata',
        )
        
        # 过滤配置
        self.filters = FilterConfig()
        
        # 指数列表
        self.index_list = [
            'sh999999.day',  # 上证指数
            'sh000300.day',  # 沪深300
            'sz399001.day',  # 深成指
        ]
        
        # 尝试加载配置文件
        self.load()
    
    def load(self) -> bool:
        """从文件加载配置"""
        if not os.path.exists(self.config_file):
            print(f"配置文件不存在,使用默认配置: {self.config_file}")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载路径配置
            if 'paths' in data:
                self.paths = PathConfig(**data['paths'])
            
            # 加载过滤配置
            if 'filters' in data:
                self.filters = FilterConfig(**data['filters'])
            
            # 加载其他配置
            self.debug = data.get('debug', False)
            self.index_list = data.get('index_list', self.index_list)
            
            print(f"配置加载成功: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"配置加载失败: {e}")
            return False
    
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            data = {
                'paths': {
                    'tdx_path': self.paths.tdx_path,
                    'csv_lday': self.paths.csv_lday,
                    'pickle': self.paths.pickle,
                    'csv_index': self.paths.csv_index,
                    'csv_cw': self.paths.csv_cw,
                    'csv_gbbq': self.paths.csv_gbbq,
                },
                'filters': self.filters.to_dict(),
                'debug': self.debug,
                'index_list': self.index_list,
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"配置保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"配置保存失败: {e}")
            return False
    
    def validate(self) -> bool:
        """验证配置"""
        return self.paths.validate()
    
    def get_tdx_dict(self) -> Dict:
        """获取通达信配置字典(兼容旧代码)"""
        return self.paths.to_dict()


# 兼容旧代码的接口
def load_legacy_config():
    """加载旧版user_config.py配置"""
    try:
        import user_config as ucfg
        
        config = Config()
        config.debug = ucfg.debug
        config.paths = PathConfig(
            tdx_path=ucfg.tdx['tdx_path'],
            csv_lday=ucfg.tdx['csv_lday'],
            pickle=ucfg.tdx['pickle'],
            csv_index=ucfg.tdx['csv_index'],
            csv_cw=ucfg.tdx['csv_cw'],
            csv_gbbq=ucfg.tdx['csv_gbbq'],
        )
        config.index_list = ucfg.index_list
        
        return config
        
    except ImportError:
        print("警告: 无法导入user_config.py,使用默认配置")
        return Config()


if __name__ == '__main__':
    # 测试配置管理
    config = Config()
    
    # 验证配置
    if config.validate():
        print("配置验证通过")
    
    # 保存配置
    config.save()
    
    # 重新加载
    config2 = Config()
    print(f"Debug模式: {config2.debug}")
    print(f"通达信路径: {config2.paths.tdx_path}")
