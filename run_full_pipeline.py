#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整流程运行脚本（包括回测）
一键完成从数据更新到回测的全部流程

运行方式: python run_full_pipeline.py
"""

import os
import sys
import time
import shutil
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(msg, level=1):
    if level == 1:
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
        print(f"{msg}")
        print(f"{'='*70}{Colors.END}\n")
    else:
        print(f"\n{Colors.CYAN}{'-'*70}")
        print(f"{msg}")
        print(f"{'-'*70}{Colors.END}\n")

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def print_step(step_num, total_steps, msg):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}[步骤 {step_num}/{total_steps}] {msg}{Colors.END}")

def check_rqalpha_bundle():
    """检查RQAlpha数据包"""
    print_info("检查RQAlpha数据包...")
    
    bundle_path = Path.home() / '.rqalpha' / 'bundle'
    
    if not bundle_path.exists():
        print_warning("RQAlpha数据包未安装")
        print_info("正在下载RQAlpha数据包...")
        
        result = os.system("rqalpha update-bundle")
        
        if result == 0:
            print_success("RQAlpha数据包安装成功")
            return True
        else:
            print_error("RQAlpha数据包安装失败")
            print_info("请手动运行: rqalpha update-bundle")
            return False
    else:
        print_success(f"RQAlpha数据包已存在: {bundle_path}")
        return True

def step1_update_financial_data(mode='fast'):
    """步骤1: 更新财务数据"""
    print_step(1, 6, "更新财务数据")
    
    if mode == 'fast':
        print_info("快速模式：跳过财务数据更新（如需更新请选择完整模式）")
        return True
    
    print_info("开始更新财务数据...")
    start_time = time.time()
    
    # 使用优化版本
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
        return False

def step2_update_daily_data(mode='fast'):
    """步骤2: 更新日线数据"""
    print_step(2, 6, "更新日线数据")
    
    if mode == 'fast':
        print_info("快速模式：只更新新增数据")
    else:
        print_info("完整模式：重新生成所有数据")
    
    print_info("开始更新日线数据...")
    start_time = time.time()
    
    if mode == 'fast':
        result = os.system("python readTDX_lday.py")
    else:
        result = os.system("python readTDX_lday.py del")
    
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"日线数据更新完成 (耗时: {elapsed/60:.1f}分钟)")
        return True
    else:
        print_error("日线数据更新失败")
        return False

def step3_save_strategy_signals(mode='fast'):
    """步骤3: 保存策略信号"""
    print_step(3, 6, "保存策略信号")
    
    print_info("为所有股票的历史数据添加买卖信号...")
    print_warning("这一步可能需要较长时间（10-30分钟）")
    
    start_time = time.time()
    
    if mode == 'fast':
        # 快速模式：只更新缺失的信号
        result = os.system("python celue_save.py")
    else:
        # 完整模式：重新生成所有信号
        result = os.system("python celue_save.py del")
    
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"策略信号保存完成 (耗时: {elapsed/60:.1f}分钟)")
        
        # 检查celue汇总.csv是否生成
        import user_config as ucfg
        celue_file = Path(ucfg.tdx['csv_gbbq']) / 'celue汇总.csv'
        if celue_file.exists():
            print_success(f"策略汇总文件已生成: {celue_file}")
            
            # 显示文件大小
            file_size = celue_file.stat().st_size / 1024 / 1024
            print_info(f"文件大小: {file_size:.2f} MB")
            
            return True
        else:
            print_error("策略汇总文件未生成")
            return False
    else:
        print_error("策略信号保存失败")
        return False

def step4_run_backtest():
    """步骤4: 运行回测"""
    print_step(4, 6, "运行回测")
    
    print_info("使用RQAlpha进行策略回测...")
    print_info("这将模拟策略在历史数据上的表现")
    
    # 检查celue汇总.csv是否存在
    import user_config as ucfg
    celue_file = Path(ucfg.tdx['csv_gbbq']) / 'celue汇总.csv'
    
    if not celue_file.exists():
        print_error("策略汇总文件不存在，无法进行回测")
        print_info("请先运行步骤3：保存策略信号")
        return False
    
    start_time = time.time()
    
    result = os.system("python huice.py")
    
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"回测完成 (耗时: {elapsed/60:.1f}分钟)")
        
        # 检查回测结果
        if os.path.exists('rq_result'):
            result_files = [f for f in os.listdir('rq_result') if f.endswith('.pkl')]
            if result_files:
                latest_result = sorted(result_files)[-1]
                print_success(f"回测结果已保存: rq_result/{latest_result}")
                return True
        
        return True
    else:
        print_error("回测失败")
        return False

def step5_visualize_results():
    """步骤5: 可视化结果"""
    print_step(5, 6, "可视化回测结果")
    
    print_info("生成回测结果的可视化图表...")
    
    start_time = time.time()
    
    result = os.system("python plot.py")
    
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"可视化完成 (耗时: {elapsed:.1f}秒)")
        
        if os.path.exists('pyecharts.html'):
            print_success("可视化文件已生成: pyecharts.html")
            print_info("请在浏览器中打开 pyecharts.html 查看结果")
            return True
        else:
            print_warning("可视化文件未找到")
            return True
    else:
        print_error("可视化失败")
        return False

def step6_run_selection():
    """步骤6: 运行选股"""
    print_step(6, 6, "运行选股（获取最新信号）")
    
    print_info("基于最新数据运行选股...")
    
    start_time = time.time()
    
    result = os.system("python xuangu.py")
    
    elapsed = time.time() - start_time
    
    if result == 0:
        print_success(f"选股完成 (耗时: {elapsed:.1f}秒)")
        return True
    else:
        print_error("选股失败")
        return False

def print_summary(steps_completed, total_time):
    """打印执行摘要"""
    print_header("执行摘要", level=1)
    
    total_steps = len(steps_completed)
    completed = sum(steps_completed.values())
    
    print(f"完成进度: {completed}/{total_steps}")
    print()
    
    for step_name, status in steps_completed.items():
        status_symbol = "✓" if status else "✗"
        color = Colors.GREEN if status else Colors.RED
        print(f"{color}{status_symbol}{Colors.END} {step_name}")
    
    print()
    print(f"总耗时: {total_time/60:.1f} 分钟")
    print()
    
    if completed == total_steps:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 完整流程执行成功！{Colors.END}")
        print("\n查看结果:")
        print("  1. 回测报告: rq_result/ 目录")
        print("  2. 可视化图表: pyecharts.html")
        print("  3. 选股结果: 控制台输出")
    else:
        print(f"{Colors.YELLOW}部分步骤未完成{Colors.END}")

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*15 + "股票分析系统 - 完整流程（含回测）" + " "*15 + "║")
    print("╚" + "═"*68 + "╝")
    print(f"{Colors.END}\n")
    
    print("完整流程包括以下步骤:")
    print("  1. 更新财务数据")
    print("  2. 更新日线数据")
    print("  3. 保存策略信号 ⭐")
    print("  4. 运行回测 ⭐")
    print("  5. 可视化结果 ⭐")
    print("  6. 运行选股")
    
    print("\n" + "="*70)
    print("\n选择运行模式:")
    print("  [1] 完整模式 - 重新生成所有数据和信号（推荐首次运行）")
    print("  [2] 快速模式 - 只更新增量数据（日常使用）")
    print("  [3] 仅回测 - 跳过数据更新，直接回测（数据已是最新）")
    print("  [0] 退出")
    
    while True:
        choice = input("\n请选择 (0-3): ").strip()
        if choice in ['0', '1', '2', '3']:
            break
        print_error("无效选择，请重新输入")
    
    if choice == '0':
        print("已退出")
        return 0
    
    # 确定运行模式
    if choice == '1':
        mode = 'full'
        run_steps = [1, 2, 3, 4, 5, 6]
    elif choice == '2':
        mode = 'fast'
        run_steps = [1, 2, 3, 4, 5, 6]
    else:  # choice == '3'
        mode = 'fast'
        run_steps = [4, 5, 6]
        print_warning("跳过数据更新步骤")
    
    # 确认开始
    print(f"\n准备以 {Colors.BOLD}{mode.upper()}{Colors.END} 模式运行")
    response = input("是否开始? (y/n): ").strip().lower()
    
    if response != 'y':
        print("已取消")
        return 0
    
    # 检查RQAlpha
    print_header("环境检查", level=2)
    if not check_rqalpha_bundle():
        print_error("RQAlpha环境检查失败")
        return 1
    
    # 记录开始时间
    total_start_time = time.time()
    
    # 执行步骤
    steps_completed = {}
    
    try:
        # 步骤1: 更新财务数据
        if 1 in run_steps:
            result = step1_update_financial_data(mode)
            steps_completed["1. 更新财务数据"] = result
            if not result and mode == 'full':
                print_error("财务数据更新失败，是否继续?")
                response = input("继续? (y/n): ").strip().lower()
                if response != 'y':
                    raise KeyboardInterrupt()
        
        # 步骤2: 更新日线数据
        if 2 in run_steps:
            result = step2_update_daily_data(mode)
            steps_completed["2. 更新日线数据"] = result
            if not result:
                print_error("日线数据更新失败，无法继续")
                raise KeyboardInterrupt()
        
        # 步骤3: 保存策略信号
        if 3 in run_steps:
            result = step3_save_strategy_signals(mode)
            steps_completed["3. 保存策略信号"] = result
            if not result:
                print_error("策略信号保存失败，无法进行回测")
                raise KeyboardInterrupt()
        
        # 步骤4: 运行回测
        if 4 in run_steps:
            result = step4_run_backtest()
            steps_completed["4. 运行回测"] = result
        
        # 步骤5: 可视化结果
        if 5 in run_steps:
            result = step5_visualize_results()
            steps_completed["5. 可视化结果"] = result
        
        # 步骤6: 运行选股
        if 6 in run_steps:
            result = step6_run_selection()
            steps_completed["6. 运行选股"] = result
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}用户中断执行{Colors.END}")
    
    except Exception as e:
        print_error(f"执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 计算总耗时
    total_time = time.time() - total_start_time
    
    # 打印摘要
    print_summary(steps_completed, total_time)
    
    return 0 if all(steps_completed.values()) else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}程序已中断{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}程序异常: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
