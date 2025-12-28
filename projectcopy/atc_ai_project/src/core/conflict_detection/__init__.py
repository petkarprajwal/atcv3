"""
Conflict Detection Module
Real-time aircraft conflict detection and resolution
"""

from .real_time_conflict_detector import RealTimeConflictDetector, LiveConflictAlert, get_conflict_summary_stats

__all__ = ['RealTimeConflictDetector', 'LiveConflictAlert', 'get_conflict_summary_stats']