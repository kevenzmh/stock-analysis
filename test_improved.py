#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
改进版策略快速测试脚本

用途:
1. 验证改进版策略是否能正常运行
2. 对比原始版和改进版的筛选结果
3. 显示评分系统的工作效果

运行方法:
    python test_improved.py
"""

import os
import sys
import pandas as pd
from rich import print
from rich.table import Table
from rich.console import Console

# 导入策略模块
try:
    import CeLue
    import CeLue_improved
    import user_config as ucfg
    print("[green]✓ 模块导入成功[/green]\n")
except ImportError as e:
    print(f"[red]✗ 模块导入失败: {e}[/red]")
    print("[yellow]请确保在正确的项目目录下运行此脚本[/yellow]")
    sys.exit(1)

console = Console()

# 测试股票列表
TEST_STOCKS = ['000001', '600036', '000002', '600519', '000858']

def test_strategy():
    """测试改进版策略"""
    
    print("=" * 70)
    print("[bold cyan]改进版策略测试[/bold cyan]")
    print("=" * 70)
    
    # ========== 1. 加载沪深300指数 ==========
    print("\n[1/4] 加载沪深300指数数据...")
    try:
        df_hs300 = pd.read_csv(
            ucfg.tdx['csv_index'] + '/000300.csv',
            index_col=None,
            encoding='gbk',
            dtype={'code': str}
        )
        df_hs300['date'] = pd.to_datetime(df_hs300['date'], format='%Y-%m-%d')
        df_hs300.set_index('date', drop=False, inplace=True)
        
        HS300_信号 = CeLue.策略HS300(df_hs300)
        print(f"      [green]✓ 沪深300信号生成成功[/green]")
        print(f"      [cyan]  当前大盘状态: {'向好 🚀' if HS300_信号.iloc[-1] else '不佳 ⚠️'}[/cyan]")
    except Exception as e:
        print(f"      [red]✗ 沪深300数据加载失败: {e}[/red]")
        sys.exit(1)
    
    # ========== 2. 对比测试 ==========
    print(f"\n[2/4] 对比原始版和改进版策略1...")
    print(f"      测试 {len(TEST_STOCKS)} 只股票\n")
    
    table = Table(title="策略1对比测试", show_header=True, header_style="bold magenta")
    table.add_column("股票代码", style="cyan", justify="center", width=10)
    table.add_column("原始策略1", style="yellow", justify="center", width=12)
    table.add_column("改进策略1", style="green", justify="center", width=12)
    table.add_column("结果", style="red", justify="center", width=20)
    
    原始通过 = 0
    改进通过 = 0
    
    for code in TEST_STOCKS:
        try:
            pkl_file = ucfg.tdx['pickle'] + os.sep + code + '.pkl'
            csv_file = ucfg.tdx['csv_lday'] + os.sep + code + '.csv'
            
            if os.path.exists(pkl_file):
                df_stock = pd.read_pickle(pkl_file)
            elif os.path.exists(csv_file):
                df_stock = pd.read_csv(csv_file, index_col=None, encoding='gbk', dtype={'code': str})
                df_stock['date'] = pd.to_datetime(df_stock['date'], format='%Y-%m-%d')
                df_stock.set_index('date', drop=False, inplace=True)
            else:
                table.add_row(code, "数据缺失", "数据缺失", "跳过")
                continue
            
            # 测试原始策略1
            result_original = CeLue.策略1(df_stock, mode='fast')
            
            # 测试改进策略1
            result_improved = CeLue_improved.策略1_增强版(df_stock, mode='fast')
            
            原始通过 += 1 if result_original else 0
            改进通过 += 1 if result_improved else 0
            
            # 判断结果
            if result_original and result_improved:
                result_text = "都通过 ✓✓"
            elif result_original and not result_improved:
                result_text = "改进版更严格 ⚡"
            elif not result_original and result_improved:
                result_text = "异常情况 ⚠️"
            else:
                result_text = "都未通过 ✗✗"
            
            table.add_row(
                code,
                "通过 ✓" if result_original else "未通过 ✗",
                "通过 ✓" if result_improved else "未通过 ✗",
                result_text
            )
            
        except Exception as e:
            table.add_row(code, "错误", "错误", f"异常: {str(e)[:15]}...")
    
    console.print(table)
    print(f"\n      [cyan]原始版通过率: {原始通过}/{len(TEST_STOCKS)} = {原始通过/len(TEST_STOCKS)*100:.1f}%[/cyan]")
    print(f"      [green]改进版通过率: {改进通过}/{len(TEST_STOCKS)} = {改进通过/len(TEST_STOCKS)*100:.1f}%[/green]")
    
    # ========== 3. 评分系统测试 ==========
    print(f"\n[3/4] 测试改进版策略2评分系统...")
    
    score_table = Table(title="策略2评分测试", show_header=True, header_style="bold magenta")
    score_table.add_column("股票代码", style="cyan", justify="center", width=10)
    score_table.add_column("买入信号", style="yellow", justify="center", width=12)
    score_table.add_column("综合得分", style="green", justify="center", width=12)
    score_table.add_column("评级", style="red", justify="center", width=15)
    
    得分列表 = []
    
    for code in TEST_STOCKS:
        try:
            pkl_file = ucfg.tdx['pickle'] + os.sep + code + '.pkl'
            
            if not os.path.exists(pkl_file):
                continue
            
            df_stock = pd.read_pickle(pkl_file)
            df_stock['date'] = pd.to_datetime(df_stock['date'], format='%Y-%m-%d')
            df_stock.set_index('date', drop=False, inplace=True)
            
            # 测试评分系统
            信号, 得分 = CeLue_improved.策略2_精选版(df_stock, HS300_信号)
            
            得分列表.append((code, 得分))
            
            # 评级
            if 得分 >= 80:
                rating = "⭐⭐⭐⭐⭐"
            elif 得分 >= 70:
                rating = "⭐⭐⭐⭐"
            elif 得分 >= 60:
                rating = "⭐⭐⭐"
            elif 得分 >= 50:
                rating = "⭐⭐"
            else:
                rating = "⭐"
            
            score_table.add_row(
                code,
                "是 ✓" if 信号 else "否 ✗",
                f"{得分:.1f}" if 信号 else "N/A",
                rating if 信号 else "无信号"
            )
            
        except Exception as e:
            score_table.add_row(code, "错误", "N/A", f"异常: {str(e)[:10]}...")
    
    console.print(score_table)
    
    if len(得分列表) > 0:
        得分列表.sort(key=lambda x: x[1], reverse=True)
        print(f"\n      [green]✓ 评分系统工作正常[/green]")
        print(f"      [cyan]  最高分: {得分列表[0][0]} ({得分列表[0][1]:.1f}分)[/cyan]")
    else:
        print(f"\n      [yellow]⚠️  没有股票获得买入信号[/yellow]")
    
    # ========== 4. 总结 ==========
    print(f"\n[4/4] 测试总结")
    print("=" * 70)
    
    if 改进通过 < 原始通过:
        print("[green]✓ 改进版策略1筛选更严格，符合预期[/green]")
    else:
        print("[yellow]⚠️  改进版策略1可能需要调整参数[/yellow]")
    
    if len(得分列表) > 0:
        print("[green]✓ 评分系统运行正常[/green]")
    else:
        print("[yellow]⚠️  评分系统未找到符合条件的股票（可能是大盘环境不佳）[/yellow]")
    
    print("\n[bold cyan]测试完成！可以运行主程序了：[/bold cyan]")
    print("[yellow]    python xuangu.py[/yellow]")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        test_strategy()
    except KeyboardInterrupt:
        print("\n\n[yellow]测试被用户中断[/yellow]")
    except Exception as e:
        print(f"\n[red]测试失败: {e}[/red]")
        import traceback
        traceback.print_exc()
