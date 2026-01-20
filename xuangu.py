"""
选股多线程版本文件 - 改进版
使用增强策略 + 评分机制 + 智能精选

改进点:
1. 策略1: 使用增强版筛选,提高流动性和质量要求
2. 策略2: 增加评分机制,为每只股票打分
3. 最终精选: 只输出得分最高的TOP 30只股票

导入数据——执行策略——显示结果
为保证和通达信选股一致,需使用前复权数据
"""
import os
import sys
import time
import pandas as pd
from multiprocessing import Pool, RLock, freeze_support
from rich import print
from rich.table import Table
from rich.console import Console
from tqdm import tqdm

# 导入策略模块
import CeLue  # 原始策略
try:
    import CeLue_improved  # 改进版策略
    USE_IMPROVED = True
    print("[green]✅ 检测到改进版策略，将使用增强筛选[/green]")
except ImportError:
    USE_IMPROVED = False
    print("[yellow]⚠️  未找到改进版策略，使用原始策略[/yellow]")

import func
import user_config as ucfg

# ==================== 配置部分 ====================

start_date = ''
end_date = ''

# 精选股票数量配置
TOP_N_STOCKS = 30  # 最终只选出得分最高的30只股票

# 变量定义
tdxpath = ucfg.tdx['tdx_path']
csvdaypath = ucfg.tdx['pickle']
已选出股票列表 = []  # 策略选出的股票
股票得分字典 = {}  # 存储股票代码和得分 {股票代码: 得分}

要剔除的通达信概念 = ["ST板块", ]
要剔除的通达信行业 = ["T1002", ]

starttime_str = time.strftime("%H:%M:%S", time.localtime())
starttime = time.time()
starttime_tick = time.time()

console = Console()


# ==================== 股票列表生成 ====================

def make_stocklist():
    """生成候选股票列表"""
    stocklist = [i[:-4] for i in os.listdir(ucfg.tdx['csv_lday'])]
    print(f'生成股票列表, 共 {len(stocklist)} 只股票')
    print(f'剔除通达信概念股票: {要剔除的通达信概念}')
    
    tmplist = []
    df = func.get_TDX_blockfilecontent("block_gn.dat")
    if df is not None:
        for i in 要剔除的通达信概念:
            tmplist = tmplist + df.loc[df['blockname'] == i]['code'].tolist()
        stocklist = list(filter(lambda i: i not in tmplist, stocklist))
        print(f"通过概念板块筛选，剔除了 {len(tmplist)} 只股票")
    else:
        print("⚠️ 未找到 block_gn.dat 文件，跳过概念股票筛选")
    
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
    tmplist = []
    for stockcode in stocklist:
        if stockcode[:2] != '68':
            tmplist.append(stockcode)
    stocklist = tmplist
    return stocklist


# ==================== 策略1执行函数 ====================

def run_celue1(stocklist, df_today, tqdm_position=None):
    """执行策略1筛选"""
    if 'single' in sys.argv[1:]:
        tq = tqdm(stocklist[:])
    else:
        tq = tqdm(stocklist[:], leave=False, position=tqdm_position)
    
    for stockcode in tq:
        tq.set_description(stockcode)
        pklfile = csvdaypath + os.sep + stockcode + '.pkl'
        df_stock = pd.read_pickle(pklfile)
        
        if df_today is not None:
            df_stock = func.update_stockquote(stockcode, df_stock, df_today)
        
        df_stock['date'] = pd.to_datetime(df_stock['date'], format='%Y-%m-%d')
        df_stock.set_index('date', drop=False, inplace=True)
        
        # 使用改进版策略1或原始策略1
        if USE_IMPROVED:
            celue1 = CeLue_improved.策略1_增强版(df_stock, start_date=start_date, end_date=end_date, mode='fast')
        else:
            celue1 = CeLue.策略1(df_stock, start_date=start_date, end_date=end_date, mode='fast')
        
        if not celue1:
            stocklist.remove(stockcode)
    
    return stocklist


# ==================== 策略2执行函数(带评分) ====================

def run_celue2_with_score(stocklist, HS300_信号, df_gbbq, df_today, tqdm_position=None):
    """
    执行策略2筛选并评分
    返回: (筛选后的股票列表, 股票得分字典)
    """
    股票得分 = {}
    
    if 'single' in sys.argv[1:]:
        tq = tqdm(stocklist[:])
    else:
        tq = tqdm(stocklist[:], leave=False, position=tqdm_position)
    
    for stockcode in tq:
        tq.set_description(stockcode)
        pklfile = csvdaypath + os.sep + stockcode + '.pkl'
        df_stock = pd.read_pickle(pklfile)
        df_stock['date'] = pd.to_datetime(df_stock['date'], format='%Y-%m-%d')
        df_stock.set_index('date', drop=False, inplace=True)
        
        # 更新实时行情
        if '09:00:00' < time.strftime("%H:%M:%S", time.localtime()) < '16:00:00' \
                and 0 <= time.localtime(time.time()).tm_wday <= 4:
            if not df_today.empty and 'code' in df_today.columns:
                df_today_code = df_today.loc[df_today['code'] == stockcode]
                df_stock = func.update_stockquote(stockcode, df_stock, df_today_code)
            
            # 判断是否在权息日
            now_date = pd.to_datetime(time.strftime("%Y-%m-%d", time.localtime()))
            if now_date in df_gbbq.loc[df_gbbq['code'] == stockcode]['权息日'].to_list():
                cw_dict = func.readall_local_cwfile()
                df_stock = func.make_fq(stockcode, df_stock, df_gbbq, cw_dict)
        
        # 使用改进版策略2(带评分)或原始策略2
        if USE_IMPROVED:
            信号, 得分 = CeLue_improved.策略2_精选版(df_stock, HS300_信号, start_date=start_date, end_date=end_date)
            if 信号:
                股票得分[stockcode] = 得分
            else:
                stocklist.remove(stockcode)
        else:
            celue2 = CeLue.策略2(df_stock, HS300_信号, start_date=start_date, end_date=end_date).iat[-1]
            if celue2:
                股票得分[stockcode] = 50  # 原始策略没有评分,统一给50分
            else:
                stocklist.remove(stockcode)
    
    return stocklist, 股票得分


# ==================== 精选TOP N股票 ====================

def select_top_stocks(股票得分字典, top_n=30):
    """
    从股票得分字典中选出得分最高的N只
    
    参数:
        股票得分字典: {股票代码: 得分}
        top_n: 选出前N只
    
    返回:
        sorted_stocks: [(股票代码, 得分), ...]
    """
    sorted_stocks = sorted(股票得分字典.items(), key=lambda x: x[1], reverse=True)
    return sorted_stocks[:top_n]


# ==================== 显示结果表格 ====================

def display_result_table(selected_stocks, total_time):
    """
    使用Rich库显示精美的结果表格
    
    参数:
        selected_stocks: [(股票代码, 得分), ...]
        total_time: 总用时
    """
    table = Table(title=f"\n[bold cyan]📊 精选股票结果 - TOP {len(selected_stocks)} 只[/bold cyan]", 
                  show_header=True, header_style="bold magenta")
    
    table.add_column("排名", style="cyan", justify="center", width=6)
    table.add_column("股票代码", style="green", justify="center", width=10)
    table.add_column("综合得分", style="yellow", justify="center", width=10)
    table.add_column("评级", style="red", justify="center", width=10)
    
    for idx, (code, score) in enumerate(selected_stocks, 1):
        # 根据得分给出评级
        if score >= 80:
            rating = "⭐⭐⭐⭐⭐"
        elif score >= 70:
            rating = "⭐⭐⭐⭐"
        elif score >= 60:
            rating = "⭐⭐⭐"
        elif score >= 50:
            rating = "⭐⭐"
        else:
            rating = "⭐"
        
        table.add_row(
            str(idx),
            code,
            f"{score:.1f}",
            rating
        )
    
    console.print(table)
    console.print(f"\n[bold green]✅ 选股完成！共用时 {total_time:.2f} 秒[/bold green]")
    console.print(f"[bold yellow]💡 建议: 重点关注得分≥70分的股票[/bold yellow]\n")


# ==================== 主程序 ====================

if __name__ == '__main__':
    # 命令行参数检查
    if 'single' in sys.argv[1:]:
        print(f'[yellow]检测到参数 single, 单进程执行[/yellow]')
    else:
        print(f'[cyan]附带命令行参数 single 单进程执行(默认多进程)[/cyan]')
    
    # 打印配置信息
    print("\n" + "=" * 70)
    print(f"[bold cyan]改进版选股策略配置[/bold cyan]")
    print("=" * 70)
    if USE_IMPROVED:
        print("[green]✓ 策略1: 增强版筛选 (更严格的流动性和质量要求)[/green]")
        print("[green]✓ 策略2: 智能评分系统 (综合考虑5个维度)[/green]")
        print(f"[green]✓ 精选数量: TOP {TOP_N_STOCKS} 只股票[/green]")
    else:
        print("[yellow]✓ 策略1: 原始版本[/yellow]")
        print("[yellow]✓ 策略2: 原始版本[/yellow]")
    print("=" * 70 + "\n")
    
    # 生成候选股票列表
    stocklist = make_stocklist()
    print(f'\n[bold]共 {len(stocklist)} 只候选股票[/bold]\n')
    
    # 加载股改数据
    df_gbbq = pd.read_csv(ucfg.tdx['csv_gbbq'] + '/gbbq.csv', encoding='gbk', dtype={'code': str})
    
    # ========== 大盘判断 ==========
    print('[bold cyan]━━━━━━ 第一步: 大盘环境判断 ━━━━━━[/bold cyan]')
    df_hs300 = pd.read_csv(
        ucfg.tdx['csv_index'] + '/000300.csv',
        index_col=None,
        encoding='gbk',
        dtype={'code': str}
    )
    df_hs300['date'] = pd.to_datetime(df_hs300['date'], format='%Y-%m-%d')
    df_hs300.set_index('date', drop=False, inplace=True)
    
    # 交易时段获取实时行情
    if '09:00:00' < time.strftime("%H:%M:%S", time.localtime()) < '16:00:00':
        df_today = func.get_tdx_lastestquote((1, '000300'))
        df_hs300 = func.update_stockquote('000300', df_hs300, df_today)
        del df_today
    
    HS300_信号 = CeLue.策略HS300(df_hs300)
    
    if HS300_信号.iat[-1]:
        print('[bold red]🚀 沪深300满足买入条件，大盘环境良好！[/bold red]')
    else:
        print('[bold yellow]⚠️  沪深300不满足买入条件，大盘环境一般[/bold yellow]')
        print('[yellow]    将继续选股，但建议谨慎操作或观望[/yellow]')
        HS300_信号.loc[:] = True  # 强制继续选股
    
    # ========== 获取实时行情 ==========
    df_today_tmppath = ucfg.tdx['csv_gbbq'] + '/df_today.pkl'
    if '09:00:00' < time.strftime("%H:%M:%S", time.localtime()) < '16:00:00' \
            and 0 <= time.localtime(time.time()).tm_wday <= 4:
        print(f'\n[cyan]现在是交易时段，正在获取实时行情...[/cyan]')
        if os.path.exists(df_today_tmppath):
            if round(time.time() - os.path.getmtime(df_today_tmppath)) < 600:
                print(f'[green]✓ 使用缓存的实时行情数据[/green]')
                df_today = pd.read_pickle(df_today_tmppath)
            else:
                df_today = func.get_tdx_lastestquote(stocklist)
                df_today.to_pickle(df_today_tmppath, compression=None)
        else:
            df_today = func.get_tdx_lastestquote(stocklist)
            df_today.to_pickle(df_today_tmppath, compression=None)
    else:
        try:
            os.remove(df_today_tmppath)
        except FileNotFoundError:
            pass
        df_today = None
    
    # ========== 策略1筛选 ==========
    print(f'\n[bold cyan]━━━━━━ 第二步: 策略1基础筛选 ━━━━━━[/bold cyan]')
    if USE_IMPROVED:
        print('[green]使用增强版策略1: 更严格的流动性和质量标准[/green]')
    starttime_tick = time.time()
    
    if 'single' in sys.argv[1:]:
        stocklist = run_celue1(stocklist, df_today)
    else:
        # 多进程处理
        if os.cpu_count() > 8:
            t_num = int(os.cpu_count() / 1.5)
        else:
            t_num = os.cpu_count() - 2
        
        freeze_support()
        tqdm.set_lock(RLock())
        p = Pool(processes=t_num, initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),))
        pool_result = []
        
        for i in range(0, t_num):
            div = int(len(stocklist) / t_num)
            mod = len(stocklist) % t_num
            if i + 1 != t_num:
                pool_result.append(p.apply_async(run_celue1, args=(stocklist[i * div:(i + 1) * div], df_today, i,)))
            else:
                pool_result.append(p.apply_async(run_celue1, args=(stocklist[i * div:(i + 1) * div + mod], df_today, i,)))
        
        p.close()
        p.join()
        
        stocklist = []
        for i in pool_result:
            stocklist = stocklist + i.get()
    
    print(f'[bold green]✓ 策略1完成: 筛选出 {len(stocklist)} 只股票, 用时 {(time.time() - starttime_tick):.2f} 秒[/bold green]')
    
    # ========== 策略2筛选+评分 ==========
    print(f'\n[bold cyan]━━━━━━ 第三步: 策略2精选+评分 ━━━━━━[/bold cyan]')
    if USE_IMPROVED:
        print('[green]使用智能评分系统: 综合5个维度为每只股票打分[/green]')
    
    # 确保有实时行情数据
    if '09:00:00' < time.strftime("%H:%M:%S", time.localtime()) < '16:00:00' and 'df_today' not in dir():
        df_today = func.get_tdx_lastestquote(stocklist)
    
    starttime_tick = time.time()
    
    if 'single' in sys.argv[1:]:
        stocklist, 股票得分字典 = run_celue2_with_score(stocklist, HS300_信号, df_gbbq, df_today)
    else:
        # 多进程处理
        t_num = os.cpu_count() - 2
        freeze_support()
        tqdm.set_lock(RLock())
        p = Pool(processes=t_num, initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),))
        pool_result = []
        
        for i in range(0, t_num):
            div = int(len(stocklist) / t_num)
            mod = len(stocklist) % t_num
            if i + 1 != t_num:
                pool_result.append(p.apply_async(run_celue2_with_score, 
                                                args=(stocklist[i * div:(i + 1) * div], HS300_信号, df_gbbq, df_today, i,)))
            else:
                pool_result.append(p.apply_async(run_celue2_with_score,
                                                args=(stocklist[i * div:(i + 1) * div + mod], HS300_信号, df_gbbq, df_today, i,)))
        
        p.close()
        p.join()
        
        stocklist = []
        股票得分字典 = {}
        for i in pool_result:
            result_list, result_scores = i.get()
            stocklist = stocklist + result_list
            股票得分字典.update(result_scores)
    
    print(f'[bold green]✓ 策略2完成: 筛选出 {len(stocklist)} 只股票, 用时 {(time.time() - starttime_tick):.2f} 秒[/bold green]')
    
    # ========== 最终精选 ==========
    print(f'\n[bold cyan]━━━━━━ 第四步: 智能精选TOP {TOP_N_STOCKS} ━━━━━━[/bold cyan]')
    
    if len(股票得分字典) == 0:
        print('[bold red]❌ 很遗憾，没有找到符合条件的股票！[/bold red]')
        print('[yellow]建议: 可能当前大盘环境不佳，或者策略条件过于严格[/yellow]')
    else:
        # 选出得分最高的股票
        top_stocks = select_top_stocks(股票得分字典, top_n=min(TOP_N_STOCKS, len(股票得分字典)))
        
        # 显示结果表格
        display_result_table(top_stocks, time.time() - starttime)
        
        # 输出股票代码列表（方便复制）
        final_codes = [code for code, score in top_stocks]
        print(f"[bold]股票代码列表（可直接复制）：[/bold]")
        print(final_codes)
        
        # 保存结果到文件
        result_file = 'selected_stocks.txt'
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"选股时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}\n")
            f.write(f"总用时: {(time.time() - starttime):.2f} 秒\n")
            f.write(f"选出股票数: {len(top_stocks)} 只\n")
            f.write("\n排名\t股票代码\t得分\n")
            for idx, (code, score) in enumerate(top_stocks, 1):
                f.write(f"{idx}\t{code}\t{score:.1f}\n")
        print(f"\n[green]✓ 结果已保存到: {result_file}[/green]")
