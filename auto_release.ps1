<#
.SYNOPSIS
    自动发布新版本脚本

.DESCRIPTION
    读取所有 git tag，找到最大版本号，自动递增并推送到远程
    版本号格式：vx.x.x（前两位最大10，最后一位最大100）

.PARAMETER DryRun
    演习模式，仅显示将要执行的操作，不实际创建标签

.EXAMPLE
    .\auto_release.ps1
    自动递增并发布新版本

.EXAMPLE
    .\auto_release.ps1 -DryRun
    仅显示将要创建的版本号
#>

param(
    [switch]$DryRun
)

# 版本号限制
$MAX_MAJOR = 10
$MAX_MINOR = 10
$MAX_PATCH = 100

function Get-AllTags {
    """获取所有 git tag"""
    try {
        $tags = git tag -l 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 获取标签失败" -ForegroundColor Red
            return @()
        }
        $tagList = $tags | Where-Object { $_ -match '\S' }
        Write-Host "✓ 找到 $($tagList.Count) 个标签" -ForegroundColor Green
        return $tagList
    }
    catch {
        Write-Host "✗ 获取标签失败: $_" -ForegroundColor Red
        return @()
    }
}

function Parse-Version {
    param([string]$tag)
    
    if ($tag -match '^v(\d+)\.(\d+)\.(\d+)$') {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = [int]$matches[3]
        
        if ($major -le $MAX_MAJOR -and $minor -le $MAX_MINOR -and $patch -le $MAX_PATCH) {
            return @{
                Major = $major
                Minor = $minor
                Patch = $patch
                Valid = $true
            }
        }
    }
    
    return @{ Valid = $false }
}

function Find-MaxVersion {
    param([array]$tags)
    
    $versions = @()
    foreach ($tag in $tags) {
        $version = Parse-Version $tag
        if ($version.Valid) {
            $versions += $version
        }
    }
    
    if ($versions.Count -eq 0) {
        Write-Host "⚠ 未找到有效的版本标签" -ForegroundColor Yellow
        return $null
    }
    
    $maxVersion = $versions | Sort-Object { $_.Major * 10000 + $_.Minor * 100 + $_.Patch } | Select-Object -Last 1
    Write-Host "✓ 当前最大版本: v$($maxVersion.Major).$($maxVersion.Minor).$($maxVersion.Patch)" -ForegroundColor Green
    
    return $maxVersion
}

function Increment-Version {
    param($version)
    
    if ($null -eq $version) {
        return @{ Major = 0; Minor = 0; Patch = 1; Valid = $true }
    }
    
    # 尝试递增 patch
    if ($version.Patch -lt $MAX_PATCH) {
        return @{
            Major = $version.Major
            Minor = $version.Minor
            Patch = $version.Patch + 1
            Valid = $true
        }
    }
    
    # patch 已达最大，递增 minor
    if ($version.Minor -lt $MAX_MINOR) {
        return @{
            Major = $version.Major
            Minor = $version.Minor + 1
            Patch = 0
            Valid = $true
        }
    }
    
    # minor 已达最大，递增 major
    if ($version.Major -lt $MAX_MAJOR) {
        return @{
            Major = $version.Major + 1
            Minor = 0
            Patch = 0
            Valid = $true
        }
    }
    
    Write-Host "✗ 版本号已达到最大值 v$MAX_MAJOR.$MAX_MINOR.$MAX_PATCH" -ForegroundColor Red
    return @{ Valid = $false }
}

function Format-Version {
    param($version)
    return "v$($version.Major).$($version.Minor).$($version.Patch)"
}

function Test-GitStatus {
    """检查 git 状态"""
    $status = git status --porcelain 2>&1
    if ($status) {
        Write-Host "⚠ 警告：工作区有未提交的更改" -ForegroundColor Yellow
        Write-Host $status
        $response = Read-Host "是否继续？(y/N)"
        return $response -eq 'y'
    }
    return $true
}

function New-GitTag {
    param(
        [string]$tag,
        [string]$message = "Release $tag"
    )
    
    try {
        git tag -a $tag -m $message 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 创建标签失败" -ForegroundColor Red
            return $false
        }
        Write-Host "✓ 成功创建标签: $tag" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ 创建标签失败: $_" -ForegroundColor Red
        return $false
    }
}

function Push-GitTag {
    param([string]$tag)
    
    try {
        git push origin $tag 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 推送标签失败" -ForegroundColor Red
            return $false
        }
        Write-Host "✓ 成功推送标签到远程: $tag" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ 推送标签失败: $_" -ForegroundColor Red
        return $false
    }
}

# 主流程
Write-Host "=" * 60
Write-Host "自动版本发布脚本" -ForegroundColor Cyan
Write-Host "=" * 60

# 1. 获取所有标签
$tags = Get-AllTags

# 2. 找到最大版本号
$maxVersion = Find-MaxVersion $tags

# 3. 递增版本号
$nextVersion = Increment-Version $maxVersion
if (-not $nextVersion.Valid) {
    exit 1
}

$nextTag = Format-Version $nextVersion

Write-Host ""
Write-Host "📦 新版本: $nextTag" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 演习模式：以下是将要执行的操作" -ForegroundColor Yellow
    Write-Host "  1. 创建标签: $nextTag"
    Write-Host "  2. 推送到远程: git push origin $nextTag"
    exit 0
}

# 4. 检查 git 状态
if (-not (Test-GitStatus)) {
    exit 1
}

# 5. 确认操作
Write-Host "即将创建并推送标签: $nextTag" -ForegroundColor Yellow
$response = Read-Host "确认继续？(Y/n)"
if ($response -eq 'n') {
    Write-Host "✗ 操作已取消" -ForegroundColor Red
    exit 1
}

# 6. 创建标签
if (-not (New-GitTag $nextTag)) {
    exit 1
}

# 7. 推送标签
if (-not (Push-GitTag $nextTag)) {
    Write-Host "⚠ 标签已创建但推送失败，可手动执行：" -ForegroundColor Yellow
    Write-Host "   git push origin $nextTag"
    exit 1
}

Write-Host ""
Write-Host "=" * 60
Write-Host "✓ 发布成功！新版本: $nextTag" -ForegroundColor Green
Write-Host "=" * 60
