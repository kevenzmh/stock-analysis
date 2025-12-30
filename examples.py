#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化模块使用示例

演示如何使用优化后的各个模块

作者: 2024
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def example_1_config():
    """示例1: 配置管理"""
    print("=" * 60)
    print("示例1: 配置管理")
    print("=" * 60)
    
    from optimized import Config, load_legacy_config
    
    # 方式1: 使用默认配置
    print("\n1. 使用默认配置:")
    config = Config()
    print(f"  通达信路径: {config.paths.tdx_path}")
    print(f"  数据目录: {config.paths.csv_lday}")
    
    # 方式2: 加载旧配置
    print("\n2. 加载 user_config.py:")
    try:
        config = load_legacy_config()
        print(f"  ✓ 配置加载成功")
        print(f"  通达信路径: {config.paths.tdx_path}")
    except Exception as e:
        print(f"  ✗ 配置加载失败: {e}")
    
    # 方式3: 保存和加载配置文件
    print("\n3. 保存和加载配置文件:")
    config.save()
    print(f"  ✓ 配置已保存到 config.json")
    
    config2 = Config()
    print(f"  ✓ 配置已从 config.json 加载")


def example_2_logger():
    """示例2: 日志系统"""
    print("\n" + "=" * 60)
    print("示例2: 日志系统")
    print("=" * 60)
    
    from optimized import get_logger, set_log_level
    import logging
    
    logger = get_logger()
    
    print("\n1. 不同级别的日志:")
    logger.debug("这是调试信息(DEBUG)")
    logger.info("这是普通信息(INFO)")
    logger.warning("这是警告信息(WARNING)")
    logger.error("这是错误信息(ERROR)")
    
    print("\n2. 异常日志:")
    try:
        result = 1 / 0
    except Exception as e:
        logger.exception("捕获到异常(带堆栈信息)")
    
    print("\n提示: 详细日志已保存到 logs/ 目录")


def example_3_downloader():
    """示例3: 文件下载"""
    print("\n" + "=" * 60)
    print("示例3: 文件下载")
    print("=" * 60)
    
    from optimized import Downloader, verify_zip_file
    
    # 创建下载器
    downloader = Downloader(timeout=30, max_retries=2)
    
    # 测试URL(一个小文件)
    test_url = "https://www.python.org/static/community_logos/python-logo.png"
    save_path = "test_download.png"
    
    print(f"\n下载测试文件: {test_url}")
    success = downloader.download(test_url, save_path)
    
    if success:
        print("✓ 下载成功")
        # 清理测试文件
        import os
        os.remove(save_path)
        print("✓ 测试文件已清理")
    else:
        print("✗ 下载失败")
    
    downloader.close()


def example_4_data_reader():
    """示例4: 数据读取"""
    print("\n" + "=" * 60)
    print("示例4: 数据读取")
    print("=" * 60)
    
    from optimized import load_legacy_config, DataCache
    import os
    
    try:
        config = load_legacy_config()
        
        # 示例: 读取日线数据
        print("\n1. 读取日线数据:")
        csv_dir = config.paths.csv_lday
        
        if os.path.exists(csv_dir):
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            
            if csv_files:
                sample_file = csv_files[0]
                print(f"  示例文件: {sample_file}")
                # 这里可以添加实际的读取代码
            else:
                print("  ✗ 没有找到CSV文件")
        else:
            print(f"  ✗ 目录不存在: {csv_dir}")
        
        # 示例: 数据缓存
        print("\n2. 数据缓存:")
        cache = DataCache(max_size=100)
        print(f"  缓存大小限制: {cache.max_size}")
        print(f"  当前缓存条目: {cache.size()}")
        
    except Exception as e:
        print(f"✗ 示例执行失败: {e}")


def example_5_financial_manager():
    """示例5: 财务数据管理"""
    print("\n" + "=" * 60)
    print("示例5: 财务数据管理")
    print("=" * 60)
    
    from optimized import load_legacy_config, FinancialDataManager
    
    try:
        config = load_legacy_config()
        manager = FinancialDataManager(config)
        
        print("\n1. 获取服务器文件列表:")
        try:
            df = manager.get_server_file_list()
            print(f"  ✓ 服务器有 {len(df)} 个财务文件")
            print(f"  最新文件: {df['filename'].iloc[-1]}")
        except Exception as e:
            print(f"  ✗ 获取失败: {e}")
        
        print("\n2. 检查本地文件:")
        local_files = manager.get_local_file_list('zip')
        print(f"  本地ZIP文件数: {len(local_files)}")
        
        if local_files:
            print(f"  示例文件: {local_files[0]}")
        
        print("\n提示: 使用 update_financial_data.py 执行完整更新")
        
    except Exception as e:
        print(f"✗ 示例执行失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("优化模块使用示例")
    print("=" * 60)
    
    examples = [
        ("配置管理", example_1_config),
        ("日志系统", example_2_logger),
        ("文件下载", example_3_downloader),
        ("数据读取", example_4_data_reader),
        ("财务数据管理", example_5_financial_manager),
    ]
    
    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print("  0. 运行所有示例")
    
    try:
        choice = input("\n请选择要运行的示例 (0-5): ").strip()
        
        if choice == '0':
            # 运行所有示例
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    print(f"\n✗ 示例 '{name}' 执行失败: {e}")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            # 运行指定示例
            idx = int(choice) - 1
            examples[idx][1]()
        else:
            print("无效的选择")
            return 1
        
        print("\n" + "=" * 60)
        print("示例运行完成")
        print("=" * 60)
        return 0
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
        return 130
    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
