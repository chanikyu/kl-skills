# Windows counterpart of run.sh. Same dispatch, same contract.
#
#   run.ps1 <gate-name> [extra args...]
#
#   1. hooks\py\<gate-name>.py exists -> run it with python/python3 if available
#   2. otherwise                      -> bin\kl-gate-x86_64-pc-windows-msvc.exe
#
# Python is often absent on Windows, which is exactly why the Rust binary is the
# one that ships prebuilt. When python is missing this exits 0 rather than erroring:
# a missing rule beats a session that will not start.
#
# Only x86_64 is shipped: ARM64 Windows runs x86_64 binaries under emulation,
# so a separate aarch64 build buys nothing yet.
$ErrorActionPreference = 'SilentlyContinue'

$root = if ($env:CLAUDE_PLUGIN_ROOT) { $env:CLAUDE_PLUGIN_ROOT } else { Split-Path -Parent $PSScriptRoot }
$gate = if ($args.Count -gt 0) { $args[0] } else { '' }
$payload = [Console]::In.ReadToEnd()

# 1. Python gate
if ($gate) {
  $pyScript = Join-Path $root "hooks\py\$gate.py"
  if (Test-Path $pyScript) {
    foreach ($py in @('python3', 'python')) {
      if (Get-Command $py -ErrorAction SilentlyContinue) {
        $payload | & $py $pyScript @args
        exit $LASTEXITCODE
      }
    }
    exit 0
  }
}

# 2. Rust gate
$bin = Join-Path $root 'bin\kl-gate-x86_64-pc-windows-msvc.exe'
if (-not (Test-Path $bin)) { exit 0 }

$payload | & $bin @args
exit $LASTEXITCODE
