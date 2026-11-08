<#
  60天搞定中考词汇 · 一键安装到 AI 助手的 skills 目录（Windows）

  用法：
    .\install.ps1                 # 自动判断：有 Hermes 装 Hermes，否则装 Claude Code
    .\install.ps1 -Hermes         # 装到 $env:HERMES_HOME\skills\productivity\60days-zhongkao-vocab
    .\install.ps1 -Claude         # 装到 ~\.claude\skills\60days-zhongkao-vocab
    .\install.ps1 -Target DIR     # 装到指定目录

  如果提示"禁止运行脚本"，在当前窗口先执行：
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#>
param(
  [switch]$Hermes,
  [switch]$Claude,
  [string]$Target = ""
)

$ErrorActionPreference = "Stop"
# 让中文在 Windows 控制台正常显示（cp936 控制台下默认会乱码）
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$Name = "60days-zhongkao-vocab"
$Cat  = "productivity"
$Src  = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path (Join-Path $Src "SKILL.md"))) {
  Write-Host "✗ 这个脚本要在仓库根目录里运行（找不到 SKILL.md）" -ForegroundColor Red
  exit 1
}

if (-not $Target) {
  if ($Hermes) {
    $base = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $HOME ".hermes" }
    $Target = Join-Path $base "skills\$Cat\$Name"
  } elseif ($Claude) {
    $Target = Join-Path $HOME ".claude\skills\$Name"
  } elseif ($env:HERMES_HOME) {
    $Target = Join-Path $env:HERMES_HOME "skills\$Cat\$Name"
  } elseif (Test-Path (Join-Path $HOME ".hermes")) {
    $Target = Join-Path $HOME ".hermes\skills\$Cat\$Name"
  } else {
    $Target = Join-Path $HOME ".claude\skills\$Name"
  }
}

Write-Host "→ 安装到：$Target"
$parent = Split-Path -Parent $Target
if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
if (Test-Path $Target) { Remove-Item -Recurse -Force $Target }
Copy-Item -Recurse -Force $Src $Target
$gitDir = Join-Path $Target ".git"
if (Test-Path $gitDir) { Remove-Item -Recurse -Force $gitDir }

Write-Host ""
Write-Host "✅ 安装完成" -ForegroundColor Green
Write-Host "   skill 目录：$Target"
Write-Host ""
Write-Host "下一步（二选一）："
Write-Host "  1) 在 AI 助手里说：「用 60days-zhongkao-vocab 帮我做词汇训练页」"
Write-Host "  2) 先本地试跑："
Write-Host "     python `"$Target\scripts\generate.py`" `"$Target\assets\sample-wordlist.json`" 示例.html"
Write-Host ""
Write-Host "卸载：Remove-Item -Recurse -Force `"$Target`""
