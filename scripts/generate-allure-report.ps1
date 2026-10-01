param(
    [string]$Results = "reports/allure-results",
    [string]$Output = "reports/allure-report"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command allure -ErrorAction SilentlyContinue)) {
    throw "未找到 Allure CLI。请先执行：scoop install allure"
}

allure generate $Results --clean --output $Output
Write-Host "Allure 报告已生成：$Output/index.html"
