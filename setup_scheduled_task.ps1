# PowerShell脚本：自动设置Windows定时任务
# 用于每小时更新帖子热度分数
# 使用方法：右键点击 -> 使用PowerShell运行（需要管理员权限）

# 检查是否以管理员身份运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ 错误：需要管理员权限才能创建定时任务" -ForegroundColor Red
    Write-Host "请右键点击此脚本，选择'以管理员身份运行'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  用户个性化推荐分数定时更新设置" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 配置路径
$projectPath = "C:\PROGRAMING\RUC_baplatform\baplatform"
$batchFile = Join-Path $projectPath "update_heat_scores.bat"
$logFolder = "C:\PROGRAMING\RUC_baplatform\logs"
$taskName = "更新用户个性化推荐分数"

# 检查批处理文件是否存在
if (-not (Test-Path $batchFile)) {
    Write-Host "❌ 错误：找不到批处理文件: $batchFile" -ForegroundColor Red
    pause
    exit 1
}

# 创建日志文件夹
if (-not (Test-Path $logFolder)) {
    New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
    Write-Host "✓ 创建日志文件夹: $logFolder" -ForegroundColor Green
}

Write-Host "配置信息：" -ForegroundColor Yellow
Write-Host "  任务名称: $taskName"
Write-Host "  项目路径: $projectPath"
Write-Host "  批处理文件: $batchFile"
Write-Host "  日志文件夹: $logFolder"
Write-Host ""

# 检查任务是否已存在
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "⚠ 警告：任务 '$taskName' 已存在" -ForegroundColor Yellow
    $response = Read-Host "是否要删除并重新创建？(y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "✓ 已删除旧任务" -ForegroundColor Green
    } else {
        Write-Host "取消操作" -ForegroundColor Gray
        pause
        exit 0
    }
}

Write-Host ""
Write-Host "正在创建定时任务..." -ForegroundColor Cyan

try {
    # 创建任务操作
    $action = New-ScheduledTaskAction `
        -Execute $batchFile `
        -WorkingDirectory $projectPath

    # 创建触发器（每小时运行一次）
    $trigger = New-ScheduledTaskTrigger `
        -Once `
        -At (Get-Date).AddMinutes(5) `
        -RepetitionInterval (New-TimeSpan -Hours 1) `
        -RepetitionDuration ([TimeSpan]::MaxValue)

    # 创建主体（使用当前用户）
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest

    # 创建设置
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1)

    # 注册任务
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "每小时为活跃用户计算个性化推荐分数并缓存，提高论坛推荐系统性能" `
        -ErrorAction Stop | Out-Null

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "✓ 定时任务创建成功！" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "任务详情：" -ForegroundColor Cyan
    Write-Host "  - 首次运行：$(Get-Date).AddMinutes(5).ToString('yyyy-MM-dd HH:mm')"
    Write-Host "  - 运行频率：每小时一次"
    Write-Host "  - 日志位置：$logFolder\heat_score_update.log"
    Write-Host ""
    
    # 显示任务信息
    $taskInfo = Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo
    Write-Host "当前状态：" -ForegroundColor Cyan
    Write-Host "  - 状态：$(if ((Get-ScheduledTask -TaskName $taskName).State -eq 'Ready') {'就绪 ✓'} else {(Get-ScheduledTask -TaskName $taskName).State})" 
    Write-Host "  - 上次运行时间：$($taskInfo.LastRunTime)"
    Write-Host "  - 下次运行时间：$($taskInfo.NextRunTime)"
    Write-Host ""
    
    Write-Host "常用命令：" -ForegroundColor Yellow
    Write-Host "  # 立即运行任务（测试）"
    Write-Host "  Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  # 查看任务状态"
    Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Get-ScheduledTaskInfo" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  # 查看日志"
    Write-Host "  Get-Content '$logFolder\heat_score_update.log' -Tail 20" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  # 停用任务"
    Write-Host "  Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  # 删除任务"
    Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Gray
    Write-Host ""

    # 询问是否立即测试
    $testNow = Read-Host "是否立即运行一次任务进行测试？(y/n)"
    if ($testNow -eq 'y' -or $testNow -eq 'Y') {
        Write-Host ""
        Write-Host "正在运行任务..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $taskName
        Start-Sleep -Seconds 2
        
        $taskInfo = Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo
        Write-Host "✓ 任务已触发" -ForegroundColor Green
        Write-Host "上次运行结果：$($taskInfo.LastTaskResult)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "提示：任务正在后台运行，可以查看日志了解执行情况" -ForegroundColor Yellow
        Write-Host "日志位置：$logFolder\heat_score_update.log" -ForegroundColor Gray
    }

} catch {
    Write-Host ""
    Write-Host "❌ 创建任务失败：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因：" -ForegroundColor Yellow
    Write-Host "  1. 缺少管理员权限"
    Write-Host "  2. 任务计划程序服务未启动"
    Write-Host "  3. 路径包含特殊字符"
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
pause
