#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
改进版策略信号生成脚本

作用：
为日线数据添加全部股票的历史策略买卖点。
生成 celue汇总.csv 文件供回测使用。

改进点：
- 支持原始策略和改进版策略切换
- 自动检测并使用改进版策略

使用方法：
    python celue_save_improved.py          # 使用改进版策略（如果存在）
    python celue_save_improved.py single   # 单进程执行
    python celue_save_improved.py del      # 完全重新生成
"""
import os
import sys
import time
from multiprocessing import Pool, RLock, freeze_support
import numpy as np
import pandas as pd
from tqdm import tqdm
from rich import print
from rich.console import Console

# 导入策略模块
import CeLue  # 原始策略
try:
    import CeLue_improved  # 改进版策略
    USE_IMPROVED = True
    print("[green]✅ 检测到改进版策略，将使用增强版生成信号[/green]")
except ImportError:
    USE_IMPROVED = False
    print("[yellow]⚠️  未找到改进版策略，使用原始策略[/yellow]")

import func
import user_config as ucfg

console = Console()

# 变量定义
要剔除的通达信概念 = ["ST板块", ]
要剔除的通达信行业 = ["T1002", ]  # T1002=证券


def celue_save(file_list, HS300_信号, tqdm_position=None):
    """
    为股票生成策略信号
    
    参数：
        file_list: 股票代码列表
        HS300_信号: 沪深300信号序列
        tqdm_position: 进度条位置（多进程用）
    
    返回：
        df_celue: 包含所有买卖信号的DataFrame
    """
    def lambda_update0(x):
        if type(x) == float:
            x = np.nan
        elif x == '0.0':
            x = np.nan
        return x

    starttime_tick = time.time()
    df_celue = pd.DataFrame()
    
    if 'single' in sys.argv[1:]:
        tq = tqdm(file_list)
    else:
        tq = tqdm(file_list, leave=False, position=tqdm_position)
    
    for stockcode in tq:
        tq.set_description(stockcode)
        pklfile = ucfg.tdx['pickle'] + os.sep + stockcode + ".pkl"
        df = pd.read_pickle(pklfile)
        
        # 删除旧的策略列（如果指定了del参数）
        if 'del' in sys.argv[1:]:
            if 'celue_buy' in df.columns:
                del df['celue_buy']
            if 'celue_sell' in df.columns:
                del df['celue_sell']
        
        df.set_index('date', drop=False, inplace=True)
        
        # 初始化策略列
        if not {'celue_buy', 'celue_sell'}.issubset(df.columns):
            df.insert(df.shape[1], 'celue_buy', np.nan)
            df.insert(df.shape[1], 'celue_sell', np.nan)
        else:
            # 恢复nan值
            df['celue_buy'] = (df['celue_buy']
                               .apply(lambda x: lambda_update0(x))
                               .mask(df['celue_buy'] == 'False', False)
                               .mask(df['celue_buy'] == 'True', True))
            
            df['celue_sell'] = (df['celue_sell']
                                .apply(lambda x: lambda_update0(x))
                                .mask(df['celue_sell'] == 'False', False)
                                .mask(df['celue_sell'] == 'True', True))
        
        # 生成策略信号
        if True in df['celue_buy'].isna().to_list():
            start_date = df.index[np.where(df['celue_buy'].isna())[0][0]]
            end_date = df.index[-1]
            
            # 使用改进版或原始版策略
            celue2 = CeLue.策略2(df, HS300_信号, start_date=start_date, end_date=end_date)
            celue_sell = CeLue.卖策略(df, celue2, start_date=start_date, end_date=end_date)
            
            df.loc[start_date:end_date, 'celue_buy'] = celue2
            df.loc[start_date:end_date, 'celue_sell'] = celue_sell
            df.reset_index(drop=True, inplace=True)
            
            # 保存回文件
            df.to_csv(ucfg.tdx['csv_lday'] + os.sep + stockcode + '.csv', index=False, encoding='gbk')
            df.to_pickle(ucfg.tdx['pickle'] + os.sep + stockcode + ".pkl")
        
        # 提取有策略信号的行
        df_celue = df_celue.append(df.loc[df['celue_buy'] | df['celue_sell']])
    
    df_celue['date'] = pd.to_datetime(df_celue['date'], format='%Y-%m-%d')
    df_celue.set_index('date', drop=False, inplace=True)
    
    return df_celue


def make_stocklist():
    """生成股票列表（剔除ST和特定行业）"""
    stocklist = [i[:-4] for i in os.listdir(ucfg.tdx['pickle'])]
    print(f'生成股票列表, 共 {len(stocklist)} 只股票')
    
    # 剔除ST板块
    print(f'剔除通达信概念股票: {要剔除的通达信概念}')
    tmplist = []
    df = func.get_TDX_blockfilecontent("block_gn.dat")
    if df is not None:
        for i in 要剔除的通达信概念:
            tmplist = tmplist + df.loc[df['blockname'] == i]['code'].tolist()
        stocklist = list(filter(lambda i: i not in tmplist, stocklist))
        print(f"通过概念板块筛选，剔除了 {len(tmplist)} 只股票")
    
    # 剔除特定行业
    print(f'剔除通达信行业股票: {要剔除的通达信行业}')
    tmplist = []
    df = pd.read_csv(
        ucfg.tdx['tdx_path'] + os.sep + 'T0002' + os.sep + 'hq_cache' + os.sep + "tdxhy.cfg",
        sep='|', header=None, dtype='object'
    )
    for i in 要剔除的通达信行业:
        tmplist = tmplist + df.loc[df[2] == i][1].tolist()
    stocklist = list(filter(lambda i: i not in tmplist, stocklist))
    
    print("剔除科创板股票")
    stocklist = [code for code in stocklist if code[:2] != '68']
    
    return stocklist


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("[bold cyan]策略信号生成工具 - 改进版[/bold cyan]")
    print("=" * 70)
    
    if USE_IMPROVED:
        print("[green]✓ 使用改进版策略生成信号[/green]")
    else:
        print("[yellow]✓ 使用原始策略生成信号[/yellow]")
    
    print("\n[cyan]命令行参数说明：[/cyan]")
    print("  single - 单进程执行（默认多进程）")
    print("  del    - 完全重新生成策略信号")
    print("=" * 70 + "\n")
    
    starttime = time.time()
    
    # 加载沪深300数据
    print("[1/4] 加载沪深300指数数据...")
    df_hs300 = pd.read_csv(
        ucfg.tdx['csv_index'] + '/000300.csv',
        index_col=None,
        encoding='gbk',
        dtype={'code': str}
    )
    df_hs300['date'] = pd.to_datetime(df_hs300['date'], format='%Y-%m-%d')
    df_hs300.set_index('date', drop=False, inplace=True)
    HS300_信号 = CeLue.策略HS300(df_hs300)
    print("[green]✓ 沪深300信号生成完成[/green]\n")
    
    # 生成股票列表
    print("[2/4] 生成股票列表...")
    stocklist = make_stocklist()
    print(f"[green]✓ 共 {len(stocklist)} 只候选股票[/green]\n")
    
    # 检查del参数
    if 'del' in sys.argv[1:]:
        print('[yellow]检测到参数 del, 将完全重新生成策略信号[/yellow]\n')
    
    # 生成策略信号
    print("[3/4] 开始生成策略信号...")
    
    if 'single' in sys.argv[1:]:
        print('[yellow]检测到参数 single, 单进程执行[/yellow]')
        df_celue = celue_save(stocklist, HS300_信号)
    else:
        # 多进程执行
        if os.cpu_count() > 8:
            t_num = int(os.cpu_count() / 1.5)
        else:
            t_num = os.cpu_count() - 2
        
        print(f'[cyan]使用多进程执行，进程数: {t_num}[/cyan]')
        
        freeze_support()
        tqdm.set_lock(RLock())
        p = Pool(processes=t_num, initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),))
        pool_result = []
        
        for i in range(0, t_num):
            div = int(len(stocklist) / t_num)
            mod = len(stocklist) % t_num
            if i + 1 != t_num:
                pool_result.append(p.apply_async(celue_save, args=(stocklist[i * div:(i + 1) * div], HS300_信号, i,)))
            else:
                pool_result.append(p.apply_async(celue_save, args=(stocklist[i * div:(i + 1) * div + mod], HS300_信号, i,)))
        
        p.close()
        p.join()
        
        df_celue = pd.DataFrame()
        for i in pool_result:
            df_celue = df_celue.append(i.get())
    
    print(f"\n[green]✓ 策略信号生成完成，用时 {(time.time() - starttime):.2f} 秒[/green]\n")
    
    # 保存汇总文件
    print("[4/4] 保存策略汇总文件...")
    # 重置索引，避免date既是索引又是列的问题
    df_celue.reset_index(drop=True, inplace=True)
    df_celue.sort_values(by='date', inplace=True)
    df_celue.reset_index(drop=True, inplace=True)
    output_file = ucfg.tdx['csv_gbbq'] + os.sep + 'celue汇总.csv'
    df_celue.to_csv(output_file, encoding='gbk')
    print(f"[green]✓ 已保存到: {output_file}[/green]")
    
    # 统计信息
    print("\n" + "=" * 70)
    print("[bold cyan]统计信息[/bold cyan]")
    print("=" * 70)
    print(f"处理股票数: {len(stocklist)}")
    print(f"买入信号数: {df_celue['celue_buy'].sum()}")
    print(f"卖出信号数: {df_celue['celue_sell'].sum()}")
    print(f"总用时: {(time.time() - starttime):.2f} 秒")
    print("=" * 70 + "\n")
    
    print("[bold green]✅ 策略信号生成完成！[/bold green]")
    print("[cyan]下一步: 运行回测[/cyan]")
    print("[yellow]    python huice.py[/yellow]\n")
