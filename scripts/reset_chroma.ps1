# Run from project root or backend folder when Chroma settings conflict.
$backend = if (Test-Path "backend") { "backend" } else { "." }
$path = Join-Path $backend "chroma_db"
if (Test-Path $path) {
    Remove-Item -Recurse -Force $path
    Write-Host "Deleted $path"
}
New-Item -ItemType Directory -Force -Path $path | Out-Null
Write-Host "Recreated $path. Upload documents again to rebuild embeddings."
