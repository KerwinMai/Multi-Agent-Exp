"""
数据分析子智能体

负责对查询结果进行深度分析，生成洞察和建议。
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path

from langchain_core.language_models import BaseLLM

import sys
sys.path.append(str(Path(__file__).parent.parent))
from prompts import get_analysis_prompt


class DataAnalysisAgent:
    """数据分析子智能体"""
    
    def __init__(self, llm: BaseLLM):
        self.llm = llm
    
    def _parse_data(self, data_str: str) -> Optional[Any]:
        """解析数据字符串"""
        try:
            return json.loads(data_str)
        except:
            return None
    
    def _prepare_data_summary(self, data: Any) -> str:
        """准备数据摘要
        
        Args:
            data: 解析后的数据
            
        Returns:
            数据摘要文本
        """
        if isinstance(data, list):
            if len(data) == 0:
                return "数据为空"
            
            summary = f"数据总数: {len(data)}条记录\n"
            
            # 显示前几条数据
            if len(data) > 0:
                summary += f"数据示例:\n"
                for i, item in enumerate(data[:3]):
                    summary += f"  记录{i+1}: {json.dumps(item, ensure_ascii=False)}\n"
            
            # 如果有数值字段，计算统计信息
            if len(data) > 0 and isinstance(data[0], dict):
                numeric_fields = []
                for key, value in data[0].items():
                    if isinstance(value, (int, float)):
                        numeric_fields.append(key)
                
                if numeric_fields:
                    summary += "\n数值字段统计:\n"
                    for field in numeric_fields:
                        values = [item[field] for item in data if field in item and isinstance(item[field], (int, float))]
                        if values:
                            summary += f"  {field}:\n"
                            summary += f"    - 最小值: {min(values)}\n"
                            summary += f"    - 最大值: {max(values)}\n"
                            summary += f"    - 平均值: {sum(values)/len(values):.2f}\n"
            
            return summary
        
        elif isinstance(data, dict):
            return f"单条记录: {json.dumps(data, ensure_ascii=False)}"
        
        else:
            return str(data)
    
    def analyze(self, data: str, context: str = "") -> Dict[str, Any]:
        """分析数据
        
        Args:
            data: JSON格式的数据字符串
            context: 上下文信息（如原始问题）
            
        Returns:
            包含分析结果和错误信息的字典
        """
        result = {
            "analysis": None,
            "error": None
        }
        
        try:
            # 解析数据
            parsed_data = self._parse_data(data)
            
            if parsed_data is None:
                result["error"] = "无法解析数据"
                return result
            
            # 检查是否有错误
            if isinstance(parsed_data, dict) and "error" in parsed_data:
                result["error"] = f"数据包含错误: {parsed_data['error']}"
                return result
            
            # 准备数据摘要
            data_summary = self._prepare_data_summary(parsed_data)
            
            # 生成分析prompt
            prompt = get_analysis_prompt(
                data_summary=data_summary,
                raw_data=data,
                context=context
            )
            
            # 调用LLM进行分析
            analysis = self.llm.invoke(prompt)
            result["analysis"] = analysis
            
        except Exception as e:
            result["error"] = f"分析失败: {str(e)}"
        
        return result

