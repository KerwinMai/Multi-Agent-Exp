"""
LangGraph智能问答Agent - 多智能体版本

基于LangGraph工作流的自然语言数据库查询和分析系统。
支持一主两从的多智能体架构：
- 主智能体：MasterAgent（意图识别、路由、汇总）
- 子智能体1：SQLQueryAgent（数据库查询）
- 子智能体2：DataAnalysisAgent（数据分析）
"""

import os
from typing import Dict, Any

from langchain_community.llms import Tongyi
from langchain_core.language_models import BaseLLM
import yaml

from agents import MasterAgent

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


class MultiAgentSystem:
    """多智能体系统 - 主入口类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化多智能体系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.llm = self._init_llm()
        self.db_path = self.config["database"]["path"]
        
        # 初始化主智能体（内部会初始化两个子智能体）
        self.master_agent = MasterAgent(
            llm=self.llm,
            db_path=self.db_path,
            num_examples=self.config["nl2sql"]["num_examples"]
        )
        
        # 用于区分不同会话的线程ID
        self.thread_id = "default"
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 替换环境变量
        def replace_env_vars(obj):
            if isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            if isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                return os.getenv(obj[2:-1], obj)
            return obj
        
        return replace_env_vars(config)
    
    def _init_llm(self) -> BaseLLM:
        """初始化语言模型"""
        llm_config = self.config["llm"]
        
        if llm_config["provider"] == "dashscope":
            return Tongyi(
                model=llm_config["model"],
                temperature=llm_config["temperature"],
                max_tokens=llm_config["max_tokens"],
                dashscope_api_key=llm_config["api_key"]
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config['provider']}")
    
    def query(self, question: str) -> str:
        """执行查询
        
        Args:
            question: 用户问题
        
        Returns:
            回答结果
        """
        return self.master_agent.query(question, thread_id=self.thread_id)
    
    def set_thread_id(self, thread_id: str):
        """设置会话线程ID
        
        Args:
            thread_id: 线程ID，用于区分不同的会话
        """
        self.thread_id = thread_id

SQLAgent = MultiAgentSystem

def main():

    console.print(Panel.fit(
        "[cyan]LangGraph 多智能体数据查询系统[/cyan]\n"
        "主智能体 + SQL查询 + 数据分析\n"
        "智能路由 · 深度分析 · 会话记忆",
        border_style="cyan"
    ))
    console.print()
    
    if not os.getenv("DASHSCOPE_API_KEY"):
        console.print("[red]错误：未设置 DASHSCOPE_API_KEY 环境变量[/red]")
        return
    
    agent = MultiAgentSystem()
    console.print("[green]系统已就绪[/green]\n")
    
    while True:
        question = Prompt.ask("[cyan]请输入问题[/cyan]")
        
        if question.lower() in ['exit', 'quit', 'q']:
            console.print("\n[yellow]再见[/yellow]")
            break
        
        if not question.strip():
            continue
        
        answer = agent.query(question)
        console.print(Panel(answer, title="回答", border_style="green"))
        console.print()


if __name__ == "__main__":
    main()
