"""
版本控制服务
提供策略版本管理、比较和差异分析功能
"""

import difflib
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.strategy import Strategy, StrategyVersion
from ..models.user import User

logger = logging.getLogger(__name__)


@dataclass
class DiffLine:
    """差异行"""
    line_number: int
    content: str
    type: str  # 'added', 'removed', 'unchanged', 'modified'
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None


@dataclass
class DiffBlock:
    """差异块"""
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine]


@dataclass
class VersionDiff:
    """版本差异"""
    old_version: StrategyVersion
    new_version: StrategyVersion
    diff_blocks: List[DiffBlock]
    stats: Dict[str, int]  # 统计信息：added, removed, modified


@dataclass
class VersionBranch:
    """版本分支"""
    name: str
    description: str
    base_version_id: int
    head_version_id: int
    created_at: datetime
    is_active: bool


class VersionControlService:
    """版本控制服务"""
    
    def __init__(self):
        pass
    
    def compare_versions(self, db: Session, version1_id: int, version2_id: int, user_id: int) -> VersionDiff:
        """
        比较两个版本的差异
        
        Args:
            db: 数据库会话
            version1_id: 版本1 ID
            version2_id: 版本2 ID
            user_id: 用户ID
            
        Returns:
            VersionDiff: 版本差异信息
        """
        # 获取版本信息
        version1 = db.query(StrategyVersion).filter(
            StrategyVersion.id == version1_id,
            StrategyVersion.user_id == user_id
        ).first()
        
        version2 = db.query(StrategyVersion).filter(
            StrategyVersion.id == version2_id,
            StrategyVersion.user_id == user_id
        ).first()
        
        if not version1 or not version2:
            raise ValueError("版本不存在或无权限访问")
        
        # 比较代码差异
        diff_blocks = self._generate_diff_blocks(version1.code, version2.code)
        
        # 计算统计信息
        stats = self._calculate_diff_stats(diff_blocks)
        
        return VersionDiff(
            old_version=version1,
            new_version=version2,
            diff_blocks=diff_blocks,
            stats=stats
        )
    
    def _generate_diff_blocks(self, old_code: str, new_code: str) -> List[DiffBlock]:
        """生成差异块"""
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()
        
        # 使用difflib生成差异
        differ = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=3  # 上下文行数
        )
        
        diff_blocks = []
        current_block = None
        old_line_num = 0
        new_line_num = 0
        
        for line in differ:
            if line.startswith('@@'):
                # 解析差异块头部
                if current_block:
                    diff_blocks.append(current_block)
                
                # 解析行号信息
                parts = line.split()
                old_range = parts[1][1:]  # 去掉'-'
                new_range = parts[2][1:]  # 去掉'+'
                
                old_start, old_count = self._parse_range(old_range)
                new_start, new_count = self._parse_range(new_range)
                
                current_block = DiffBlock(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    lines=[]
                )
                
                old_line_num = old_start
                new_line_num = new_start
            
            elif line.startswith('-'):
                # 删除的行
                if current_block:
                    current_block.lines.append(DiffLine(
                        line_number=old_line_num,
                        content=line[1:],
                        type='removed',
                        old_line_number=old_line_num
                    ))
                    old_line_num += 1
            
            elif line.startswith('+'):
                # 添加的行
                if current_block:
                    current_block.lines.append(DiffLine(
                        line_number=new_line_num,
                        content=line[1:],
                        type='added',
                        new_line_number=new_line_num
                    ))
                    new_line_num += 1
            
            elif line.startswith(' '):
                # 未改变的行
                if current_block:
                    current_block.lines.append(DiffLine(
                        line_number=old_line_num,
                        content=line[1:],
                        type='unchanged',
                        old_line_number=old_line_num,
                        new_line_number=new_line_num
                    ))
                    old_line_num += 1
                    new_line_num += 1
        
        if current_block:
            diff_blocks.append(current_block)
        
        return diff_blocks
    
    def _parse_range(self, range_str: str) -> Tuple[int, int]:
        """解析范围字符串"""
        if ',' in range_str:
            start, count = range_str.split(',')
            return int(start), int(count)
        else:
            return int(range_str), 1
    
    def _calculate_diff_stats(self, diff_blocks: List[DiffBlock]) -> Dict[str, int]:
        """计算差异统计"""
        stats = {
            'added': 0,
            'removed': 0,
            'modified': 0,
            'unchanged': 0
        }
        
        for block in diff_blocks:
            for line in block.lines:
                if line.type == 'added':
                    stats['added'] += 1
                elif line.type == 'removed':
                    stats['removed'] += 1
                elif line.type == 'unchanged':
                    stats['unchanged'] += 1
        
        # 计算修改的行数（添加和删除的较小值）
        stats['modified'] = min(stats['added'], stats['removed'])
        
        return stats
    
    def get_version_history(self, db: Session, strategy_id: int, user_id: int) -> List[StrategyVersion]:
        """获取策略版本历史"""
        versions = db.query(StrategyVersion).filter(
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.user_id == user_id
        ).order_by(StrategyVersion.version_number.desc()).all()
        
        return versions
    
    def create_version_from_code(
        self, 
        db: Session, 
        strategy_id: int, 
        code: str, 
        version_name: str,
        description: str,
        change_log: str,
        user_id: int,
        is_major_version: bool = False
    ) -> StrategyVersion:
        """从代码创建新版本"""
        try:
            # 获取策略信息
            strategy = db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            if not strategy:
                raise ValueError("策略不存在或无权限访问")
            
            # 获取下一个版本号
            latest_version = db.query(StrategyVersion).filter(
                StrategyVersion.strategy_id == strategy_id
            ).order_by(StrategyVersion.version_number.desc()).first()
            
            next_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # 创建新版本
            new_version = StrategyVersion(
                version_number=next_version_number,
                version_name=version_name,
                description=description,
                code=code,
                entry_point=strategy.entry_point,
                parameters=strategy.parameters,
                change_log=change_log,
                is_major_version=is_major_version,
                strategy_id=strategy_id,
                user_id=user_id
            )
            
            db.add(new_version)
            
            # 更新策略的当前版本
            strategy.version = next_version_number
            strategy.code = code
            
            db.commit()
            db.refresh(new_version)
            
            logger.info(f"创建策略版本: {strategy_id} v{next_version_number}")
            return new_version
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建版本失败: {e}")
            raise
    
    def rollback_to_version(
        self, 
        db: Session, 
        strategy_id: int, 
        target_version_id: int, 
        user_id: int
    ) -> Strategy:
        """回滚到指定版本"""
        try:
            # 获取策略和目标版本
            strategy = db.query(Strategy).filter(
                Strategy.id == strategy_id,
                Strategy.user_id == user_id
            ).first()
            
            target_version = db.query(StrategyVersion).filter(
                StrategyVersion.id == target_version_id,
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.user_id == user_id
            ).first()
            
            if not strategy or not target_version:
                raise ValueError("策略或版本不存在")
            
            # 检查策略是否正在运行
            if strategy.is_running:
                raise ValueError("策略正在运行，无法回滚")
            
            # 创建回滚版本
            rollback_version = self.create_version_from_code(
                db=db,
                strategy_id=strategy_id,
                code=target_version.code,
                version_name=f"回滚到v{target_version.version_number}",
                description=f"从版本{target_version.version_number}回滚",
                change_log=f"回滚到版本{target_version.version_number}: {target_version.version_name}",
                user_id=user_id,
                is_major_version=False
            )
            
            # 更新策略信息
            strategy.entry_point = target_version.entry_point
            strategy.parameters = target_version.parameters
            
            db.commit()
            db.refresh(strategy)
            
            logger.info(f"策略回滚成功: {strategy_id} -> v{target_version.version_number}")
            return strategy
            
        except Exception as e:
            db.rollback()
            logger.error(f"版本回滚失败: {e}")
            raise
    
    def create_branch(
        self, 
        db: Session, 
        strategy_id: int, 
        branch_name: str, 
        description: str,
        base_version_id: int,
        user_id: int
    ) -> VersionBranch:
        """创建版本分支"""
        # 注意：这里简化实现，实际项目中可能需要更复杂的分支管理
        try:
            # 验证基础版本
            base_version = db.query(StrategyVersion).filter(
                StrategyVersion.id == base_version_id,
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.user_id == user_id
            ).first()
            
            if not base_version:
                raise ValueError("基础版本不存在")
            
            # 创建分支（这里简化为创建一个新版本）
            branch_version = self.create_version_from_code(
                db=db,
                strategy_id=strategy_id,
                code=base_version.code,
                version_name=f"分支: {branch_name}",
                description=description,
                change_log=f"从版本{base_version.version_number}创建分支: {branch_name}",
                user_id=user_id,
                is_major_version=True
            )
            
            # 返回分支信息
            branch = VersionBranch(
                name=branch_name,
                description=description,
                base_version_id=base_version_id,
                head_version_id=branch_version.id,
                created_at=datetime.now(),
                is_active=True
            )
            
            logger.info(f"创建版本分支: {strategy_id} - {branch_name}")
            return branch
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建分支失败: {e}")
            raise
    
    def merge_versions(
        self, 
        db: Session, 
        strategy_id: int, 
        source_version_id: int, 
        target_version_id: int,
        merge_message: str,
        user_id: int
    ) -> StrategyVersion:
        """合并版本"""
        try:
            # 获取源版本和目标版本
            source_version = db.query(StrategyVersion).filter(
                StrategyVersion.id == source_version_id,
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.user_id == user_id
            ).first()
            
            target_version = db.query(StrategyVersion).filter(
                StrategyVersion.id == target_version_id,
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.user_id == user_id
            ).first()
            
            if not source_version or not target_version:
                raise ValueError("源版本或目标版本不存在")
            
            # 简化的合并逻辑：使用源版本的代码
            # 实际项目中可能需要更复杂的三路合并算法
            merged_code = source_version.code
            
            # 创建合并版本
            merged_version = self.create_version_from_code(
                db=db,
                strategy_id=strategy_id,
                code=merged_code,
                version_name=f"合并v{source_version.version_number}到v{target_version.version_number}",
                description=merge_message,
                change_log=f"合并版本{source_version.version_number}到{target_version.version_number}: {merge_message}",
                user_id=user_id,
                is_major_version=True
            )
            
            logger.info(f"版本合并成功: {strategy_id} v{source_version.version_number} -> v{target_version.version_number}")
            return merged_version
            
        except Exception as e:
            db.rollback()
            logger.error(f"版本合并失败: {e}")
            raise
    
    def get_version_tree(self, db: Session, strategy_id: int, user_id: int) -> Dict[str, Any]:
        """获取版本树结构"""
        versions = self.get_version_history(db, strategy_id, user_id)
        
        # 构建版本树（简化实现）
        version_tree = {
            'strategy_id': strategy_id,
            'versions': [],
            'branches': [],
            'total_versions': len(versions)
        }
        
        for version in versions:
            version_node = {
                'id': version.id,
                'version_number': version.version_number,
                'version_name': version.version_name,
                'description': version.description,
                'is_major_version': version.is_major_version,
                'created_at': version.created_at.isoformat() if version.created_at else None,
                'change_log': version.change_log,
                'parent_version': version.version_number - 1 if version.version_number > 1 else None
            }
            version_tree['versions'].append(version_node)
        
        return version_tree
    
    def export_version_diff(self, version_diff: VersionDiff, format: str = 'unified') -> str:
        """导出版本差异"""
        if format == 'unified':
            return self._export_unified_diff(version_diff)
        elif format == 'side_by_side':
            return self._export_side_by_side_diff(version_diff)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_unified_diff(self, version_diff: VersionDiff) -> str:
        """导出统一差异格式"""
        lines = []
        lines.append(f"--- 版本 {version_diff.old_version.version_number}: {version_diff.old_version.version_name}")
        lines.append(f"+++ 版本 {version_diff.new_version.version_number}: {version_diff.new_version.version_name}")
        lines.append("")
        
        for block in version_diff.diff_blocks:
            lines.append(f"@@ -{block.old_start},{block.old_count} +{block.new_start},{block.new_count} @@")
            
            for line in block.lines:
                if line.type == 'removed':
                    lines.append(f"-{line.content}")
                elif line.type == 'added':
                    lines.append(f"+{line.content}")
                else:
                    lines.append(f" {line.content}")
        
        return '\n'.join(lines)
    
    def _export_side_by_side_diff(self, version_diff: VersionDiff) -> str:
        """导出并排差异格式"""
        # 简化实现，实际项目中可能需要更复杂的格式化
        lines = []
        lines.append(f"版本比较: v{version_diff.old_version.version_number} vs v{version_diff.new_version.version_number}")
        lines.append("=" * 80)
        
        for block in version_diff.diff_blocks:
            lines.append(f"差异块: 行 {block.old_start}-{block.old_start + block.old_count}")
            lines.append("-" * 40)
            
            for line in block.lines:
                if line.type == 'removed':
                    lines.append(f"< {line.content}")
                elif line.type == 'added':
                    lines.append(f"> {line.content}")
                else:
                    lines.append(f"  {line.content}")
        
        return '\n'.join(lines)


# 全局版本控制服务实例
version_control_service = VersionControlService()