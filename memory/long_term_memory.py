"""
长期记忆管理器

负责用户偏好、知识的存储、检索和更新。
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class LongTermMemory:
    """长期记忆管理器 - 跨会话持久化用户信息"""
    
    def __init__(self, memory_db_path: str = "./data/long_term_memory.db"):
        """初始化长期记忆管理器
        
        Args:
            memory_db_path: 长期记忆数据库路径
        """
        self.db_path = memory_db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """确保数据库文件存在，如果不存在则初始化"""
        if not Path(self.db_path).exists():
            from data.init_memory_db import init_memory_database
            init_memory_database(self.db_path)
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典形式的结果
        return conn
    
    # ==================== 用户管理 ====================
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户概况
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典，如果用户不存在则返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, created_at, last_active
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def create_or_update_user(self, user_id: str) -> bool:
        """创建或更新用户记录
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (user_id, created_at, last_active)
                VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_active = CURRENT_TIMESTAMP
            """, (user_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"创建/更新用户失败: {e}")
            return False
        finally:
            conn.close()
    
    def update_user_activity(self, user_id: str) -> bool:
        """更新用户最后活跃时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        return self.create_or_update_user(user_id)
    
    # ==================== 用户偏好管理 ====================
    
    def save_preference(self, user_id: str, key: str, value: str) -> bool:
        """保存用户偏好
        
        Args:
            user_id: 用户ID
            key: 偏好键（如：favorite_department, display_format）
            value: 偏好值
            
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 确保用户存在
            self.create_or_update_user(user_id)
            
            cursor.execute("""
                INSERT INTO user_preferences (user_id, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, key, value))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"保存偏好失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_preference(self, user_id: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取用户偏好
        
        Args:
            user_id: 用户ID
            key: 偏好键
            default: 默认值
            
        Returns:
            偏好值，如果不存在则返回默认值
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value
            FROM user_preferences
            WHERE user_id = ? AND key = ?
        """, (user_id, key))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row["value"]
        return default
    
    def get_all_preferences(self, user_id: str) -> Dict[str, str]:
        """获取用户的所有偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            偏好字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key, value
            FROM user_preferences
            WHERE user_id = ?
        """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return {row["key"]: row["value"] for row in rows}
    
    # ==================== 用户知识管理 ====================
    
    def save_knowledge(
        self, 
        user_id: str, 
        category: str, 
        content: str, 
        confidence: float = 0.8
    ) -> bool:
        """保存用户知识
        
        Args:
            user_id: 用户ID
            category: 知识分类（如：常问问题、业务领域、使用习惯）
            content: 知识内容
            confidence: 置信度（0-1）
            
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 确保用户存在
            self.create_or_update_user(user_id)
            
            cursor.execute("""
                INSERT INTO user_knowledge (user_id, category, content, confidence, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, category, content, confidence))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"保存知识失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_knowledge_by_category(
        self, 
        user_id: str, 
        category: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """按分类获取用户知识
        
        Args:
            user_id: 用户ID
            category: 知识分类
            limit: 返回数量限制
            
        Returns:
            知识列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT knowledge_id, category, content, confidence, created_at
            FROM user_knowledge
            WHERE user_id = ? AND category = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, category, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_relevant_knowledge(
        self, 
        user_id: str, 
        query: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """检索与查询相关的用户知识
        
        使用简单的关键词匹配策略
        
        Args:
            user_id: 用户ID
            query: 查询文本
            top_k: 返回前K个结果
            
        Returns:
            相关知识列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 简单的关键词匹配（使用LIKE）
        # 在生产环境中可以使用FTS5全文搜索或向量检索
        cursor.execute("""
            SELECT knowledge_id, category, content, confidence, created_at
            FROM user_knowledge
            WHERE user_id = ? AND content LIKE ?
            ORDER BY confidence DESC, created_at DESC
            LIMIT ?
        """, (user_id, f"%{query}%", top_k))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_knowledge(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取用户的所有知识
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            知识列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT knowledge_id, category, content, confidence, created_at
            FROM user_knowledge
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==================== 工具方法 ====================
    
    def delete_preference(self, user_id: str, key: str) -> bool:
        """删除用户偏好
        
        Args:
            user_id: 用户ID
            key: 偏好键
            
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM user_preferences
                WHERE user_id = ? AND key = ?
            """, (user_id, key))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"删除偏好失败: {e}")
            return False
        finally:
            conn.close()
    
    def delete_knowledge(self, knowledge_id: int) -> bool:
        """删除指定知识
        
        Args:
            knowledge_id: 知识ID
            
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM user_knowledge
                WHERE knowledge_id = ?
            """, (knowledge_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"删除知识失败: {e}")
            return False
        finally:
            conn.close()

