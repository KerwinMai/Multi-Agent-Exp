"""
SQL查询子智能体

负责将自然语言转换为SQL并执行查询。
"""

import json
import sqlite3
import sys
import asyncio
from typing import Dict, Any
from pathlib import Path

from langchain_core.language_models import BaseLLM
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.append(str(Path(__file__).parent.parent))
from prompts import get_few_shot_prompt


class SQLQueryAgent:
    """SQL查询子智能体"""
    
    def __init__(self, llm: BaseLLM, db_path: str, num_examples: int = 3):
        """初始化SQL查询智能体
        
        Args:
            llm: 语言模型实例
            db_path: 数据库路径
            num_examples: Few-shot示例数量
        """
        self.llm = llm
        self.db_path = db_path
        self.num_examples = num_examples
    
    def _get_schema(self) -> str:
        """获取数据库Schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        schema_text = ""
        for table in tables:
            table_name = table[0]
            schema_text += f"\n表：{table_name}\n"
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                cid, name, dtype, notnull, default, pk = col
                pk_text = " (主键)" if pk else ""
                notnull_text = " NOT NULL" if notnull else ""
                schema_text += f"  - {name}: {dtype}{notnull_text}{pk_text}\n"
        
        conn.close()
        return schema_text.strip()
    
    def _generate_sql(self, question: str) -> str:
        """生成SQL语句
        
        Args:
            question: 用户问题
            
        Returns:
            SQL语句
        """
        schema = self._get_schema()
        prompt = get_few_shot_prompt(
            question=question,
            schema=schema,
            num_examples=self.num_examples
        )
        
        sql = self.llm.invoke(prompt).strip()
        
        # 清理SQL（移除可能的前缀和标记）
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]
        
        # 移除常见的中英文前缀
        prefixes = ["SQL：", "SQL:", "sql:", "sql："]
        for prefix in prefixes:
            if sql.startswith(prefix):
                sql = sql[len(prefix):]
                break
        
        if sql.endswith("```"):
            sql = sql[:-3]
        
        return sql.strip()
    
    async def _execute_sql_via_mcp(self, sql: str) -> str:
        """通过MCP工具执行SQL
        
        Args:
            sql: SQL语句
            
        Returns:
            查询结果JSON字符串
        """
        mcp_script = Path(__file__).parent.parent / "mcp_sql_server.py"
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(mcp_script)]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化MCP会话
                await session.initialize()
                
                # 调用execute_sql工具
                result = await session.call_tool(
                    "execute_sql", 
                    arguments={"sql": sql}
                )
                
                if result.content:
                    return result.content[0].text
                return json.dumps({"error": "无返回结果"})
    
    def query(self, question: str) -> Dict[str, Any]:
        """执行查询
        
        Args:
            question: 用户问题
            
        Returns:
            包含SQL、结果和错误信息的字典
        """
        result = {
            "sql": None,
            "data": None,
            "error": None
        }
        
        try:
            # 生成SQL
            sql = self._generate_sql(question)
            result["sql"] = sql
            
            if not sql:
                result["error"] = "未能生成有效的SQL"
                return result
            
            # 执行SQL
            query_result = asyncio.run(self._execute_sql_via_mcp(sql))
            result["data"] = query_result
            
            # 检查是否有错误
            result_data = json.loads(query_result)
            if isinstance(result_data, dict) and "error" in result_data:
                result["error"] = result_data["error"]
                
        except Exception as e:
            result["error"] = f"查询失败: {str(e)}"
        
        return result

