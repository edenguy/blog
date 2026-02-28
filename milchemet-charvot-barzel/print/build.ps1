$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$postDir = Split-Path -Parent $scriptDir
$printDir = $scriptDir

$readme = Join-Path $postDir "README.md"
$htmlFile = Join-Path $printDir "book.html"
$pdfFile = Join-Path $printDir "book.pdf"
$cssFile = Join-Path $printDir "print.css"

Write-Host "=== Building print PDF ===" -ForegroundColor Cyan
Write-Host "Source:  $readme"
Write-Host "Output:  $pdfFile"
Write-Host ""

# Step 1: Extract metadata from YAML front-matter
Write-Host "[1/3] Extracting metadata..." -ForegroundColor Yellow
$md = [System.IO.File]::ReadAllText($readme, [System.Text.Encoding]::UTF8)
$titleMatch = [regex]::Match($md, 'title:\s*"([^"]+)"')
$authorMatch = [regex]::Match($md, 'author:\s*"([^"]+)"')
$dateMatch = [regex]::Match($md, 'date:\s*(\S+)')
$title = if ($titleMatch.Success) { $titleMatch.Groups[1].Value } else { "Untitled" }
$author = if ($authorMatch.Success) { $authorMatch.Groups[1].Value } else { "" }
$date = if ($dateMatch.Success) { $dateMatch.Groups[1].Value } else { "" }
Write-Host "  Title:  $title"
Write-Host "  Author: $author"
Write-Host "  Date:   $date"

# Step 2: Convert Markdown to HTML via Pandoc
Write-Host "[2/3] Converting Markdown -> HTML (Pandoc)..." -ForegroundColor Yellow
$coverHtml = @"
<div class="cover-page">
<h1>$title</h1>
<div class="author">$author</div>
<div class="date">$date</div>
</div>
"@
$coverFile = Join-Path $printDir "_cover.html"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($coverFile, $coverHtml, $utf8NoBom)

pandoc $readme `
    -o $htmlFile `
    --standalone `
    --css="print.css" `
    --include-before-body=$coverFile `
    --metadata title="$title" `
    --variable lang=he `
    --variable dir=rtl `
    --resource-path="$postDir"

if ($LASTEXITCODE -ne 0) { throw "Pandoc failed with exit code $LASTEXITCODE" }

# Fix image and CSS paths to absolute (Playwright needs file:// URIs)
$htmlContent = [System.IO.File]::ReadAllText($htmlFile, [System.Text.Encoding]::UTF8)

$absImgPath = ($postDir -replace '\\', '/') + '/images/'
$htmlContent = $htmlContent -replace 'src="images/', "src=`"$absImgPath"

$absCssPath = ($printDir -replace '\\', '/') + '/print.css'
$htmlContent = $htmlContent -replace 'href="print\.css"', "href=`"$absCssPath`""

[System.IO.File]::WriteAllText($htmlFile, $htmlContent, $utf8NoBom)
Write-Host "  HTML written: $htmlFile"

# Step 2b: Post-process HTML (pair phone screenshots side-by-side)
$postprocScript = Join-Path $printDir "postprocess_html.py"
if (Test-Path $postprocScript) {
    Write-Host "[2b/3] Post-processing phone screenshots..." -ForegroundColor Yellow
    python $postprocScript $htmlFile $postDir
    if ($LASTEXITCODE -ne 0) { throw "Post-processing failed with exit code $LASTEXITCODE" }
}

# Step 3: Convert HTML to PDF via Playwright
Write-Host "[3/3] Converting HTML -> PDF (Playwright/Chromium)..." -ForegroundColor Yellow
python "$printDir\html_to_pdf.py" $htmlFile $pdfFile

if ($LASTEXITCODE -ne 0) { throw "PDF generation failed with exit code $LASTEXITCODE" }

# Cleanup
Remove-Item $coverFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Green
Write-Host "PDF: $pdfFile"
