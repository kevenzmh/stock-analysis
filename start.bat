@echo off
chcp 65001 >nul
echo ========================================
echo 股票分析系统 - 快速启动
echo ========================================
echo.

REM 检查conda环境
echo [1/5] 检查conda环境...
call conda activate stock-analysis 2>nul
if errorlevel 1 (
    echo ✗ conda环境不存在或未激活
    echo.
    echo 请先创建并激活conda环境:
    echo   conda create -n stock-analysis python=3.8
    echo   conda activate stock-analysis
    pause
    exit /b 1
)
echo ✓ conda环境已激活
echo.

REM 检查依赖
echo [2/5] 检查Python依赖...
python check_environment.py
if errorlevel 1 (
    echo.
    echo ✗ 环境检查未通过
    echo 请按照提示解决问题后重新运行
    pause
    exit /b 1
)
echo.

REM 菜单选择
:menu
echo ========================================
echo 请选择要执行的操作:
echo ========================================
echo.
echo [1] 更新财务数据 (readTDX_cw.py)
echo [2] 更新日线数据 (readTDX_lday.py)
echo [3] 运行选股 (xuangu.py)
echo [4] 完整流程 (更新数据 + 选股)
echo [5] 测试优化模块 (examples.py)
echo [0] 退出
echo.
set /p choice="请输入选项 (0-5): "

if "%choice%"=="1" goto update_cw
if "%choice%"=="2" goto update_lday
if "%choice%"=="3" goto xuangu
if "%choice%"=="4" goto full_process
if "%choice%"=="5" goto examples
if "%choice%"=="0" goto end
echo 无效的选项
goto menu

:update_cw
echo.
echo [3/5] 更新财务数据...
python readTDX_cw.py
if errorlevel 1 (
    echo ✗ 财务数据更新失败
    pause
    goto menu
)
echo ✓ 财务数据更新完成
echo.
pause
goto menu

:update_lday
echo.
echo [4/5] 更新日线数据...
echo 提示: 首次运行可能需要很长时间 (30分钟-2小时)
python readTDX_lday.py
if errorlevel 1 (
    echo ✗ 日线数据更新失败
    pause
    goto menu
)
echo ✓ 日线数据更新完成
echo.
pause
goto menu

:xuangu
echo.
echo [5/5] 运行选股...
python xuangu.py
if errorlevel 1 (
    echo ✗ 选股失败
    pause
    goto menu
)
echo ✓ 选股完成
echo.
pause
goto menu

:full_process
echo.
echo 执行完整流程...
echo.
echo [Step 1] 更新财务数据...
python readTDX_cw.py
if errorlevel 1 (
    echo ✗ 财务数据更新失败
    pause
    goto menu
)
echo ✓ 财务数据更新完成
echo.

echo [Step 2] 更新日线数据...
python readTDX_lday.py
if errorlevel 1 (
    echo ✗ 日线数据更新失败
    pause
    goto menu
)
echo ✓ 日线数据更新完成
echo.

echo [Step 3] 运行选股...
python xuangu.py
if errorlevel 1 (
    echo ✗ 选股失败
    pause
    goto menu
)
echo ✓ 选股完成
echo.
echo ========================================
echo 完整流程执行完成!
echo ========================================
pause
goto menu

:examples
echo.
echo 运行优化模块示例...
python examples.py
pause
goto menu

:end
echo.
echo 程序退出
exit /b 0
