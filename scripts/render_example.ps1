<#
One-line helper to render example video using the repo's Python runner.

Usage examples:
    # default: use config.json, out/ directory, and MoviePy renderer
    .\scripts\render_example.ps1

  # pass a specific output filename (only valid when JSON has 1 item)
  .\scripts\render_example.ps1 -OutFile example.mp4

  # dry-run and use moviepy
  .\scripts\render_example.ps1 -OutFile example.mp4 -DryRun -UseMoviepy
#>

param(
    [string]$OutFile = "test2",
    [string]$Json = "config.json",
    [string]$OutDir = "out",
    [switch]$UseMoviepy = $true,
    [switch]$DryRun,
    [bool]$HideTimer = $true
)

$venv = "C:\Projects\en_words\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    & $venv
} else {
    Write-Host "Warning: virtualenv activate script not found at $venv; continuing without activation"
}

# ensure repo-local ffmpeg is used
$env:IMAGEIO_FFMPEG_EXE = "C:\Projects\en_words\FFmpeg\ffmpeg.exe"
$env:FFMPEG_PATH = "C:\Projects\en_words\FFmpeg\ffmpeg.exe"
Set-Location -Path "C:\Projects\en_words"

# build python argument list and pass as separate args
$pythonArgs = @()
$pythonArgs += "scripts/render_example.py"
$pythonArgs += "--json"
$pythonArgs += $Json
$pythonArgs += "--out-dir"
$pythonArgs += $OutDir
if ($UseMoviepy) { $pythonArgs += "--use-moviepy" }
if ($DryRun) { $pythonArgs += "--dry-run" }
if ($HideTimer) { $pythonArgs += "--hide-timer" } else { $pythonArgs += "--timer-visible" }
if ($OutFile -ne "") { $pythonArgs += "--out-file"; $pythonArgs += $OutFile }

Write-Host "Running: python $($pythonArgs -join ' ')"
& python @pythonArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "ffprobe results for files in $OutDir/ :"
    Get-ChildItem -Path $OutDir -Filter '*.mp4' | ForEach-Object {
        Write-Host "==> $_"
        C:\Projects\en_words\FFmpeg\ffprobe.exe -v error -show_entries stream=index,codec_type,codec_name -of default=noprint_wrappers=1 $_.FullName
    }
}

