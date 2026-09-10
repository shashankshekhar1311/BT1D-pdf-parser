$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host "[BOOTSTRAP] Ensuring required Windows developer tools are installed"

function Ensure-Command {
    param(
        [Parameter(Mandatory = $true)] [string] $Name,
        [Parameter(Mandatory = $true)] [string] $DisplayName,
        [Parameter(Mandatory = $true)] [string[]] $Candidates,
        [Parameter(Mandatory = $true)] [string] $InstallerUrl,
        [Parameter(Mandatory = $true)] [string] $InstallArgs
    )

    $resolved = $null
    foreach ($candidate in $Candidates) {
        try {
            $resolved = (Get-Command $candidate -ErrorAction Stop).Source
            if ($resolved) { break }
        }
        catch {
            $resolved = $null
        }
    }

    if ($resolved) {
        Write-Host "[BOOTSTRAP] $DisplayName already available at $resolved"
        return $resolved
    }

    Write-Host "[BOOTSTRAP] $DisplayName not found. Downloading installer..."
    $tempDir = Join-Path $env:TEMP "pdf_parser_bootstrap"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    $installerPath = Join-Path $tempDir ([System.IO.Path]::GetFileName($InstallerUrl))

    try {
        Invoke-WebRequest -Uri $InstallerUrl -OutFile $installerPath -UseBasicParsing
    }
    catch {
        throw "Failed to download $DisplayName installer from $InstallerUrl. Check network access or install it manually."
    }

    Write-Host "[BOOTSTRAP] Installing $DisplayName"
    Start-Process -FilePath $installerPath -ArgumentList $InstallArgs -Wait -NoNewWindow

    foreach ($candidate in $Candidates) {
        try {
            $resolved = (Get-Command $candidate -ErrorAction Stop).Source
            if ($resolved) { break }
        }
        catch {
            $resolved = $null
        }
    }

    if (-not $resolved) {
        throw "$DisplayName was installed but still not found on PATH. Open a new PowerShell window and retry."
    }

    Write-Host "[BOOTSTRAP] $DisplayName installed at $resolved"
    return $resolved
}

$gitCandidates = @(
    "git.exe",
    "D:\Git\cmd\git.exe",
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files\Git\bin\git.exe"
)
$gitArgs = "/SILENT /NORESTART /NOCANCEL /SP- /COMPONENTS=icons,ext\reg\shellhere,assoc,assoc_sh"
$gitInstaller = "https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.1/Git-2.55.0-64-bit.exe"
$gitExe = Ensure-Command -Name "git.exe" -DisplayName "Git for Windows" -Candidates $gitCandidates -InstallerUrl $gitInstaller -InstallArgs $gitArgs

$pythonCandidates = @(
    "python.exe",
    "py.exe",
    "C:\Program Files\Python311\python.exe",
    "C:\Program Files\Python312\python.exe",
    "C:\Program Files\Python313\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe"
)
$pythonInstaller = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$pythonExe = Ensure-Command -Name "python.exe" -DisplayName "Python 3.11" -Candidates $pythonCandidates -InstallerUrl $pythonInstaller -InstallArgs "/quiet InstallAllUsers=1 PrependPath=1"

# Refresh PATH in the current session for the rest of the script
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + $env:Path

Write-Host "[BOOTSTRAP] Verifying Git and Python"
& $gitExe --version
& $pythonExe --version

Write-Host "[BOOTSTRAP] Prerequisites installed successfully. You can now run the project setup script."
Write-Host "[BOOTSTRAP] Example: powershell -ExecutionPolicy Bypass -File .\152\scripts\setup_152_server.ps1"
