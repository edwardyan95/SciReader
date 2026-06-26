$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:SCIREADER_HOST = "127.0.0.1"
if (-not $env:SCIREADER_PORT) {
  $env:SCIREADER_PORT = "4174"
}
python server.py
