param([Parameter(Mandatory=$true)][string]$Manifest)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$manifestPath = (Resolve-Path -LiteralPath $Manifest).Path
$entries = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$speech = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $speech.SelectVoice('Microsoft Zira Desktop')
    $speech.Rate = 1
    foreach ($entry in $entries) {
        $target = [System.IO.Path]::GetFullPath($entry.audio)
        $speech.SetOutputToWaveFile($target)
        $speech.Speak([string]$entry.en)
        $speech.SetOutputToNull()
    }
} finally { $speech.Dispose() }
Write-Output 'Offline narration complete. Microsoft Zira Desktop; no cloud request.'
