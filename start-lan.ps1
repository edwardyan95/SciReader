$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:SCIREADER_HOST = "0.0.0.0"
if (-not $env:SCIREADER_PORT) {
  $env:SCIREADER_PORT = "4174"
}
python server.py
