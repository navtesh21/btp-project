param([string]$Deck = "BTP_presentation.pptx", [string]$OutDir = "deck_png")
$deckPath = (Resolve-Path $Deck).Path
$out = Join-Path (Get-Location) $OutDir
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory $out | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
$pres = $ppt.Presentations.Open($deckPath, $true, $false, $false)
# 1600px wide keeps text legible without huge files
$pres.SaveCopyAs($out + "\deck.pptx", 17)   # 17 = ppSaveAsPNG writes one PNG per slide
$pres.Close()
$ppt.Quit()
Write-Output ("slides exported: " + (Get-ChildItem -Path $out -Recurse -Filter *.PNG).Count)
Get-ChildItem -Path $out -Recurse -Filter *.PNG | Select-Object -First 3 -ExpandProperty FullName
