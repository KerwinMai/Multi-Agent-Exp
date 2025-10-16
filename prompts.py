"""
NL2SQL提示词模板

定义系统提示词和Few-shot示例。
"""

SYSTEM_PROMPT = """你是一个SQL查询专家，负责将用户的自然语言问题转换为准确的SQL查询语句。

数据库Schema如下：
{schema}

请遵循以下规则：
1. 只生成SELECT查询，不要执行修改操作
2. 使用标准SQL语法，兼容SQLite
3. 表名和列名区分大小写
4. 日期使用 'YYYY-MM-DD' 格式
5. 如果问题不明确，倾向于返回更多信息而不是更少

直接返回SQL语句，不需要解释。"""


NL2SQL_EXAMPLES = [
    {
        "question": "平均工资最高的部门是哪个？",
        "sql": """SELECT d.dept_name, AVG(s.base_salary + s.bonus) as avg_salary
FROM departments d
JOIN employees e ON d.dept_id = e.dept_id
JOIN salaries s ON e.emp_id = s.emp_id
GROUP BY d.dept_id, d.dept_name
ORDER BY avg_salary DESC
LIMIT 1"""
    },
    {
        "question": "工资超过10000的员工有几个？",
        "sql": """SELECT COUNT(*) as high_salary_count
FROM salaries
WHERE base_salary + bonus > 10000"""
    },
    {
        "question": "研发部工资最高的3个人是谁？",
        "sql": """SELECT e.emp_name, e.position, (s.base_salary + s.bonus) as total_salary
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
JOIN salaries s ON e.emp_id = s.emp_id
WHERE d.dept_name = '研发部'
ORDER BY total_salary DESC
LIMIT 3"""
    }
]


def get_few_shot_prompt(question: str, schema: str, num_examples: int = 3) -> str:
    """构建Few-shot提示词
    
    Args:
        question: 用户的自然语言问题
        schema: 数据库表结构描述
        num_examples: 使用的示例数量
    
    Returns:
        完整的提示词
    """
    examples_text = ""
    for example in NL2SQL_EXAMPLES[:num_examples]:
        examples_text += f"\n问题：{example['question']}\n{example['sql']}\n"
    
    prompt = f"""{SYSTEM_PROMPT.format(schema=schema)}

以下是一些示例：
{examples_text}
现在请为以下问题生成SQL（只返回SQL语句，不要任何前缀）：
问题：{question}
"""
    
    return prompt


def get_intent_prompt(question: str) -> str:
    """判断用户意图的提示词
    
    Args:
        question: 用户输入
    
    Returns:
        意图判断提示词
    """
    return f"""判断以下用户输入是否需要查询数据库。

用户输入：{question}

如果需要查询数据库，返回"需要查询"。
如果不需要（比如打招呼、感谢、或与数据无关的问题），返回"无需查询"。

只返回"需要查询"或"无需查询"，不要有其他内容。"""


def get_response_format_prompt(question: str, query_result: str) -> str:
    """格式化查询结果的提示词
    
    Args:
        question: 原始问题
        query_result: SQL查询结果
    
    Returns:
        格式化提示词
    """
    return f"""请根据查询结果回答用户的问题。

用户问题：{question}

查询结果：
{query_result}

请用自然语言简洁地回答用户的问题，不要显示原始的JSON数据。如果结果为空，请友好地告知用户。"""


def get_master_intent_prompt(question: str, conversation_history: str = "") -> str:
    """主智能体意图识别的提示词
    
    Args:
        question: 用户当前问题
        conversation_history: 会话历史摘要
    
    Returns:
        意图识别提示词
    """
    history_context = f"\n对话历史：\n{conversation_history}\n" if conversation_history else ""
    
    return f"""你是一个智能任务路由器，需要分析用户的问题并决定如何处理。{history_context}
当前问题：{question}

请判断这个问题属于以下哪一类：

1. simple_answer - 简单问候、感谢或与业务无关的问题（如：你好、谢谢、再见）
2. sql_only - 需要查询数据库但不需要深度分析（如：有多少员工、张三的工资是多少）
3. analysis_only - 只需要分析已有数据，不需要新查询（如：分析一下刚才的结果、帮我总结一下之前的数据）
4. sql_and_analysis - 需要先查询数据再进行深度分析（如：分析各部门薪资水平、找出工资异常的员工并分析原因）

只返回以下四个选项之一：simple_answer、sql_only、analysis_only、sql_and_analysis
不要返回任何解释，只返回选项本身。"""


def get_analysis_prompt(data_summary: str, raw_data: str, context: str = "") -> str:
    """数据分析的提示词
    
    Args:
        data_summary: 数据摘要
        raw_data: 原始数据JSON
        context: 上下文信息
    
    Returns:
        数据分析提示词
    """
    context_text = f"\n问题背景：{context}\n" if context else ""
    
    return f"""你是一个专业的数据分析师，请对以下数据进行深度分析。{context_text}
数据摘要：
{data_summary}

原始数据：
{raw_data}

请提供以下分析：
1. 数据概览：简要描述数据的整体情况
2. 关键发现：指出数据中最重要的3-5个发现
3. 趋势分析：如果数据中有趋势或模式，请指出
4. 异常检测：是否有异常值或不寻常的数据点
5. 洞察建议：基于数据提供的建议或行动项

请用清晰、专业但易懂的语言回答，突出重点。"""


def get_summary_prompt(question: str, sql_result: str, analysis_result: str) -> str:
    """多智能体结果汇总的提示词
    
    Args:
        question: 用户原始问题
        sql_result: SQL查询结果
        analysis_result: 分析结果
    
    Returns:
        结果汇总提示词
    """
    sql_section = f"\n查询结果：\n{sql_result}\n" if sql_result else ""
    analysis_section = f"\n分析结果：\n{analysis_result}\n" if analysis_result else ""
    
    return f"""请根据以下信息，为用户的问题提供一个完整、清晰的回答。

用户问题：{question}{sql_section}{analysis_section}

请综合以上信息，用自然、友好的语言回答用户的问题。确保回答：
1. 直接针对用户的问题
2. 包含关键数据和分析洞察
3. 结构清晰、易于理解
4. 如果有多个要点，使用列表或分段展示

不要重复显示原始JSON数据，而是用自然语言表达。"""