# Aggressive Cache Clear Script for Expo
# Run this script in PowerShell to clear all Expo/Metro caches

Write-Host "🧹 Starting Aggressive Cache Clearing..." -ForegroundColor Cyan

# Stop if any command fails
$ErrorActionPreference = "Continue"

# Clear .expo directory
Write-Host "`n📁 Clearing .expo directory..." -ForegroundColor Yellow
if (Test-Path ".\.expo") {
    Remove-Item -Recurse -Force ".\.expo\*" -ErrorAction SilentlyContinue
    Write-Host "✓ .expo directory cleared" -ForegroundColor Green
}

# Clear node_modules cache
Write-Host "`n📁 Clearing node_modules cache..." -ForegroundColor Yellow
if (Test-Path ".\node_modules\.cache") {
    Remove-Item -Recurse -Force ".\node_modules\.cache" -ErrorAction SilentlyContinue
    Write-Host "✓ node_modules cache cleared" -ForegroundColor Green
}

# Clear Metro cache in temp
Write-Host "`n📁 Clearing Metro cache from temp..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "$env:TEMP\metro-*" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\haste-map-*" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:TEMP\react-native-*" -ErrorAction SilentlyContinue
Write-Host "✓ Temp cache cleared" -ForegroundColor Green

# Clear watchman if it exists
Write-Host "`n📁 Checking for Watchman..." -ForegroundColor Yellow
$watchmanExists = Get-Command watchman -ErrorAction SilentlyContinue
if ($watchmanExists) {
    Write-Host "Found Watchman, clearing..." -ForegroundColor Yellow
    watchman watch-del-all 2>$null
    Write-Host "✓ Watchman cache cleared" -ForegroundColor Green
} else {
    Write-Host "Watchman not found (this is OK)" -ForegroundColor Gray
}

Write-Host "`n✅ All caches cleared!" -ForegroundColor Green
Write-Host "`n🚀 Now run: npx expo start --clear" -ForegroundColor Cyan
Write-Host "📱 Then completely close and reopen Expo Go app" -ForegroundColor Cyan
