# 读取 docs/profile_data.csv，把热点函数耗时画成 PNG 柱状图。
# 用法（在项目根目录）：powershell -ExecutionPolicy Bypass -File tools\render_chart.ps1

Add-Type -AssemblyName System.Drawing

$root = Split-Path -Parent $PSScriptRoot
$csvPath = Join-Path $root "docs\profile_data.csv"
$pngPath = Join-Path $root "docs\profile.png"

$rows = Import-Csv $csvPath
$rowHeight = 34
$top = 72
$width = 860
$height = $top + $rows.Count * $rowHeight + 24

$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.Clear([System.Drawing.Color]::White)

$titleFont = New-Object System.Drawing.Font("Microsoft YaHei", 14, [System.Drawing.FontStyle]::Bold)
$labelFont = New-Object System.Drawing.Font("Microsoft YaHei", 10)
$brush = [System.Drawing.Brushes]::Black

$graphics.DrawString("查重程序热点函数累计耗时", $titleFont, $brush, 12, 16)

$maxValue = ($rows | ForEach-Object { [double]$_.cumulative_ms } | Measure-Object -Maximum).Maximum
if (-not $maxValue -or $maxValue -le 0) { $maxValue = 1 }

$index = 0
foreach ($row in $rows) {
    $y = $top + $index * $rowHeight
    $graphics.DrawString($row.function, $labelFont, $brush, 12, $y)
    $barWidth = [int]([double]$row.cumulative_ms / $maxValue * 440)
    if ($barWidth -lt 1) { $barWidth = 1 }
    $graphics.FillRectangle([System.Drawing.Brushes]::CornflowerBlue, 230, $y, $barWidth, 20)
    $graphics.DrawString("$($row.cumulative_ms) ms", $labelFont, $brush, (238 + $barWidth), $y)
    $index++
}

$graphics.Dispose()
$bitmap.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()

Write-Output "已生成 $pngPath"
