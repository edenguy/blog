param(
    [Parameter(Mandatory=$true)][string]$Lang,
    [Parameter(Mandatory=$true)][string]$SourceMd
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$postDir = Split-Path -Parent $scriptDir
$sourceDir = Split-Path -Parent (Resolve-Path $SourceMd)

$htmlFile = Join-Path $sourceDir "book-$Lang.html"
$pdfFile = Join-Path $sourceDir "book-$Lang.pdf"
$cssFile = Join-Path $scriptDir "print-ltr.css"

Write-Host "=== Building $Lang PDF ===" -ForegroundColor Cyan
Write-Host "Source:  $SourceMd"
Write-Host "Output:  $pdfFile"
Write-Host ""

Write-Host "[1/3] Extracting metadata..." -ForegroundColor Yellow
$md = [System.IO.File]::ReadAllText($SourceMd, [System.Text.Encoding]::UTF8)
$titleMatch = [regex]::Match($md, 'title:\s*"([^"]+)"')
$authorMatch = [regex]::Match($md, 'author:\s*"([^"]+)"')
$dateMatch = [regex]::Match($md, 'date:\s*(\S+)')
$subtitleMatch = [regex]::Match($md, 'subtitle:\s*"([^"]+)"')
$title = if ($titleMatch.Success) { $titleMatch.Groups[1].Value } else { "Untitled" }
$author = if ($authorMatch.Success) { $authorMatch.Groups[1].Value } else { "" }
$date = if ($dateMatch.Success) { $dateMatch.Groups[1].Value } else { "" }
$subtitle = if ($subtitleMatch.Success) { $subtitleMatch.Groups[1].Value } else { "" }
Write-Host "  Title:  $title"
Write-Host "  Author: $author"

Write-Host "[2/3] Converting Markdown -> HTML (Pandoc)..." -ForegroundColor Yellow
$subtitleHtml = if ($subtitle) { "<div class=`"subtitle`">$subtitle</div>" } else { "" }
$coverHtml = @"
<div class="cover-page">
<h1>$title</h1>
$subtitleHtml
<div class="author">$author</div>
<div class="date">$date</div>
</div>
"@
$coverFile = Join-Path $sourceDir "_cover-$Lang.html"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($coverFile, $coverHtml, $utf8NoBom)

pandoc $SourceMd `
    -o $htmlFile `
    --standalone `
    --css="print-ltr.css" `
    --include-before-body=$coverFile `
    --metadata title="$title" `
    --variable lang=$Lang `
    --variable dir=ltr `
    --resource-path="$postDir"

if ($LASTEXITCODE -ne 0) { throw "Pandoc failed with exit code $LASTEXITCODE" }

$htmlContent = [System.IO.File]::ReadAllText($htmlFile, [System.Text.Encoding]::UTF8)

$absImgPath = ($postDir -replace '\\', '/') + '/images/'
$htmlContent = $htmlContent -replace 'src="(\.\./)*images/', "src=`"$absImgPath"

$absCssPath = ($scriptDir -replace '\\', '/') + '/print-ltr.css'
$htmlContent = $htmlContent -replace 'href="print-ltr\.css"', "href=`"$absCssPath`""

[System.IO.File]::WriteAllText($htmlFile, $htmlContent, $utf8NoBom)
Write-Host "  HTML written: $htmlFile"

$postprocScript = Join-Path $scriptDir "postprocess_html.py"
if (Test-Path $postprocScript) {
    Write-Host "[2b/3] Post-processing images..." -ForegroundColor Yellow
    python $postprocScript $htmlFile
    if ($LASTEXITCODE -ne 0) { throw "Post-processing failed with exit code $LASTEXITCODE" }
}

Write-Host "[3/3] Converting HTML -> PDF (Playwright/Chromium)..." -ForegroundColor Yellow
python "$scriptDir\html_to_pdf.py" $htmlFile $pdfFile

if ($LASTEXITCODE -ne 0) { throw "PDF generation failed with exit code $LASTEXITCODE" }

Remove-Item $coverFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "PDF: $pdfFile"
