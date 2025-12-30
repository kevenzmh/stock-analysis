#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
读取通达信专业财务数据文件 /vipdoc/cw/gpcw?????.dat
修复版：增加下载验证和重试机制

作者：wking [http://wkings.net]
修复：Claude
"""

import os
import time
import requests
import hashlib
import zipfile
import zlib
import pandas as pd
import pytdx.reader.gbbq_reader

import func
import user_config as ucfg


def download_file_simple(url, local_path, max_retries=3):
    """
    简单的文件下载函数，带重试机制和完整性验证
    :param url: 下载链接
    :param local_path: 本地保存路径
    :param max_retries: 最大重试次数
    :return: True表示成功，False表示失败
    """
    for retry in range(max_retries):
        try:
            print(f'  尝试下载 ({retry + 1}/{max_retries})...')
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # 写入文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 验证是否为有效的ZIP文件
            try:
                with zipfile.ZipFile(local_path, 'r') as test_zip:
                    test_zip.testzip()  # 测试ZIP文件完整性
                print(f'  下载成功并验证完整')
                return True
            except (zipfile.BadZipFile, zlib.error) as e:
                print(f'  ZIP文件损坏: {e}')
                if os.path.exists(local_path):
                    os.remove(local_path)
                if retry < max_retries - 1:
                    print(f'  等待3秒后重试...')
                    time.sleep(3)
                continue
                
        except Exception as e:
            print(f'  下载出错: {e}')
            if os.path.exists(local_path):
                os.remove(local_path)
            if retry < max_retries - 1:
                print(f'  等待3秒后重试...')
                time.sleep(3)
            continue
    
    return False


# 变量定义
tdxpath = ucfg.tdx['tdx_path']
starttime_str = time.strftime("%H:%M:%S", time.localtime())
starttime = time.time()

# 主程序开始
# 目录不存在则创建
os.makedirs(ucfg.tdx['csv_cw'], exist_ok=True)
os.makedirs(ucfg.tdx['tdx_path'] + os.sep + "vipdoc" + os.sep + "cw", exist_ok=True)

# 本机专业财务文件和通达信服务器对比，检查更新

print('正在获取通达信服务器文件列表...')
# 下载通达信服务器文件校检信息txt
tdx_txt_url = 'http://down.tdx.com.cn:8001/tdxfin/gpcw.txt'
try:
    tdx_txt_df = func.dowload_url(tdx_txt_url)  # 下载gpcw.txt
    tdx_txt_df = tdx_txt_df.text.strip().split('\r\n')  # 分割行
    tdx_txt_df = [l.strip().split(",") for l in tdx_txt_df]  # 用,分割，二维列表
    tdx_txt_df = pd.DataFrame(tdx_txt_df, columns=['filename', 'md5', 'filesize'])  # 转为df格式，好比较
    print(f'获取到 {len(tdx_txt_df)} 个财务文件信息')
except Exception as e:
    print(f'获取文件列表失败: {e}')
    print('程序退出')
    exit(1)

# 检查本机通达信dat文件是否有缺失
local_zipfile_list = func.list_localTDX_cwfile('zip')  # 获取本机已有文件
print(f'本机已有 {len(local_zipfile_list)} 个ZIP文件')

for df_filename in tdx_txt_df['filename'].tolist():
    starttime_tick = time.time()
    if df_filename not in local_zipfile_list:
        print(f'\n{df_filename} 本机没有，开始下载')
        tdx_zipfile_url = 'http://down.tdx.com.cn:8001/tdxfin/' + df_filename
        local_zipfile_path = ucfg.tdx['tdx_path'] + os.sep + "vipdoc" + os.sep + "cw" + os.sep + df_filename
        
        # 使用简单的下载函数替代多线程下载
        if download_file_simple(tdx_zipfile_url, local_zipfile_path):
            try:
                # 解压文件
                with zipfile.ZipFile(local_zipfile_path, 'r') as zipobj:
                    zipobj.extractall(ucfg.tdx['tdx_path'] + os.sep + "vipdoc" + os.sep + "cw")
                
                # 读取DAT文件并保存为PKL
                local_datfile_path = local_zipfile_path[:-4] + ".dat"
                if os.path.exists(local_datfile_path):
                    df = func.historyfinancialreader(local_datfile_path)
                    csvpath = ucfg.tdx['csv_cw'] + os.sep + df_filename[:-4] + ".pkl"
                    df.to_pickle(csvpath, compression=None)
                    print(f'{df_filename} 完成更新 用时 {(time.time() - starttime_tick):>5.2f} 秒')
                else:
                    print(f'警告: DAT文件不存在 {local_datfile_path}')
            except Exception as e:
                print(f'处理文件失败: {e}')
                if os.path.exists(local_zipfile_path):
                    os.remove(local_zipfile_path)
        else:
            print(f'{df_filename} 下载失败，跳过')

# 检查本机通达信zip文件是否需要更新
print('\n检查本机文件是否需要更新...')
local_zipfile_list = func.list_localTDX_cwfile('zip')  # 获取本机已有文件
for zipfile_filename in local_zipfile_list:
    starttime_tick = time.time()
    local_zipfile_path = ucfg.tdx['tdx_path'] + os.sep + "vipdoc" + os.sep + "cw" + os.sep + zipfile_filename
    
    try:
        with open(local_zipfile_path, 'rb') as fobj:  # 读取本机zip文件，计算md5
            file_content = fobj.read()
            file_md5 = hashlib.md5(file_content).hexdigest()
    except Exception as e:
        print(f'读取文件 {zipfile_filename} 失败: {e}')
        continue
    
    if file_md5 not in tdx_txt_df['md5'].tolist():  # 本机zip文件的md5与服务器端不一致
        print(f'\n{zipfile_filename} 需要更新，开始下载')
        os.remove(local_zipfile_path)  # 删除本机zip文件
        tdx_zipfile_url = 'http://down.tdx.com.cn:8001/tdxfin/' + zipfile_filename
        
        if download_file_simple(tdx_zipfile_url, local_zipfile_path):
            try:
                # 解压文件
                with zipfile.ZipFile(local_zipfile_path, 'r') as zipobj:
                    zipobj.extractall(ucfg.tdx['tdx_path'] + os.sep + "vipdoc" + os.sep + "cw")
                
                # 读取DAT文件并保存为PKL
                local_datfile_path = local_zipfile_path[:-4] + ".dat"
                if os.path.exists(local_datfile_path):
                    df = func.historyfinancialreader(local_datfile_path)
                    csvpath = ucfg.tdx['csv_cw'] + os.sep + zipfile_filename[:-4] + ".pkl"
                    df.to_pickle(csvpath, compression=None)
                    print(f'{zipfile_filename} 完成更新 用时 {(time.time() - starttime_tick):>5.2f} 秒')
                else:
                    print(f'警告: DAT文件不存在 {local_datfile_path}')
            except Exception as e:
                print(f'处理文件失败: {e}')
                if os.path.exists(local_zipfile_path):
                    os.remove(local_zipfile_path)
        else:
            print(f'{zipfile_filename} 更新失败')

# 检查本机财报导出文件是否存在
print('\n检查本机财报导出文件...')
cwfile_list = os.listdir(ucfg.tdx['csv_cw'])  # cw目录 生成文件名列表
local_datfile_list = func.list_localTDX_cwfile('dat')  # 获取本机已有文件
for filename in local_datfile_list:
    starttime_tick = time.time()
    filenamepkl = filename[:-4] + '.pkl'
    pklpath = ucfg.tdx['csv_cw'] + os.sep + filenamepkl
    filenamedat = filename[:-4] + '.dat'
    datpath = ucfg.tdx['tdx_path'] + os.sep + "vipdoc" + os.sep + "cw" + os.sep + filenamedat
    
    if filenamepkl not in cwfile_list:
        print(f'{filename} 本机没有PKL文件，需要导出')
        try:
            df = func.historyfinancialreader(datpath)
            df.to_pickle(pklpath, compression=None)
            print(f'{filename} 完成导出 用时 {(time.time() - starttime_tick):>5.2f} 秒')
        except Exception as e:
            print(f'导出失败: {e}')

print(f'\n专业财务文件检查更新完成 已用 {(time.time() - starttime):>5.2f} 秒')

# 解密通达信股本变迁文件
starttime_tick = time.time()
category = {
    '1': '除权除息', '2': '送配股上市', '3': '非流通股上市', '4': '未知股本变动', '5': '股本变化',
    '6': '增发新股', '7': '股份回购', '8': '增发新股上市', '9': '转配股上市', '10': '可转债上市',
    '11': '扩缩股', '12': '非流通股缩股', '13': '送认购权证', '14': '送认沽权证'}

print('\n解密通达信gbbq股本变迁文件')
filepath = ucfg.tdx['tdx_path'] + '/T0002/hq_cache/gbbq'
try:
    df_gbbq = pytdx.reader.gbbq_reader.GbbqReader().get_df(filepath)
    df_gbbq.drop(columns=['market'], inplace=True)
    df_gbbq.columns = ['code', '权息日', '类别',
                       '分红-前流通盘', '配股价-前总股本', '送转股-后流通盘', '配股-后总股本']
    df_gbbq['类别'] = df_gbbq['类别'].astype('object')
    df_gbbq['code'] = df_gbbq['code'].astype('object')
    for i in range(df_gbbq.shape[0]):
        df_gbbq.iat[i, df_gbbq.columns.get_loc("类别")] = category[str(df_gbbq.iat[i, df_gbbq.columns.get_loc("类别")])]
    df_gbbq.to_csv(ucfg.tdx['csv_gbbq'] + os.sep + 'gbbq.csv', encoding='gbk', index=False)
    print(f'股本变迁解密完成 用时 {(time.time() - starttime_tick):>5.2f} 秒')
except Exception as e:
    print(f'股本变迁文件处理失败: {e}')

print(f'\n全部完成 用时 {(time.time() - starttime):>5.2f} 秒 程序结束')
