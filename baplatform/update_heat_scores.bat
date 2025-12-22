@echo off
REM 用户个性化推荐分数更新任务
REM 此脚本用于Windows任务计划程序
REM 功能：1. 更新帖子基础热度分数  2. 为活跃用户计算个性化推荐分数并缓存

cd /d "C:\PROGRAMING\RUC_baplatform\baplatform"

REM 激活虚拟环境并运行更新命令
call "%~dp0..\baplatform_env\Scripts\activate.bat" && python manage.py update_heat_scores >> "%~dp0..\logs\heat_score_update.log" 2>&1

REM 如果日志文件夹不存在，创建它
if not exist "%~dp0..\logs" mkdir "%~dp0..\logs"

echo [%date% %time%] Personalized recommendation score update task completed >> "%~dp0..\logs\heat_score_update.log"
