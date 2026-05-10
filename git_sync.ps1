<#
PowerFlow V6 - Git sync ultra-simple
Usage:
  .\git_sync.ps1 "Message"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Message,

    [string]$RepoUrl = "https://github.com/gestionzen57-alt/V7.git"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$Args)

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Commande git echouee: git $($Args -join ' ')"
    }
}

$inside = (& git rev-parse --is-inside-work-tree 2>$null)
if ($LASTEXITCODE -ne 0 -or $inside.Trim() -ne "true") {
    throw "Ce dossier n'est pas un repo Git. Lance le script depuis la racine du repo PowerFlow/V7."
}

$origin = (& git remote get-url origin 2>$null)
if ($LASTEXITCODE -ne 0) {
    Invoke-Git @("remote", "add", "origin", $RepoUrl)
    $origin = $RepoUrl
}
elseif ($origin.Trim() -ne $RepoUrl) {
    Write-Host "Remote origin actuel : $($origin.Trim())"
    Write-Host "Remote attendu       : $RepoUrl"
    Write-Host "Aucune modification du remote."
}

Invoke-Git @("add", ".")

$status = (& git status --porcelain)
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "Aucun changement a committer."
}
else {
    Invoke-Git @("commit", "-m", $Message)
}

$branch = (& git rev-parse --abbrev-ref HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch)) {
    throw "Impossible de detecter la branche courante."
}

Invoke-Git @("push", "-u", "origin", $branch)

Write-Host "Git sync termine."
Write-Host "Repo   : $RepoUrl"
Write-Host "Branch : $branch"
Write-Host "URL    : $RepoUrl"
