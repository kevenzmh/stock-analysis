#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
一键回测脚本 - 改进版策略

功能：
1. 自动生成策略信号（celue汇总.csv）
2. 运行回测
3. 显示回测结果

使用方法：
    python run_backtest.py              # 使用现有信号文件（如果存在）
    python run_backtest.py regenerate   # 重新生成信号文件
    python run_backtest.py quick        # 快速回测（使用现有信号，不显示详细信息）

注意：
- 首次运行或策略修改后，建议使用 regenerate 参数
- 回测需要安装 rqalpha 库
"""

import os
import sys
import time
import subprocess
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def check_signal_file():
    """检查策略信号文件是否存在"""
    try:
        import user_config as ucfg
        signal_file = ucfg.tdx['csv_gbbq'] + os.sep + 'celue汇总.csv'
        return os.path.exists(signal_file)
    except:
        return False


def generate_signals():
    """生成策略信号"""
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]步骤1: 生成策略信号[/bold cyan]")
    console.print("=" * 70 + "\n")
    
    console.print("[yellow]正在运行 celue_save_improved.py...[/yellow]")
    console.print("[dim]这可能需要几分钟时间，请耐心等待...[/dim]\n")
    
    # 运行信号生成脚本
    try:
        result = subprocess.run(
            [sys.executable, "celue_save_improved.py"],
            capture_output=False,
            text=True,
            check=True
        )
        console.print("\n[green]✅ 策略信号生成完成！[/green]\n")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]❌ 策略信号生成失败: {e}[/red]")
        return False
    except FileNotFoundError:
        console.print("\n[red]❌ 未找到 celue_save_improved.py 文件[/red]")
        console.print("[yellow]提示: 请确保在正确的项目目录下运行[/yellow]")
        return False


def run_backtest():
    """运行回测"""
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]步骤2: 运行回测[/bold cyan]")
    console.print("=" * 70 + "\n")
    
    console.print("[yellow]正在运行回测...[/yellow]")
    console.print("[dim]回测时间: 2022-01-01 至 2025-12-30[/dim]\n")
    
    # 运行回测
    try:
        result = subprocess.run(
            [sys.executable, "huice.py"],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        console.print("\n[green]✅ 回测完成！[/green]\n")
        
        # 提取并显示回测结果
        output = result.stdout
        if "回测收益" in output:
            # 提取关键信息
            lines = output.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ['回测起点', '回测终点', '回测收益', '年化收益', '基准收益', '最大回撤']):
                    console.print(line)
        
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]❌ 回测失败: {e}[/red]")
        if e.stderr:
            console.print(f"[red]错误信息: {e.stderr}[/red]")
        return False
    except FileNotFoundError:
        console.print("\n[red]❌ 未找到 huice.py 文件[/red]")
        return False


def display_summary():
    """显示回测摘要"""
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]回测完成总结[/bold cyan]")
    console.print("=" * 70 + "\n")
    
    # 检查是否生成了结果文件
    result_dir = "D:\\Projects\\stock-analysis\\rq_result"
    if os.path.exists(result_dir):
        files = [f for f in os.listdir(result_dir) if f.endswith('.png')]
        if files:
            latest_file = max([os.path.join(result_dir, f) for f in files], key=os.path.getmtime)
            console.print(f"[green]✓ 收益曲线图已生成: {latest_file}[/green]")
    
    console.print("\n[bold yellow]📊 查看详细结果：[/bold yellow]")
    console.print("1. 打开 rq_result 文件夹查看收益走势图 (.png)")
    console.print("2. 查看 .pkl 文件获取详细交易记录")
    
    console.print("\n[bold cyan]📈 投资建议：[/bold cyan]")
    console.print("• 如果年化收益 > 15% 且最大回撤 < 30%，策略表现较好")
    console.print("• 如果跑赢基准（沪深300），说明策略有效")
    console.print("• 关注最大回撤，确保风险可控")
    console.print("• 建议用小资金实盘验证1-2个月")
    
    console.print("\n" + "=" * 70 + "\n")


def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold cyan]改进版策略回测工具[/bold cyan]\n"
        "自动生成信号 + 运行回测 + 显示结果",
        border_style="cyan"
    ))
    
    # 检查命令行参数
    regenerate = 'regenerate' in sys.argv[1:]
    quick = 'quick' in sys.argv[1:]
    
    # 步骤1: 检查或生成策略信号
    signal_exists = check_signal_file()
    
    if regenerate or not signal_exists:
        if not signal_exists:
            console.print("\n[yellow]⚠️  未找到策略信号文件，需要先生成[/yellow]")
        else:
            console.print("\n[yellow]📝 检测到 regenerate 参数，将重新生成策略信号[/yellow]")
        
        # 生成信号
        if not generate_signals():
            console.print("\n[red]❌ 策略信号生成失败，无法继续回测[/red]")
            return
    else:
        console.print("\n[green]✓ 检测到现有策略信号文件，将直接使用[/green]")
        console.print("[dim]提示: 如需重新生成信号，请使用参数 regenerate[/dim]\n")
    
    # 步骤2: 运行回测
    if not run_backtest():
        console.print("\n[red]❌ 回测失败[/red]")
        return
    
    # 步骤3: 显示摘要
    if not quick:
        display_summary()
    
    console.print("[bold green]🎉 回测流程全部完成！[/bold green]\n")


if __name__ == '__main__':
    try:
        start_time = time.time()
        main()
        elapsed_time = time.time() - start_time
        console.print(f"[dim]总用时: {elapsed_time:.2f} 秒[/dim]\n")
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  回测被用户中断[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()
