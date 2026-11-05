# Annotates the 1C screenshots for the e1c page: red frames, arrows, number badges; replaces the user name.
param([string]$ImagesDir, [string]$OutDir)
Add-Type -AssemblyName System.Drawing

$red  = [Drawing.Color]::FromArgb(229, 57, 53)
$pen  = New-Object Drawing.Pen($red, 3)
$arrowPen = New-Object Drawing.Pen($red, 3)
$arrowPen.CustomEndCap = New-Object Drawing.Drawing2D.AdjustableArrowCap(4, 5)

function New-Canvas($path) {
    $src = [Drawing.Image]::FromFile($path)
    $bmp = New-Object Drawing.Bitmap($src.Width, $src.Height)
    $g = [Drawing.Graphics]::FromImage($bmp)
    $g.DrawImage($src, 0, 0, $src.Width, $src.Height)
    $src.Dispose()
    $g.SmoothingMode = 'AntiAlias'
    $g.TextRenderingHint = 'ClearTypeGridFit'
    return @{ Bmp = $bmp; G = $g }
}

function Draw-Badge($g, $x, $y, $text) {
    $g.FillEllipse((New-Object Drawing.SolidBrush($red)), $x - 11, $y - 11, 22, 22)
    $font = New-Object Drawing.Font('Segoe UI', 10, [Drawing.FontStyle]::Bold, [Drawing.GraphicsUnit]::Point)
    $fmt = New-Object Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
    $g.DrawString($text, $font, [Drawing.Brushes]::White, (New-Object Drawing.RectangleF(($x - 11), ($y - 11), 22, 22)), $fmt)
}

# --- Main menu of the thin client ---
$c = New-Canvas (Join-Path $ImagesDir '11.png'); $g = $c.G
# user name -> neutral name, on the header background, right-aligned like the original
$g.FillRectangle((New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(251, 237, 158))), 134, 6, 88, 20)
$nameFont = New-Object Drawing.Font('Segoe UI', 9, [Drawing.FontStyle]::Regular, [Drawing.GraphicsUnit]::Point)
$fmt = New-Object Drawing.StringFormat; $fmt.Alignment = 'Far'; $fmt.LineAlignment = 'Center'
$g.DrawString('Иванов Иван', $nameFont, (New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(51, 51, 51))), (New-Object Drawing.RectangleF(120, 5, 101, 22)), $fmt)
# 1: menu button, 2: «Перейти по ссылке...»
$g.DrawRectangle($pen, 224, 1, 38, 28)
$g.DrawRectangle($pen, 2, 61, 353, 30)
$g.DrawLine($arrowPen, 190, 50, 222, 26)
Draw-Badge $g 180 52 '1'
$g.DrawLine($arrowPen, 236, 128, 196, 95)
Draw-Badge $g 246 136 '2'
$c.Bmp.Save((Join-Path $OutDir 'menu-go-to-link.png'), [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $c.Bmp.Dispose()

# --- Launcher window ---
$c = New-Canvas (Join-Path $ImagesDir '10.png'); $g = $c.G
$g.DrawRectangle($pen, 175, 263, 123, 22)
$g.DrawLine($arrowPen, 112, 240, 170, 268)
$c.Bmp.Save((Join-Path $OutDir 'launcher-go-to-link.png'), [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $c.Bmp.Dispose()
"done"
