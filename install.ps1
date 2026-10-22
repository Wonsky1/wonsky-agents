# Optional Windows launcher. py -3 install.py also works directly.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$InstallerArguments)

$ErrorActionPreference = 'Stop'
foreach ($Candidate in @('py', 'python', 'python3')) {
    $Executable = Get-Command $Candidate -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $Executable) { continue }
    # Skip an unconfigured Microsoft Store alias instead of opening the Store.
    $Item = Get-Item -LiteralPath $Executable.Source -ErrorAction SilentlyContinue
    if ($Item -and $Item.Length -eq 0) { continue }
    $PrefixArguments = @()
    if ($Candidate -eq 'py') { $PrefixArguments = @('-3') }
    & $Executable.Source @PrefixArguments -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) {
        & $Executable.Source @PrefixArguments (Join-Path $PSScriptRoot 'install.py') @InstallerArguments
        exit $LASTEXITCODE
    }
}
Write-Error 'Python 3.9+ is required. Install Python from https://www.python.org/downloads/ and run this launcher again. No pip packages, Git or rsync are needed.'
exit 1
