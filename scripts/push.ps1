$ErrorActionPreference = 'Stop'

$message = $args -join ' '
if ([string]::IsNullOrWhiteSpace($message)) {
  $message = "Atualização $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

git status -sb | Out-Host

git add -A | Out-Host

git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
  Write-Host "Nada para commitar."
  exit 0
}

git commit -m $message | Out-Host
git push | Out-Host
