#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据下载模块 - 优化版
提供稳定可靠的文件下载功能

作者: 优化版 2024
"""

import os
import time
import hashlib
import zipfile
from pathlib import Path
from typing import Optional, Callable
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logger import get_logger

logger = get_logger()


class DownloadError(Exception):
    """下载异常"""
    pass


class Downloader:
    """文件下载器"""
    
    def __init__(self, 
                 timeout: int = 30,
                 max_retries: int = 3,
                 chunk_size: int = 8192):
        """
        初始化下载器
        
        Args:
            timeout: 超时时间(秒)
            max_retries: 最大重试次数
            chunk_size: 下载块大小
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        
        # 创建会话,配置重试策略
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # 重试延迟递增
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def download(self,
                 url: str,
                 save_path: str,
                 progress_callback: Optional[Callable[[int, int], None]] = None,
                 verify_func: Optional[Callable[[str], bool]] = None) -> bool:
        """
        下载文件
        
        Args:
            url: 下载链接
            save_path: 保存路径
            progress_callback: 进度回调函数(已下载,总大小)
            verify_func: 验证函数,返回True表示文件有效
            
        Returns:
            是否下载成功
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        for retry in range(self.max_retries):
            try:
                logger.info(f"下载文件 ({retry + 1}/{self.max_retries}): {url}")
                
                # 发起请求
                response = self.session.get(url, stream=True, timeout=self.timeout)
                response.raise_for_status()
                
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                
                # 下载文件
                downloaded = 0
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 回调进度
                            if progress_callback:
                                progress_callback(downloaded, total_size)
                
                logger.info(f"下载完成: {save_path.name}")
                
                # 验证文件
                if verify_func and not verify_func(str(save_path)):
                    logger.error(f"文件验证失败: {save_path.name}")
                    save_path.unlink(missing_ok=True)
                    
                    if retry < self.max_retries - 1:
                        wait_time = 2 ** retry  # 指数退避
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise DownloadError("文件验证失败且重试次数已用尽")
                
                return True
                
            except requests.exceptions.RequestException as e:
                logger.error(f"下载出错: {e}")
                save_path.unlink(missing_ok=True)
                
                if retry < self.max_retries - 1:
                    wait_time = 2 ** retry
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"下载失败,已重试 {self.max_retries} 次")
                    return False
            
            except Exception as e:
                logger.exception(f"下载异常: {e}")
                save_path.unlink(missing_ok=True)
                return False
        
        return False
    
    def download_batch(self,
                      urls: list,
                      save_dir: str,
                      verify_func: Optional[Callable[[str], bool]] = None) -> dict:
        """
        批量下载文件
        
        Args:
            urls: URL列表
            save_dir: 保存目录
            verify_func: 验证函数
            
        Returns:
            下载结果字典 {url: success}
        """
        results = {}
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        for url in urls:
            filename = url.split('/')[-1]
            save_path = save_dir / filename
            
            success = self.download(url, str(save_path), verify_func=verify_func)
            results[url] = success
        
        return results
    
    def close(self):
        """关闭会话"""
        self.session.close()


def verify_zip_file(file_path: str) -> bool:
    """
    验证ZIP文件完整性
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为有效的ZIP文件
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as zf:
            # 测试ZIP文件完整性
            bad_file = zf.testzip()
            if bad_file:
                logger.error(f"ZIP文件损坏: {bad_file}")
                return False
        return True
    except (zipfile.BadZipFile, Exception) as e:
        logger.error(f"ZIP文件验证失败: {e}")
        return False


def calculate_md5(file_path: str) -> str:
    """
    计算文件MD5值
    
    Args:
        file_path: 文件路径
        
    Returns:
        MD5值(十六进制字符串)
    """
    md5_hash = hashlib.md5()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()


def download_with_progress(url: str, 
                           save_path: str,
                           verify_zip: bool = True) -> bool:
    """
    下载文件(带进度显示)
    
    Args:
        url: 下载链接
        save_path: 保存路径
        verify_zip: 是否验证ZIP文件
        
    Returns:
        是否下载成功
    """
    from tqdm import tqdm
    
    downloader = Downloader()
    
    # 进度条
    pbar = None
    
    def progress_callback(downloaded: int, total: int):
        nonlocal pbar
        if pbar is None and total > 0:
            pbar = tqdm(total=total, unit='B', unit_scale=True, 
                       desc=os.path.basename(save_path))
        if pbar:
            pbar.update(downloaded - pbar.n)
    
    # 验证函数
    verify_func = verify_zip_file if verify_zip else None
    
    success = downloader.download(url, save_path, 
                                  progress_callback=progress_callback,
                                  verify_func=verify_func)
    
    if pbar:
        pbar.close()
    
    downloader.close()
    return success


if __name__ == '__main__':
    # 测试下载功能
    test_url = "http://down.tdx.com.cn:8001/tdxfin/gpcw20241231.zip"
    test_path = "test_download.zip"
    
    print("测试文件下载...")
    success = download_with_progress(test_url, test_path, verify_zip=True)
    
    if success:
        print("✓ 下载成功")
        # 清理测试文件
        os.remove(test_path)
    else:
        print("✗ 下载失败")
