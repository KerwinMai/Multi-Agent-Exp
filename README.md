# 多智能体数据查询系统 v2.0

基于LangGraph的一主两从多智能体架构，实现智能的数据库查询和分析功能，支持长短期记忆。

## 架构设计

```
主智能体 (MasterAgent)
├── 意图识别：判断用户问题类型（结合用户偏好）
├── 任务路由：选择合适的处理路径
├── 短期记忆：智能压缩对话历史（LLM总结）
├── 长期记忆：跨会话用户偏好和知识
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

**3. 双层记忆系统** ⭐NEW
- **短期记忆（MemorySaver）**
  - 会话内对话历史保留
  - 智能压缩：消息>10条或token>1000时LLM自动总结
  - 支持引用历史查询结果
- **长期记忆（LongTermMemory）**
  - 跨会话持久化用户偏好和知识
  - 自动提取：对话≥4条消息时自动提取
  - 个性化上下文：意图识别时注入用户历史
  - SQLite存储：users、user_preferences、user_knowledge

**4. 用户会话管理** ⭐NEW
- 用户登录系统（user_id）
- 会话隔离（session_id）
- 智能thread_id生成（user_id_session_id）
- 特殊命令：`new`（新会话）、`info`（查看信息）

**5. MCP集成** - 通过MCP协议执行SQL
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
python init_db.py              # 初始化业务数据库
python init_memory_db.py       # 初始化长期记忆数据库
```

### 4. 运行系统
```bash
cd intelligent_data_query
python agent.py
```

系统会提示输入用户ID，输入后即可开始使用。同一user_id可以在不同会话中保留个人偏好。

**特殊命令**：
- `new` - 开始新会话（清空短期记忆，保留长期记忆）
- `info` - 查看当前用户信息和偏好
- `exit/quit` - 退出系统

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
├── agents/                      # 智能体模块
│   ├── master_agent.py         # 主智能体（含记忆管理）
│   ├── sql_agent.py            # SQL查询子智能体
│   └── analysis_agent.py       # 数据分析子智能体
├── memory/                      # 记忆模块 ⭐NEW
│   ├── long_term_memory.py     # 长期记忆管理器
│   └── memory_extractor.py     # 记忆提取器
├── agent.py                    # 主入口（含用户登录）
├── prompts.py                  # 提示词定义
├── test_questions.py           # 测试问题集
├── config/
│   └── config.yaml             # 配置文件（含记忆配置）
├── data/
│   ├── company.db              # 业务数据库
│   ├── long_term_memory.db     # 长期记忆数据库 ⭐NEW
│   ├── init_db.py              # 业务数据库初始化
│   └── init_memory_db.py       # 记忆数据库初始化 ⭐NEW
└── mcp_sql_server.py           # MCP SQL服务器
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

# 记忆配置 ⭐NEW
memory:
  long_term_db: "./data/long_term_memory.db"  # 长期记忆数据库路径
  short_term_max_tokens: 1000                  # 短期记忆最大token数
  compression_threshold: 10                    # 超过N条消息开始压缩
  auto_extract_knowledge: true                 # 自动提取长期记忆
```

## 技术栈

- **LangGraph**: 工作流编排
- **LangChain**: LLM调用和管理
- **通义千问**: 大语言模型
- **MCP**: Model Context Protocol
- **SQLite**: 数据库
- **Rich**: 终端美化

## 已完成功能 ✅

- ~~**支持长期记忆**~~: 使用SQLite持久化用户偏好和知识 ✅ (v2.0)
- ~~**上下文压缩**~~: LLM智能总结对话历史 ✅ (v2.0)
- ~~**用户系统**~~: 支持多用户登录和会话管理 ✅ (v2.0)
- ~~**自动记忆提取**~~: 从对话中自动提取用户偏好 ✅ (v2.0)

## 下一步计划扩展

### 1. 长期记忆深度应用
- **个性化查询推荐**: 基于用户历史自动推荐相关查询
- **智能查询补全**: 根据用户偏好自动补全查询参数
- **偏好自适应展示**: 自动调整数据展示格式（表格/图表/摘要）
- **用户行为分析**: 分析用户查询模式，提供优化建议
- **团队协作记忆**: 支持团队成员共享特定知识库

### 2. 记忆检索优化
- **向量检索**: 使用ChromaDB替代简单的LIKE匹配
- **记忆衰减机制**: 根据时间和访问频率调整知识置信度
- **多模态记忆**: 保存查询结果的图表、文件等
- **全文搜索**: 为user_knowledge添加FTS5全文索引

### 3. 智能体扩展
- **报表生成子智能体**: 自动生成PDF/Excel报表
- **数据可视化子智能体**: 生成图表和仪表板
- **异常检测子智能体**: 主动发现数据异常并告警

### 4. 技术优化
- **Schema智能检索**: 大型数据库只获取相关表结构
- **支持更多数据源**: MySQL、PostgreSQL、ClickHouse等
- **并行调用优化**: 对独立任务实现并行处理
- **流式输出**: 支持实时流式返回分析结果

## 注意事项

- 确保设置 `DASHSCOPE_API_KEY` 环境变量
- 初始化业务数据库和长期记忆数据库
- 安装所有依赖包
- 使用相同的 `user_id` 可以跨会话保留个人偏好
- 长期记忆数据库建议定期备份

## 更新日志

### v2.0 (2025.10.21)
- ✨ 新增：长期记忆系统（用户偏好、知识跨会话持久化）
- ✨ 新增：短期记忆智能压缩（LLM自动总结）
- ✨ 新增：用户登录和会话管理系统
- ✨ 新增：自动记忆提取（从对话中提取偏好和知识）
- 🔧 优化：意图识别注入用户历史上下文
- 🔧 优化：messages使用add_messages累加器

### v1.0 (2025.10.16)
- 🎉 初始版本
- ✨ 一主两从多智能体架构
- ✨ 意图识别和智能路由
- ✨ NL2SQL查询和数据分析
- ✨ 短期会话记忆（MemorySaver）
