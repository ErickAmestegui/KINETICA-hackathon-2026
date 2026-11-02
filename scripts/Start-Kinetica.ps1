param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $pythonExe)) { throw 'Create .venv and install backend requirements first. See README.md.' }
if (!(Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/dist/index.html'))) { throw 'Run npm run build in frontend first.' }
$outputDirectory = Join-Path $projectRoot 'output'
New-Item -ItemType Directory -Force $outputDirectory | Out-Null
$existing = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
if ($existing) { Write-Output "Port $Port is already in use. Check http://127.0.0.1:$Port/api/health"; exit 0 }
$server = Start-Process -FilePath $pythonExe -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port',"$Port") -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $outputDirectory 'server.stdout.log') -RedirectStandardError (Join-Path $outputDirectory 'server.stderr.log')
$server.Id | Set-Content -LiteralPath (Join-Path $outputDirectory 'server.pid')
Write-Output "KINETICA starting at http://127.0.0.1:$Port (PID $($server.Id)). Logs in output/."
