#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
财务数据更新脚本 - 优化版
替代原来的 readTDX_cw.py

使用方法:
    python update_financial_data.py          # 使用默认配置
    python update_financial_data.py --debug  # 开启调试模式

作者: wking (原作者)
优化: 2024
"""

import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from optimized import (
    Config,
    load_legacy_config,
    FinancialDataManager,
    get_logger,
    set_log_level
)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='更新通达信财务数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python update_financial_data.py              # 正常模式
  python update_financial_data.py --debug      # 调试模式
  python update_financial_data.py --config config.json  # 指定配置文件
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='配置文件路径 (默认使用 user_config.py)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='开启调试模式'
    )
    
    parser.add_argument(
        '--skip-gbbq',
        action='store_true',
        help='跳过股本变迁文件处理'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析参数
    args = parse_args()
    
    # 设置日志级别
    if args.debug:
        set_log_level(logging.DEBUG)
    
    logger = get_logger()
    
    try:
        # 加载配置
        if args.config:
            logger.info(f"使用配置文件: {args.config}")
            config = Config(args.config)
        else:
            logger.info("使用 user_config.py 配置")
            config = load_legacy_config()
        
        # 验证配置
        if not config.validate():
            logger.error("配置验证失败")
            return 1
        
        # 创建财务数据管理器
        manager = FinancialDataManager(config)
        
        # 执行更新
        stats = manager.update_all()
        
        # 检查是否有失败
        total_fail = stats['download_fail'] + stats['update_fail']
        if total_fail > 0:
            logger.warning(f"有 {total_fail} 个文件处理失败")
        
        if not stats['gbbq_success'] and not args.skip_gbbq:
            logger.warning("股本变迁文件处理失败")
        
        logger.info("程序执行完成")
        return 0
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        return 130
    
    except Exception as e:
        logger.exception(f"程序执行出错: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
