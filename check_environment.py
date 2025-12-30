#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境检查脚本
检查项目运行所需的所有依赖和配置

运行方式: python check_environment.py
"""

import sys
import os
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")

def check_python_version():
    """检查Python版本"""
    print("\n" + "="*60)
    print("1. 检查Python版本")
    print("="*60)
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python版本: {version_str}")
        return True
    else:
        print_error(f"Python版本过低: {version_str}")
        print_info("需要Python 3.8或更高版本")
        return False

def check_packages():
    """检查必需的包"""
    print("\n" + "="*60)
    print("2. 检查Python依赖包")
    print("="*60)
    
    required_packages = {
        'pandas': '1.2.3',
        'pytdx': '1.72',
        'pyecharts': '1.9.0',
        'rqalpha': '4.2.5',
        'tqdm': None,
        'rich': None,
        'retry': None,
        'requests': None,
        'numpy': None,
        'talib': '0.4.19',
    }
    
    all_ok = True
    
    for package, recommended_version in required_packages.items():
        try:
            if package == 'talib':
                import talib
                version = talib.__version__ if hasattr(talib, '__version__') else 'unknown'
            else:
                mod = __import__(package)
                version = mod.__version__ if hasattr(mod, '__version__') else 'unknown'
            
            if recommended_version:
                print_success(f"{package}: {version} (推荐: {recommended_version})")
            else:
                print_success(f"{package}: {version}")
        except ImportError:
            print_error(f"{package}: 未安装")
            if recommended_version:
                print_info(f"  安装命令: pip install {package}=={recommended_version}")
            else:
                print_info(f"  安装命令: pip install {package}")
            all_ok = False
    
    return all_ok

def check_config():
    """检查配置文件"""
    print("\n" + "="*60)
    print("3. 检查配置文件")
    print("="*60)
    
    if not os.path.exists('user_config.py'):
        print_error("user_config.py 不存在")
        return False
    
    try:
        import user_config as ucfg
        print_success("user_config.py 加载成功")
        
        # 检查通达信路径
        tdx_path = ucfg.tdx.get('tdx_path', '')
        if not tdx_path:
            print_error("tdx_path 未配置")
            return False
        
        if os.path.exists(tdx_path):
            print_success(f"通达信路径存在: {tdx_path}")
        else:
            print_error(f"通达信路径不存在: {tdx_path}")
            print_info("请安装通达信软件并修改user_config.py中的tdx_path")
            return False
        
        # 检查数据目录配置
        data_dirs = {
            'csv_lday': '日线数据目录',
            'pickle': 'Pickle数据目录',
            'csv_index': '指数数据目录',
            'csv_cw': '财务数据目录',
            'csv_gbbq': '股本变迁目录',
        }
        
        for key, desc in data_dirs.items():
            path = ucfg.tdx.get(key, '')
            if path:
                print_info(f"{desc}: {path}")
                if not os.path.exists(path):
                    print_warning(f"  目录不存在，将自动创建")
                    try:
                        Path(path).mkdir(parents=True, exist_ok=True)
                        print_success(f"  目录创建成功: {path}")
                    except Exception as e:
                        print_error(f"  目录创建失败: {e}")
            else:
                print_warning(f"{desc} 未配置")
        
        return True
        
    except Exception as e:
        print_error(f"加载配置文件失败: {e}")
        return False

def check_tdx_data():
    """检查通达信数据"""
    print("\n" + "="*60)
    print("4. 检查通达信数据")
    print("="*60)
    
    try:
        import user_config as ucfg
        tdx_path = ucfg.tdx.get('tdx_path', '')
        
        if not tdx_path or not os.path.exists(tdx_path):
            print_error("通达信路径无效")
            return False
        
        # 检查日线数据目录
        lday_path_sh = os.path.join(tdx_path, 'vipdoc', 'sh', 'lday')
        lday_path_sz = os.path.join(tdx_path, 'vipdoc', 'sz', 'lday')
        
        if os.path.exists(lday_path_sh):
            sh_files = [f for f in os.listdir(lday_path_sh) if f.endswith('.day')]
            print_success(f"上海市场日线数据: {len(sh_files)} 个文件")
        else:
            print_error(f"上海市场日线数据目录不存在: {lday_path_sh}")
        
        if os.path.exists(lday_path_sz):
            sz_files = [f for f in os.listdir(lday_path_sz) if f.endswith('.day')]
            print_success(f"深圳市场日线数据: {len(sz_files)} 个文件")
        else:
            print_error(f"深圳市场日线数据目录不存在: {lday_path_sz}")
        
        # 检查财务数据目录
        cw_path = os.path.join(tdx_path, 'vipdoc', 'cw')
        if os.path.exists(cw_path):
            dat_files = [f for f in os.listdir(cw_path) if f.endswith('.dat')]
            print_success(f"财务数据文件: {len(dat_files)} 个文件")
        else:
            print_warning(f"财务数据目录不存在: {cw_path}")
        
        # 检查股本变迁文件
        gbbq_path = os.path.join(tdx_path, 'T0002', 'hq_cache', 'gbbq')
        if os.path.exists(gbbq_path):
            print_success(f"股本变迁文件存在: {gbbq_path}")
        else:
            print_warning(f"股本变迁文件不存在: {gbbq_path}")
        
        return True
        
    except Exception as e:
        print_error(f"检查通达信数据失败: {e}")
        return False

def check_strategy_file():
    """检查策略文件"""
    print("\n" + "="*60)
    print("5. 检查策略文件")
    print("="*60)
    
    if os.path.exists('CeLue.py'):
        print_success("CeLue.py 存在")
        return True
    elif os.path.exists('celue.py'):
        print_warning("celue.py 存在 (建议改名为 CeLue.py)")
        return True
    else:
        print_error("策略文件不存在 (CeLue.py 或 celue.py)")
        print_info("请复制 CeLue模板.py 并重命名为 CeLue.py")
        print_info("命令: copy CeLue模板.py CeLue.py")
        return False

def check_core_files():
    """检查核心文件"""
    print("\n" + "="*60)
    print("6. 检查核心文件")
    print("="*60)
    
    core_files = {
        'func.py': '通用函数库',
        'func_TDX.py': '通达信函数库',
        'readTDX_cw.py': '财务数据更新',
        'readTDX_lday.py': '日线数据更新',
        'xuangu.py': '选股脚本',
    }
    
    all_ok = True
    for file, desc in core_files.items():
        if os.path.exists(file):
            print_success(f"{file}: {desc}")
        else:
            print_error(f"{file}: 缺失 ({desc})")
            all_ok = False
    
    return all_ok

def check_optimized_module():
    """检查优化模块"""
    print("\n" + "="*60)
    print("7. 检查优化模块 (可选)")
    print("="*60)
    
    if os.path.exists('optimized'):
        print_success("优化模块目录存在")
        
        opt_files = [
            '__init__.py',
            'config.py',
            'logger.py',
            'downloader.py',
            'data_reader.py',
            'financial_data.py',
        ]
        
        for file in opt_files:
            path = os.path.join('optimized', file)
            if os.path.exists(path):
                print_success(f"  {file}")
            else:
                print_warning(f"  {file} 缺失")
        
        return True
    else:
        print_warning("优化模块不存在 (可选)")
        return True

def print_summary(checks):
    """打印检查摘要"""
    print("\n" + "="*60)
    print("检查摘要")
    print("="*60)
    
    total = len(checks)
    passed = sum(checks.values())
    
    for name, result in checks.items():
        status = "✓" if result else "✗"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.END} {name}")
    
    print("\n" + "-"*60)
    print(f"总计: {passed}/{total} 项检查通过")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ 所有检查通过! 项目可以运行{Colors.END}")
        print("\n下一步:")
        print("  1. python readTDX_cw.py     # 更新财务数据")
        print("  2. python readTDX_lday.py   # 生成日线数据")
        print("  3. python xuangu.py         # 运行选股")
    else:
        print(f"\n{Colors.RED}✗ 有 {total - passed} 项检查未通过{Colors.END}")
        print("\n请按照上述提示解决问题后重新运行检查")

def main():
    """主函数"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("股票分析系统 - 环境检查")
    print(f"{'='*60}{Colors.END}")
    
    checks = {}
    
    # 执行各项检查
    checks['Python版本'] = check_python_version()
    checks['Python依赖包'] = check_packages()
    checks['配置文件'] = check_config()
    checks['通达信数据'] = check_tdx_data()
    checks['策略文件'] = check_strategy_file()
    checks['核心文件'] = check_core_files()
    checks['优化模块'] = check_optimized_module()
    
    # 打印摘要
    print_summary(checks)
    
    # 返回状态码
    return 0 if all(checks.values()) else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}检查已取消{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}检查过程出错: {e}{Colors.END}")
        sys.exit(1)
