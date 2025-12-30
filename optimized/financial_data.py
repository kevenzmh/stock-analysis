#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
财务数据下载模块 - 优化版
负责下载和更新通达信财务数据

作者: wking (原作者)
优化: 2024
"""

import os
import time
import hashlib
import zipfile
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import pytdx.reader.gbbq_reader

from .config import Config
from .logger import get_logger
from .downloader import Downloader, verify_zip_file
from .data_reader import FinancialDataReader

logger = get_logger()


class FinancialDataManager:
    """财务数据管理器"""
    
    # 通达信财务数据URL
    TDX_FIN_URL_BASE = "http://down.tdx.com.cn:8001/tdxfin/"
    TDX_FIN_LIST_URL = "http://down.tdx.com.cn:8001/tdxfin/gpcw.txt"
    
    def __init__(self, config: Config):
        """
        初始化财务数据管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.downloader = Downloader(timeout=60, max_retries=3)
        self.cw_dir = Path(config.paths.tdx_path) / "vipdoc" / "cw"
        self.export_dir = Path(config.paths.csv_cw)
        
        # 确保目录存在
        self.cw_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def get_server_file_list(self) -> pd.DataFrame:
        """
        获取服务器端文件列表
        
        Returns:
            DataFrame包含filename, md5, filesize列
        """
        logger.info("获取通达信服务器文件列表...")
        
        try:
            response = self.downloader.session.get(
                self.TDX_FIN_LIST_URL, 
                timeout=30
            )
            response.raise_for_status()
            
            # 解析文件列表
            lines = response.text.strip().split('\r\n')
            data = [line.strip().split(',') for line in lines]
            df = pd.DataFrame(data, columns=['filename', 'md5', 'filesize'])
            
            logger.info(f"获取到 {len(df)} 个财务文件信息")
            return df
            
        except Exception as e:
            logger.exception(f"获取文件列表失败: {e}")
            raise
    
    def get_local_file_list(self, ext: str = 'zip') -> List[str]:
        """
        获取本地文件列表
        
        Args:
            ext: 文件扩展名
            
        Returns:
            文件名列表
        """
        pattern = f"gpcw*.{ext}"
        files = list(self.cw_dir.glob(pattern))
        return [f.name for f in files]
    
    def calculate_file_md5(self, file_path: Path) -> str:
        """
        计算文件MD5
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5值
        """
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def download_file(self, filename: str) -> bool:
        """
        下载单个文件
        
        Args:
            filename: 文件名
            
        Returns:
            是否成功
        """
        url = self.TDX_FIN_URL_BASE + filename
        save_path = self.cw_dir / filename
        
        logger.info(f"下载文件: {filename}")
        
        success = self.downloader.download(
            url, 
            str(save_path),
            verify_func=verify_zip_file
        )
        
        return success
    
    def extract_and_convert(self, zip_filename: str) -> bool:
        """
        解压ZIP并转换为PKL格式
        
        Args:
            zip_filename: ZIP文件名
            
        Returns:
            是否成功
        """
        zip_path = self.cw_dir / zip_filename
        dat_filename = zip_filename[:-4] + '.dat'
        dat_path = self.cw_dir / dat_filename
        pkl_filename = zip_filename[:-4] + '.pkl'
        pkl_path = self.export_dir / pkl_filename
        
        try:
            # 解压ZIP文件
            logger.info(f"解压文件: {zip_filename}")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(self.cw_dir)
            
            # 检查DAT文件是否存在
            if not dat_path.exists():
                logger.error(f"DAT文件不存在: {dat_filename}")
                return False
            
            # 读取DAT文件并转换为PKL
            logger.info(f"转换文件: {dat_filename} -> {pkl_filename}")
            reader = FinancialDataReader()
            df = reader.read_financial_data(str(dat_path))
            df.to_pickle(pkl_path, compression=None)
            
            logger.info(f"文件处理完成: {pkl_filename}")
            return True
            
        except Exception as e:
            logger.exception(f"文件处理失败: {e}")
            return False
    
    def check_and_download_missing(self) -> Tuple[int, int]:
        """
        检查并下载缺失的文件
        
        Returns:
            (下载成功数, 下载失败数)
        """
        logger.info("检查缺失的财务文件...")
        
        server_files = self.get_server_file_list()
        local_files = self.get_local_file_list('zip')
        
        missing_files = []
        for filename in server_files['filename']:
            if filename not in local_files:
                missing_files.append(filename)
        
        if not missing_files:
            logger.info("没有缺失的文件")
            return 0, 0
        
        logger.info(f"发现 {len(missing_files)} 个缺失文件")
        
        success_count = 0
        fail_count = 0
        
        for filename in missing_files:
            if self.download_file(filename):
                if self.extract_and_convert(filename):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
        
        return success_count, fail_count
    
    def check_and_update_files(self) -> Tuple[int, int]:
        """
        检查并更新需要更新的文件
        
        Returns:
            (更新成功数, 更新失败数)
        """
        logger.info("检查需要更新的财务文件...")
        
        server_files = self.get_server_file_list()
        local_files = self.get_local_file_list('zip')
        
        # 创建MD5映射
        md5_map = dict(zip(server_files['filename'], server_files['md5']))
        
        update_files = []
        for filename in local_files:
            file_path = self.cw_dir / filename
            local_md5 = self.calculate_file_md5(file_path)
            server_md5 = md5_map.get(filename, '')
            
            if local_md5 != server_md5:
                update_files.append(filename)
        
        if not update_files:
            logger.info("所有文件都是最新的")
            return 0, 0
        
        logger.info(f"发现 {len(update_files)} 个需要更新的文件")
        
        success_count = 0
        fail_count = 0
        
        for filename in update_files:
            # 删除旧文件
            file_path = self.cw_dir / filename
            file_path.unlink(missing_ok=True)
            
            # 下载新文件
            if self.download_file(filename):
                if self.extract_and_convert(filename):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1
        
        return success_count, fail_count
    
    def export_missing_pkl(self) -> int:
        """
        导出缺失的PKL文件
        
        Returns:
            导出的文件数
        """
        logger.info("检查缺失的PKL文件...")
        
        dat_files = self.get_local_file_list('dat')
        pkl_files = [f.name for f in self.export_dir.glob('*.pkl')]
        
        export_count = 0
        reader = FinancialDataReader()
        
        for dat_filename in dat_files:
            pkl_filename = dat_filename[:-4] + '.pkl'
            
            if pkl_filename not in pkl_files:
                logger.info(f"导出PKL文件: {pkl_filename}")
                
                try:
                    dat_path = self.cw_dir / dat_filename
                    pkl_path = self.export_dir / pkl_filename
                    
                    df = reader.read_financial_data(str(dat_path))
                    df.to_pickle(pkl_path, compression=None)
                    export_count += 1
                    
                except Exception as e:
                    logger.exception(f"导出失败: {e}")
        
        if export_count > 0:
            logger.info(f"导出了 {export_count} 个PKL文件")
        else:
            logger.info("没有需要导出的文件")
        
        return export_count
    
    def process_stock_changes(self) -> bool:
        """
        处理股本变迁文件
        
        Returns:
            是否成功
        """
        logger.info("处理股本变迁文件...")
        
        try:
            category_map = {
                '1': '除权除息', '2': '送配股上市', '3': '非流通股上市', 
                '4': '未知股本变动', '5': '股本变化', '6': '增发新股', 
                '7': '股份回购', '8': '增发新股上市', '9': '转配股上市', 
                '10': '可转债上市', '11': '扩缩股', '12': '非流通股缩股', 
                '13': '送认购权证', '14': '送认沽权证'
            }
            
            # 读取股本变迁文件
            gbbq_path = Path(self.config.paths.tdx_path) / 'T0002' / 'hq_cache' / 'gbbq'
            df_gbbq = pytdx.reader.gbbq_reader.GbbqReader().get_df(str(gbbq_path))
            
            # 处理数据
            df_gbbq = df_gbbq.drop(columns=['market'])
            df_gbbq.columns = ['code', '权息日', '类别',
                              '分红-前流通盘', '配股价-前总股本', 
                              '送转股-后流通盘', '配股-后总股本']
            
            df_gbbq['类别'] = df_gbbq['类别'].astype('object')
            df_gbbq['code'] = df_gbbq['code'].astype('object')
            
            # 映射类别
            for i in range(len(df_gbbq)):
                category_code = str(df_gbbq.iloc[i]['类别'])
                df_gbbq.iloc[i, df_gbbq.columns.get_loc('类别')] = \
                    category_map.get(category_code, f'未知类别{category_code}')
            
            # 保存文件
            output_path = Path(self.config.paths.csv_gbbq) / 'gbbq.csv'
            df_gbbq.to_csv(output_path, encoding='gbk', index=False)
            
            logger.info(f"股本变迁文件处理完成: {output_path}")
            return True
            
        except Exception as e:
            logger.exception(f"股本变迁文件处理失败: {e}")
            return False
    
    def update_all(self) -> dict:
        """
        执行完整更新流程
        
        Returns:
            更新统计信息
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("开始更新财务数据")
        logger.info("=" * 60)
        
        stats = {
            'download_success': 0,
            'download_fail': 0,
            'update_success': 0,
            'update_fail': 0,
            'export_count': 0,
            'gbbq_success': False,
        }
        
        try:
            # 1. 下载缺失文件
            success, fail = self.check_and_download_missing()
            stats['download_success'] = success
            stats['download_fail'] = fail
            
            # 2. 更新现有文件
            success, fail = self.check_and_update_files()
            stats['update_success'] = success
            stats['update_fail'] = fail
            
            # 3. 导出缺失的PKL文件
            stats['export_count'] = self.export_missing_pkl()
            
            # 4. 处理股本变迁文件
            stats['gbbq_success'] = self.process_stock_changes()
            
        except Exception as e:
            logger.exception(f"更新过程出错: {e}")
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info("财务数据更新完成")
        logger.info(f"下载成功: {stats['download_success']}, 失败: {stats['download_fail']}")
        logger.info(f"更新成功: {stats['update_success']}, 失败: {stats['update_fail']}")
        logger.info(f"导出PKL: {stats['export_count']}")
        logger.info(f"股本变迁: {'成功' if stats['gbbq_success'] else '失败'}")
        logger.info(f"总耗时: {elapsed:.2f} 秒")
        logger.info("=" * 60)
        
        return stats
    
    def __del__(self):
        """析构函数"""
        self.downloader.close()


if __name__ == '__main__':
    # 测试财务数据管理器
    from .config import load_legacy_config
    
    config = load_legacy_config()
    manager = FinancialDataManager(config)
    
    # 执行更新
    stats = manager.update_all()
    
    print("\n更新统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
