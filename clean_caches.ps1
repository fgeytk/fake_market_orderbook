# Arrêter le serveur s'il tourne encore
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*\.venv*"} | Stop-Process -Force

$root = Get-Location
$dirs = @(
  "__pycache__",
  ".hypothesis",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  "htmlcov"
)

Get-ChildItem -Path $root -Recurse -Force -Directory |
  Where-Object { $dirs -contains $_.Name } |
  ForEach-Object { Remove-Item -Recurse -Force $_.FullName }

Get-ChildItem -Path $root -Recurse -Force -File -Filter "*.pyc" |
  ForEach-Object { Remove-Item -Force $_.FullName }

Get-ChildItem -Path $root -Recurse -Force -File -Filter ".coverage*" |
  ForEach-Object { Remove-Item -Force $_.FullName }
