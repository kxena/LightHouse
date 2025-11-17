<#
PowerShell helper to:
- back up original processing scripts to a timestamped folder
- install Python requirements
- remove originals and validate regeneration using the copy in `processing_bundle/`

Run from the `backend/` folder: `./run_regeneration.ps1`
#>

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$timestamp = Get-Date -Format "yyyy-MM-ddTHHmmss"
$backup = Join-Path $root "originals_backup_$timestamp"

Write-Host "Creating backup folder: $backup"
New-Item -ItemType Directory -Path $backup -Force | Out-Null

$files = @("process_incidents.py","enrich_location_db.py","regenerate_incidents.py","run_thresholds.py")
foreach ($f in $files) {
    $src = Join-Path $root $f
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $backup -Force
        Write-Host "Backed up $f"
    } else {
        Write-Host "Warning: $f not found, skipping backup"
    }
}

# Install requirements
$req = Join-Path $root 'requirements.txt'
if (Test-Path $req) {
    Write-Host "Installing Python requirements from $req"
    python -m pip install -r $req
} else {
    Write-Host "requirements.txt not found at $req; skipping pip install"
}

Write-Host "Removing original processing scripts from backend/"
foreach ($f in $files) {
    $p = Join-Path $root $f
    if (Test-Path $p) {
        Remove-Item $p -Force
        Write-Host "Removed $f"
    }
}

# Create a small validator that loads the processing bundle module directly and runs one regeneration
$validator = @'
import importlib.util, os, sys, json
base = os.path.dirname(__file__)
pb_path = os.path.join(base, 'processing_bundle', 'process_incidents.py')
spec = importlib.util.spec_from_file_location('pb_pi', pb_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
res = mod.process_final_results(input_file=os.path.join(base,'final_results.json'), output_file=os.path.join(base,'incidents_validation.json'), cluster_threshold_km=50.0, write_output=True)
print('VALIDATION_METADATA:' + json.dumps(res.get('metadata', {})))
'@

$valpath = Join-Path $root '_validate_processing_bundle.py'
Set-Content -Path $valpath -Value $validator -Encoding UTF8

Write-Host "Running validation using processing_bundle/process_incidents.py"
python $valpath

if (Test-Path $valpath) { Remove-Item $valpath -Force }

Write-Host "Done. Backed up originals to $backup, removed originals, and ran a validation run."
