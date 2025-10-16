# 多智能体数据查询系统

基于LangGraph的一主两从多智能体架构，实现智能的数据库查询和分析功能。

## 架构设计

```
主智能体 (MasterAgent)
├── 意图识别：判断用户问题类型
├── 任务路由：选择合适的处理路径
└── 结果汇总：整合子智能体输出

子智能体1 (SQLQueryAgent)
└── NL2SQL转换、执行查询

子智能体2 (DataAnalysisAgent)
└── 数据分析、生成洞察
```

## 核心功能

**1. 意图识别** - 自动判断4种问题类型
- `simple_answer`: 简单问候
- `sql_only`: 数据查询
- `analysis_only`: 分析历史数据
- `sql_and_analysis`: 查询+分析

**2. 智能路由** - 根据意图调用不同智能体
- 主智能体直接回答 / SQL子智能体 / 数据分析子智能体 / 两者协作

**3. 会话记忆** - 支持引用历史查询结果
- 使用LangGraph的MemorySaver保存对话历史
- 通过session_data存储每个会话的查询结果

**4. MCP集成** - 通过MCP协议执行SQL
- 独立的MCP服务器处理数据库操作
- 支持扩展多数据源

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 设置API密钥
```bash
# Windows
set DASHSCOPE_API_KEY=your_api_key

# Linux/Mac
export DASHSCOPE_API_KEY=your_api_key
```

### 3. 初始化数据库
```bash
cd intelligent_data_query/data
python init_db.py
```

### 4. 运行系统
```bash
cd intelligent_data_query
python agent.py
```

## 测试问题

系统包含10个测试问题，覆盖所有意图类型：

**简单问候**
- 你好，你能帮我做什么？

**数据查询**
- 公司总共有多少个部门？每个部门分别在哪个城市？
- 研发部有多少名员工？他们的职位分布是怎样的？
- 哪些员工的基本工资超过30000元？
- 产品部和设计部分别有多少名员工？

**仅分析**
- 帮我分析一下上一次查询的数据

**查询+分析**
- 对比一下研发部、产品部和设计部的平均薪资水平
- 销售部的人员和薪资结构是怎样的？有什么特点？
- 找出薪资最高的10名员工，分析他们的职位和部门分布特征
- 分析公司各城市的人员分布和薪资差异，给出优化建议

## 目录结构

```
intelligent_data_query/
├── agents/                  # 智能体模块
│   ├── master_agent.py     # 主智能体
│   ├── sql_agent.py        # SQL查询子智能体
│   └── analysis_agent.py   # 数据分析子智能体
├── agent.py                # 主入口
├── prompts.py              # 提示词定义
├── test_questions.py       # 测试问题集
├── config/
│   └── config.yaml         # 配置文件
├── data/
│   ├── company.db          # SQLite数据库
│   └── init_db.py          # 数据库初始化
└── mcp_sql_server.py       # MCP SQL服务器
```

## 配置说明

编辑 `config/config.yaml`:

```yaml
llm:
  provider: "dashscope"
  model: "qwen-turbo"
  temperature: 0.1
  max_tokens: 2048

database:
  path: "./data/company.db"

nl2sql:
  num_examples: 3
```

## 技术栈

- **LangGraph**: 工作流编排
- **LangChain**: LLM调用和管理
- **通义千问**: 大语言模型
- **MCP**: Model Context Protocol
- **SQLite**: 数据库
- **Rich**: 终端美化

## 下一步计划扩展

1. **添加更多子智能体**: 报表生成、数据可视化等
2. **支持长期记忆**: 使用SqliteSaver持久化对话历史
3. **上下文压缩**: 针对会话历史记录进行重要性采样总结
3. **Schema智能检索**: 大型数据库只获取相关表结构
4. **支持更多数据源**: MySQL、PostgreSQL等
5. **并行调用优化**: 对独立任务实现并行处理

## 注意事项

- 确保设置 `DASHSCOPE_API_KEY` 环境变量
- 数据库路径配置正确
- 安装所有依赖包
- 使用相同的 `thread_id` 可以保持会话连续性

## 日期

- v1.0 2025.10
