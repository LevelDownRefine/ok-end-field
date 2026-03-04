#!/usr/bin/env python3
"""
自动发布新版本脚本

功能：
1. 读取所有 git tag，提取符合 vx.x.x 格式的版本号
2. 找到最大版本号并自动递增（规则：前两位最大10，最后一位最大100）
3. 创建新 tag 并推送到远程仓库

使用方法：
    python auto_release.py              # 自动递增并发布
    python auto_release.py --dry-run    # 仅显示将要创建的版本号，不实际操作
"""

import subprocess
import re
import sys
from typing import List, Tuple, Optional


class VersionManager:
    """版本管理器"""
    
    # 版本号限制
    MAX_MAJOR = 10
    MAX_MINOR = 10
    MAX_PATCH = 100
    
    def __init__(self):
        self.current_version = None
        self.next_version = None
    
    def get_all_tags(self) -> List[str]:
        """获取所有 git tag"""
        try:
            result = subprocess.run(
                ['git', 'tag', '-l'],
                capture_output=True,
                text=True,
                check=True
            )
            tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            print(f"✓ 找到 {len(tags)} 个标签")
            return tags
        except subprocess.CalledProcessError as e:
            print(f"✗ 获取标签失败: {e}")
            return []
    
    def parse_version(self, tag: str) -> Optional[Tuple[int, int, int]]:
        """解析版本号
        
        Args:
            tag: 标签名称，如 "v1.2.3"
        
        Returns:
            (major, minor, patch) 或 None（如果解析失败）
        """
        # 匹配 vx.x.x 格式
        match = re.match(r'^v(\d+)\.(\d+)\.(\d+)$', tag)
        if match:
            major, minor, patch = map(int, match.groups())
            # 验证版本号是否在有效范围内
            if (0 <= major <= self.MAX_MAJOR and 
                0 <= minor <= self.MAX_MINOR and 
                0 <= patch <= self.MAX_PATCH):
                return (major, minor, patch)
        return None
    
    def find_max_version(self, tags: List[str]) -> Optional[Tuple[int, int, int]]:
        """找到最大版本号
        
        Args:
            tags: 标签列表
        
        Returns:
            (major, minor, patch) 或 None（如果没有有效版本）
        """
        versions = []
        for tag in tags:
            version = self.parse_version(tag)
            if version:
                versions.append(version)
        
        if not versions:
            print("⚠ 未找到有效的版本标签")
            return None
        
        # 按版本号排序并取最大值
        max_version = max(versions)
        print(f"✓ 当前最大版本: v{max_version[0]}.{max_version[1]}.{max_version[2]}")
        return max_version
    
    def increment_version(self, version: Tuple[int, int, int]) -> Optional[Tuple[int, int, int]]:
        """递增版本号
        
        规则：
        1. 优先递增 patch（最后一位）
        2. 如果 patch 达到最大值，递增 minor 并重置 patch 为 0
        3. 如果 minor 达到最大值，递增 major 并重置 minor 和 patch 为 0
        4. 如果 major 达到最大值，返回 None 表示无法递增
        
        Args:
            version: 当前版本号 (major, minor, patch)
        
        Returns:
            新版本号或 None（如果无法递增）
        """
        major, minor, patch = version
        
        # 尝试递增 patch
        if patch < self.MAX_PATCH:
            return (major, minor, patch + 1)
        
        # patch 已达最大，递增 minor
        if minor < self.MAX_MINOR:
            return (major, minor + 1, 0)
        
        # minor 已达最大，递增 major
        if major < self.MAX_MAJOR:
            return (major + 1, 0, 0)
        
        # 所有位都达到最大值
        print(f"✗ 版本号已达到最大值 v{self.MAX_MAJOR}.{self.MAX_MINOR}.{self.MAX_PATCH}")
        return None
    
    def format_version(self, version: Tuple[int, int, int]) -> str:
        """格式化版本号为标签字符串"""
        return f"v{version[0]}.{version[1]}.{version[2]}"
    
    def check_git_status(self) -> bool:
        """检查 git 状态，确保工作区干净"""
        try:
            # 检查是否有未提交的更改
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                print("⚠ 警告：工作区有未提交的更改")
                print(result.stdout)
                response = input("是否继续？(y/N): ")
                return response.lower() == 'y'
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 检查 git 状态失败: {e}")
            return False
    
    def create_tag(self, tag: str, message: str = None) -> bool:
        """创建 git tag
        
        Args:
            tag: 标签名称
            message: 标签描述（可选）
        
        Returns:
            是否成功
        """
        try:
            cmd = ['git', 'tag', '-a', tag]
            if message:
                cmd.extend(['-m', message])
            else:
                cmd.extend(['-m', f'Release {tag}'])
            
            subprocess.run(cmd, check=True)
            print(f"✓ 成功创建标签: {tag}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 创建标签失败: {e}")
            return False
    
    def push_tag(self, tag: str) -> bool:
        """推送 tag 到远程仓库
        
        Args:
            tag: 标签名称
        
        Returns:
            是否成功
        """
        try:
            subprocess.run(['git', 'push', 'origin', tag], check=True)
            print(f"✓ 成功推送标签到远程: {tag}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 推送标签失败: {e}")
            return False
    
    def run(self, dry_run: bool = False) -> bool:
        """执行自动发布流程
        
        Args:
            dry_run: 是否为演习模式（仅显示将要执行的操作）
        
        Returns:
            是否成功
        """
        print("=" * 60)
        print("自动版本发布脚本")
        print("=" * 60)
        
        # 1. 获取所有标签
        tags = self.get_all_tags()
        
        # 2. 找到最大版本号
        max_version = self.find_max_version(tags)
        if max_version is None:
            # 如果没有版本，从 v0.0.1 开始
            max_version = (0, 0, 0)
            print("✓ 初始化版本号: v0.0.1")
        
        self.current_version = max_version
        
        # 3. 递增版本号
        next_version = self.increment_version(max_version)
        if next_version is None:
            return False
        
        self.next_version = next_version
        next_tag = self.format_version(next_version)
        
        print()
        print(f"📦 新版本: {next_tag}")
        print()
        
        if dry_run:
            print("🔍 演习模式：以下是将要执行的操作")
            print(f"  1. 创建标签: {next_tag}")
            print(f"  2. 推送到远程: git push origin {next_tag}")
            return True
        
        # 4. 检查 git 状态
        if not self.check_git_status():
            return False
        
        # 5. 确认操作
        print(f"即将创建并推送标签: {next_tag}")
        response = input("确认继续？(Y/n): ")
        if response.lower() == 'n':
            print("✗ 操作已取消")
            return False
        
        # 6. 创建标签
        if not self.create_tag(next_tag):
            return False
        
        # 7. 推送标签
        if not self.push_tag(next_tag):
            print("⚠ 标签已创建但推送失败，可手动执行：")
            print(f"   git push origin {next_tag}")
            return False
        
        print()
        print("=" * 60)
        print(f"✓ 发布成功！新版本: {next_tag}")
        print("=" * 60)
        return True


def main():
    """主函数"""
    # 解析命令行参数
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        return 0
    
    # 执行发布流程
    manager = VersionManager()
    success = manager.run(dry_run=dry_run)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
