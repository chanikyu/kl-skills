# Windows counterpart of run.sh.
# Same contract: never break a session — exit 0 when the binary is absent.
#
# Only x86_64 is shipped: ARM64 Windows runs x86_64 binaries under emulation,
# so a separate aarch64 build buys nothing yet.
$ErrorActionPreference = 'SilentlyContinue'

$root = if ($env:CLAUDE_PLUGIN_ROOT) { $env:CLAUDE_PLUGIN_ROOT } else { Split-Path -Parent $PSScriptRoot }
$bin = Join-Path $root 'bin\kl-gate-x86_64-pc-windows-msvc.exe'
if (-not (Test-Path $bin)) { exit 0 }

$payload = [Console]::In.ReadToEnd()
$payload | & $bin @args
exit $LASTEXITCODE
