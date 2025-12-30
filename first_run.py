#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
首次运行指导脚本
帮助你一步步完成项目的首次运行

运行方式: python first_run.py
"""

import os
import sys
import time
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"{msg}")
    print(f"{'='*60}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def check_environment():
    """检查环境"""
    print_header("步骤1: 检查环境")
    
    print("正在检查环境...")
    result = os.system("python check_environment.py")
    
    if result != 0:
        print_error("环境检查未通过")
        print_info("请按照提示解决问题后重新运行")
        return False
    
    print_success("环境检查通过")
    return True

def create_data_directories():
    """创建数据目录"""
    print_header("步骤2: 创建数据目录")
    
    try:
        import user_config as ucfg
        
        dirs = [
            ucfg.tdx['csv_lday'],
            ucfg.tdx['pickle'],
            ucfg.tdx['csv_index'],
            ucfg.tdx['csv_cw'],
            ucfg.tdx['csv_gbbq'],
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print_success(f"目录已创建/确认: {dir_path}")
        
        return True
        
    except Exception as e:
        print_error(f"创建目录失败: {e}")
        return False

def update_financial_data():
    """更新财务数据"""
    print_header("步骤3: 更新财务数据")
    
    print_info("这一步会从通达信服务器下载财务数据")
    print_info("首次运行需要下载较多文件，预计 5-15 分钟")
    
    response = input("\n是否开始? (y/n): ").strip().lower()
    if response != 'y':
        print_warning("跳过财务数据更新")
        return False
    
    print("\n开始更新财务数据...")
    start_time = time.time()
    
    # 尝试使用优化版本
    if os.path.exists('update_financial_data.py'):
        result = os.system("python update_financial_data.py")
    else:
        result = os.system("python readTDX_cw.py")
    
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"财务数据更新完成 (耗时: {elapsed:.1f}秒)")
        return True
    else:
        print_error("财务数据更新失败")
        print_info("请检查网络连接和通达信服务器状态")
        return False

def generate_daily_data():
    """生成日线数据"""
    print_header("步骤4: 生成日线数据")
    
    print_warning("重要提示:")
    print("  - 首次运行需要处理全市场4000+只股票")
    print("  - 预计耗时: 30分钟 - 2小时")
    print("  - 建议使用固态硬盘，速度会快很多")
    print("  - 可以在运行时做其他事情")
    
    response = input("\n是否开始? (y/n): ").strip().lower()
    if response != 'y':
        print_warning("跳过日线数据生成")
        return False
    
    print("\n开始生成日线数据...")
    print_info("这可能需要较长时间，请耐心等待...")
    
    start_time = time.time()
    result = os.system("python readTDX_lday.py")
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"日线数据生成完成 (耗时: {elapsed/60:.1f}分钟)")
        return True
    else:
        print_error("日线数据生成失败")
        return False

def test_strategy():
    """测试策略"""
    print_header("步骤5: 测试策略")
    
    print("正在测试策略文件...")
    
    try:
        import CeLue
        print_success("策略文件导入成功")
        
        # 运行策略测试
        result = os.system("python CeLue.py")
        
        if result == 0:
            print_success("策略测试通过")
            return True
        else:
            print_warning("策略测试有警告，但可以继续")
            return True
            
    except Exception as e:
        print_error(f"策略文件测试失败: {e}")
        return False

def run_stock_selection():
    """运行选股"""
    print_header("步骤6: 运行选股")
    
    print_info("现在可以运行选股了！")
    print_info("预计耗时: 5-15 分钟")
    
    response = input("\n是否开始选股? (y/n): ").strip().lower()
    if response != 'y':
        print_warning("跳过选股")
        return False
    
    print("\n开始运行选股...")
    start_time = time.time()
    
    result = os.system("python xuangu.py")
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"选股完成 (耗时: {elapsed:.1f}秒)")
        return True
    else:
        print_error("选股失败")
        return False

def print_final_summary(steps_completed):
    """打印最终总结"""
    print_header("首次运行总结")
    
    total_steps = 6
    completed = sum(steps_completed.values())
    
    print(f"完成进度: {completed}/{total_steps}")
    print()
    
    for step_name, completed in steps_completed.items():
        status = "✓" if completed else "✗"
        color = Colors.GREEN if completed else Colors.RED
        print(f"{color}{status}{Colors.END} {step_name}")
    
    print()
    
    if completed == total_steps:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 恭喜！项目首次运行完全成功！{Colors.END}")
        print("\n后续使用:")
        print("  每天16:00后运行:")
        print("    1. python readTDX_cw.py    # 更新财务数据")
        print("    2. python readTDX_lday.py  # 更新日线数据")
        print("    3. python xuangu.py        # 运行选股")
        print("\n  或使用启动脚本: start.bat")
    else:
        print(f"{Colors.YELLOW}部分步骤未完成，请检查错误信息{Colors.END}")
        print("\n未完成的步骤可以稍后手动运行")

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "股票分析系统 - 首次运行向导" + " "*15 + "║")
    print("╚" + "═"*58 + "╝")
    print(f"{Colors.END}\n")
    
    print("本向导将帮助你完成以下步骤:")
    print("  1. 检查环境")
    print("  2. 创建数据目录")
    print("  3. 更新财务数据")
    print("  4. 生成日线数据 (耗时最长)")
    print("  5. 测试策略")
    print("  6. 运行选股")
    
    print("\n" + "="*60)
    
    response = input("\n是否开始? (y/n): ").strip().lower()
    if response != 'y':
        print("已取消")
        return 1
    
    # 记录每个步骤的完成状态
    steps_completed = {}
    
    try:
        # 步骤1: 检查环境
        steps_completed["1. 检查环境"] = check_environment()
        if not steps_completed["1. 检查环境"]:
            print_error("环境检查失败，无法继续")
            print_final_summary(steps_completed)
            return 1
        
        # 步骤2: 创建目录
        steps_completed["2. 创建数据目录"] = create_data_directories()
        
        # 步骤3: 更新财务数据
        steps_completed["3. 更新财务数据"] = update_financial_data()
        
        # 步骤4: 生成日线数据
        steps_completed["4. 生成日线数据"] = generate_daily_data()
        
        # 步骤5: 测试策略
        steps_completed["5. 测试策略"] = test_strategy()
        
        # 步骤6: 运行选股
        if steps_completed["4. 生成日线数据"]:
            steps_completed["6. 运行选股"] = run_stock_selection()
        else:
            print_warning("跳过选股（日线数据未生成）")
            steps_completed["6. 运行选股"] = False
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}用户中断运行{Colors.END}")
        print_final_summary(steps_completed)
        return 130
    
    except Exception as e:
        print_error(f"运行出错: {e}")
        import traceback
        traceback.print_exc()
        print_final_summary(steps_completed)
        return 1
    
    # 打印最终总结
    print_final_summary(steps_completed)
    
    return 0 if all(steps_completed.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
