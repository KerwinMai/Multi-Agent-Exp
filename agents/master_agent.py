"""
主智能体

负责意图识别、任务路由、协调子智能体和结果汇总。
"""

from typing import TypedDict, Sequence, Dict, Any, Optional
from pathlib import Path

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseLLM

import sys
sys.path.append(str(Path(__file__).parent.parent))
from prompts import get_master_intent_prompt, get_summary_prompt
from agents.sql_agent import SQLQueryAgent
from agents.analysis_agent import DataAnalysisAgent


class MasterAgentState(TypedDict):
    """主智能体状态定义"""
    messages: Sequence[BaseMessage]
    user_question: str
    intent: Optional[str]  # simple_answer, sql_only, analysis_only, sql_and_analysis
    sql_result: Optional[Dict[str, Any]]
    analysis_result: Optional[Dict[str, Any]]
    final_answer: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]


class MasterAgent:
    """主智能体 - 协调SQL查询和数据分析子智能体"""
    
    def __init__(self, llm: BaseLLM, db_path: str, num_examples: int = 3):
        """初始化主智能体
        
        Args:
            llm: 语言模型实例
            db_path: 数据库路径
            num_examples: Few-shot示例数量
        """
        self.llm = llm
        self.db_path = db_path
        
        # 初始化子智能体
        self.sql_agent = SQLQueryAgent(llm, db_path, num_examples)
        self.analysis_agent = DataAnalysisAgent(llm)
        
        # 初始化短期记忆
        self.memory = MemorySaver()
        
        # 会话数据存储：保存每个thread_id的最近查询结果
        self.session_data = {}
        
        # 构建工作流
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建LangGraph状态图"""
        workflow = StateGraph(MasterAgentState)
        
        # 添加节点
        workflow.add_node("intent", self._intent_node)
        workflow.add_node("simple_answer", self._simple_answer_node)
        workflow.add_node("call_sql", self._call_sql_node)
        workflow.add_node("call_analysis", self._call_analysis_node)
        workflow.add_node("call_both", self._call_both_node)
        workflow.add_node("summarize", self._summarize_node)
        
        # 设置入口
        workflow.set_entry_point("intent")
        
        # 添加条件边 - 从意图识别到不同的处理节点
        workflow.add_conditional_edges(
            "intent",
            self._route_after_intent,
            {
                "simple_answer": "simple_answer",
                "sql_only": "call_sql",
                "analysis_only": "call_analysis",
                "sql_and_analysis": "call_both"
            }
        )
        
        # 添加边
        workflow.add_edge("simple_answer", END)
        workflow.add_edge("call_sql", "summarize")
        workflow.add_edge("call_analysis", "summarize")
        workflow.add_edge("call_both", "summarize")
        workflow.add_edge("summarize", END)
        
        # 使用MemorySaver作为checkpointer
        return workflow.compile(checkpointer=self.memory)
    
    def _get_conversation_history(self, state: MasterAgentState) -> str:
        """获取对话历史摘要
        
        Args:
            state: 当前状态
            
        Returns:
            对话历史摘要
        """
        messages = state.get("messages", [])
        if len(messages) <= 1:
            return ""
        
        # 获取最近3轮对话
        recent_messages = messages[-6:-1] if len(messages) > 6 else messages[:-1]
        
        history = []
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                history.append(f"用户: {msg.content}")
            elif isinstance(msg, AIMessage):
                history.append(f"助手: {msg.content}")
        
        return "\n".join(history) if history else ""
    
    def _intent_node(self, state: MasterAgentState) -> MasterAgentState:
        """意图识别节点"""
        question = state["user_question"]
        conversation_history = self._get_conversation_history(state)
        
        prompt = get_master_intent_prompt(question, conversation_history)
        
        try:
            response = self.llm.invoke(prompt).strip()
            
            # 清理响应，提取意图
            intent = response.lower().strip()
            
            # 验证意图是否有效
            valid_intents = ["simple_answer", "sql_only", "analysis_only", "sql_and_analysis"]
            if intent not in valid_intents:
                # 如果LLM返回的不是有效选项，尝试从响应中提取
                for valid_intent in valid_intents:
                    if valid_intent in intent:
                        intent = valid_intent
                        break
                else:
                    # 默认为sql_only
                    intent = "sql_only"
            
            state["intent"] = intent
            state["metadata"]["intent_response"] = response
            
        except Exception as e:
            state["error"] = f"意图识别失败: {str(e)}"
            state["intent"] = "simple_answer"
        
        return state
    
    def _route_after_intent(self, state: MasterAgentState) -> str:
        """意图识别后的路由"""
        return state.get("intent", "simple_answer")
    
    def _simple_answer_node(self, state: MasterAgentState) -> MasterAgentState:
        """简单回答节点"""
        question = state["user_question"]
        
        common_responses = {
            "你好": "你好！我是智能数据查询助手，可以帮你查询员工、部门、薪资等信息，还可以进行数据分析。有什么可以帮你的吗？",
            "谢谢": "不客气！还有什么其他问题吗？",
            "再见": "再见！祝你工作顺利！",
            "帮助": "我可以帮你：\n1. 查询数据库信息（如：有多少员工？）\n2. 分析数据（如：分析各部门薪资水平）\n3. 综合查询和分析（如：找出高薪员工并分析特征）",
        }
        
        # 检查常见问候
        for key, response in common_responses.items():
            if key in question:
                state["final_answer"] = response
                return state
        
        # 默认回复
        state["final_answer"] = "我是智能数据查询助手。请问有什么关于员工、部门或薪资的问题需要我帮忙吗？"
        return state
    
    def _call_sql_node(self, state: MasterAgentState) -> MasterAgentState:
        """调用SQL查询子智能体"""
        question = state["user_question"]
        thread_id = state["metadata"].get("thread_id", "default")
        
        try:
            result = self.sql_agent.query(question)
            state["sql_result"] = result
            state["metadata"]["sql_result"] = result
            
            # 保存到会话数据存储
            if thread_id not in self.session_data:
                self.session_data[thread_id] = {}
            self.session_data[thread_id]["last_sql_result"] = result
            
        except Exception as e:
            state["error"] = f"SQL查询失败: {str(e)}"
            state["sql_result"] = {"error": str(e)}
        
        return state
    
    def _call_analysis_node(self, state: MasterAgentState) -> MasterAgentState:
        """调用数据分析子智能体"""
        question = state["user_question"]
        thread_id = state["metadata"].get("thread_id", "default")
        
        # 从会话数据存储中获取最近的查询结果
        data_to_analyze = None
        
        # 首先检查当前state中是否有查询结果（可能刚刚查询过）
        if state.get("sql_result") and "data" in state["sql_result"]:
            data_to_analyze = state["sql_result"]["data"]
        # 否则从会话数据存储中获取历史查询结果
        elif thread_id in self.session_data and "last_sql_result" in self.session_data[thread_id]:
            last_sql_result = self.session_data[thread_id]["last_sql_result"]
            if last_sql_result and "data" in last_sql_result:
                data_to_analyze = last_sql_result["data"]
        
        if not data_to_analyze:
            state["error"] = "没有找到可以分析的数据。请先进行数据查询。"
            state["analysis_result"] = {"error": "无可用数据"}
            return state
        
        try:
            result = self.analysis_agent.analyze(data_to_analyze, question)
            state["analysis_result"] = result
            state["metadata"]["analysis_result"] = result
        except Exception as e:
            state["error"] = f"数据分析失败: {str(e)}"
            state["analysis_result"] = {"error": str(e)}
        
        return state
    
    def _call_both_node(self, state: MasterAgentState) -> MasterAgentState:
        """先调用SQL查询，再调用数据分析"""
        question = state["user_question"]
        thread_id = state["metadata"].get("thread_id", "default")
        
        # 第一步：SQL查询
        try:
            sql_result = self.sql_agent.query(question)
            state["sql_result"] = sql_result
            state["metadata"]["sql_result"] = sql_result
            
            # 保存到会话数据存储
            if thread_id not in self.session_data:
                self.session_data[thread_id] = {}
            self.session_data[thread_id]["last_sql_result"] = sql_result
            
            # 检查SQL查询是否成功
            if sql_result.get("error"):
                state["error"] = f"SQL查询失败: {sql_result['error']}"
                return state
            
            # 第二步：数据分析
            if sql_result.get("data"):
                analysis_result = self.analysis_agent.analyze(sql_result["data"], question)
                state["analysis_result"] = analysis_result
                state["metadata"]["analysis_result"] = analysis_result
                
                if analysis_result.get("error"):
                    state["error"] = f"数据分析失败: {analysis_result['error']}"
            else:
                state["error"] = "查询结果为空，无法进行分析"
                
        except Exception as e:
            state["error"] = f"执行失败: {str(e)}"
        
        return state
    
    def _summarize_node(self, state: MasterAgentState) -> MasterAgentState:
        """汇总结果节点"""
        question = state["user_question"]
        
        # 检查是否有错误
        if state.get("error"):
            state["final_answer"] = f"抱歉，处理过程中出现错误：{state['error']}"
            return state
        
        # 获取SQL结果和分析结果
        sql_result = state.get("sql_result")
        analysis_result = state.get("analysis_result")
        
        # 准备汇总数据
        sql_data = None
        analysis_data = None
        
        if sql_result:
            if sql_result.get("error"):
                state["final_answer"] = f"查询出错：{sql_result['error']}"
                return state
            sql_data = sql_result.get("data")
        
        if analysis_result:
            if analysis_result.get("error"):
                state["final_answer"] = f"分析出错：{analysis_result['error']}"
                return state
            analysis_data = analysis_result.get("analysis")
        
        # 使用LLM生成自然语言汇总
        try:
            prompt = get_summary_prompt(
                question=question,
                sql_result=sql_data,
                analysis_result=analysis_data
            )
            
            answer = self.llm.invoke(prompt)
            state["final_answer"] = answer
            
        except Exception as e:
            state["final_answer"] = f"生成回答时出错：{str(e)}"
        
        return state
    
    def query(self, question: str, thread_id: str = "default") -> str:
        """执行查询
        
        Args:
            question: 用户问题
            thread_id: 线程ID，用于区分不同的会话
            
        Returns:
            回答结果
        """
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "user_question": question,
            "intent": None,
            "sql_result": None,
            "analysis_result": None,
            "final_answer": None,
            "error": None,
            "metadata": {"thread_id": thread_id}  # 将thread_id添加到metadata
        }
        
        # 使用checkpointer保存会话状态
        config = {"configurable": {"thread_id": thread_id}}
        
        final_state = self.graph.invoke(initial_state, config)
        
        answer = final_state.get("final_answer", "抱歉，无法处理你的问题。")
        
        # 将回答添加到消息历史
        final_state["messages"].append(AIMessage(content=answer))
        
        return answer

