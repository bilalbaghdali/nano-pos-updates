param([Parameter(Mandatory=$true)][string]$SourceRoot)
$ErrorActionPreference='Stop'
$helper=Join-Path $SourceRoot 'test-patch-helper.ps1'
if (!(Test-Path -LiteralPath $helper)) { throw 'Missing extracted Windows patch helper' }
$base=Join-Path $env:RUNNER_TEMP ('nano-pos-194-integration-'+[guid]::NewGuid().ToString('N'))
$resources=Join-Path $base 'resources'
$payload=Join-Path $base 'payload'
$backup=Join-Path $base 'rollback'
$zip=Join-Path $base 'patch.zip'
$result=Join-Path $base 'last-patch-result.json'
$fakeExe=Join-Path $base 'nano-test-no-exe.exe'
New-Item -ItemType Directory -Force -Path $resources,$payload | Out-Null
try {
  $installed=Join-Path $resources 'app.asar'
  $newAsar=Join-Path $payload 'app.asar'
  [IO.File]::WriteAllText($installed,'old-nano-app-verified',[Text.Encoding]::UTF8)
  [IO.File]::WriteAllText($newAsar,'new-nano-app-verified',[Text.Encoding]::UTF8)
  $oldHash=(Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant()
  $newHash=(Get-FileHash -LiteralPath $newAsar -Algorithm SHA256).Hash.ToLowerInvariant()
  Compress-Archive -Path $payload -DestinationPath $zip -Force
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -PidToWait 2147483647 -ZipPath $zip -ResourcesPath $resources -ExePath $fakeExe -BackupDir $backup -ExpectedAsarSha $newHash -TargetVersion '1.0.94' -ResultPath $result
  if ($LASTEXITCODE -ne 0) { throw 'Valid patch installation failed' }
  $status=Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
  if ($status.status -ne 'success') { throw 'Valid patch did not report success' }
  if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant() -ne $newHash) { throw 'New payload not installed' }
  if ((Get-FileHash -LiteralPath (Join-Path $backup 'app.asar') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $oldHash) { throw 'Verified backup missing or corrupt' }
  Write-Host 'PASS: Windows atomic update and retained verified rollback copy'

  # Invalid payload hash: no bytes of the existing app can be replaced.
  [IO.File]::WriteAllText($installed,'old-nano-app-verified',[Text.Encoding]::UTF8)
  Compress-Archive -Path $payload -DestinationPath $zip -Force
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -PidToWait 2147483647 -ZipPath $zip -ResourcesPath $resources -ExePath $fakeExe -BackupDir (Join-Path $base 'rollback2') -ExpectedAsarSha ('0'*64) -TargetVersion '1.0.94' -ResultPath $result
  if ($LASTEXITCODE -eq 0) { throw 'Invalid update unexpectedly installed' }
  if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant() -ne $oldHash) { throw 'Invalid update modified original' }
  Write-Host 'PASS: invalid update rejected, original preserved'

  # Inject failure immediately after the real backup verification line, then
  # exercise the production catch/rollback logic without modifying live code.
  $source=Get-Content -LiteralPath $helper -Raw
  $anchor='  Write-Log (''Rollback backup verified: '' + $originalHash)'
  if (-not $source.Contains($anchor)) { throw 'Backup verification injection point missing' }
  $broken=$source.Replace($anchor,($anchor+[Environment]::NewLine+"  throw 'injected_failure_after_backup'"))
  $injected=Join-Path $base 'injected-helper.ps1'
  Set-Content -LiteralPath $injected -Value $broken -Encoding UTF8
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $injected -PidToWait 2147483647 -ZipPath $zip -ResourcesPath $resources -ExePath $fakeExe -BackupDir (Join-Path $base 'rollback3') -ExpectedAsarSha $newHash -TargetVersion '1.0.94' -ResultPath $result
  if ($LASTEXITCODE -eq 0) { throw 'Failure injection unexpectedly succeeded' }
  $failure=Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
  if ($failure.status -ne 'failed') { throw 'Failure status not recorded' }
  if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant() -ne $oldHash) { throw 'Rollback failed after simulated interruption' }
  Write-Host 'PASS: post-backup failure restores and verifies original application'
} finally {
  Remove-Item -LiteralPath $base -Recurse -Force -ErrorAction SilentlyContinue
}
