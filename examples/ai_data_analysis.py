from dify_workflow import Workflow, StartNode, LLMNode, CodeNode, EndNode

def create_ai_data_analysis():
    # 1. 创建工作流
    wf = Workflow(
        name="AI 智能问数",
        description="将自然语言转换为 SQL 查询并分析数据结果",
        icon="📊",
        mode="workflow"
    )

    # 2. 开始节点
    start = StartNode(variables=[
        {"name": "query", "type": "string", "label": "数据问题", "required": True},
        {"name": "table_schema", "type": "string", "label": "表结构", "default": "CREATE TABLE sales (date DATE, amount DECIMAL, region VARCHAR)"}
    ])
    start.id = "start"

    # 3. LLM: 生成 SQL
    sql_gen = LLMNode(
        title="生成SQL",
        model={"provider": "openai", "name": "gpt-4", "mode": "chat"},
        prompt="""你是一个数据分析师。根据以下表结构，将用户问题转换为 SQL 查询语句。

表结构：
{{#start.table_schema#}}

用户问题：
{{#start.query#}}

请只输出 SQL 语句，不要包含其他解释。"""
    )

    # 4. 代码节点: 模拟执行 SQL (实际场景这里会调数据库 API)
    execute_sql = CodeNode(
        title="执行查询",
        language="python3",
        code="""def main(args):
    sql = args.get("sql")
    # 这里模拟数据库返回结果
    # 实际项目中，这里会连接数据库执行 SQL
    print(f"Executing: {sql}")
    
    mock_data = [
        {"date": "2024-01-01", "amount": 1000, "region": "North"},
        {"date": "2024-01-02", "amount": 1500, "region": "South"}
    ]
    
    return {
        "result": mock_data,
        "status": "success"
    }
""",
        variables=[{"variable": "sql", "value_selector": ["生成SQL", "text"]}],
        outputs=[{"variable": "result", "type": "array-object"}]
    )

    # 5. LLM: 分析结果
    analyze = LLMNode(
        title="分析结果",
        prompt="""根据执行的 SQL 和数据结果，回答用户的问题。

问题：{{#start.query#}}
SQL：{{#生成SQL.text#}}
数据结果：
{{#执行查询.result#}}

请用通俗易懂的语言总结数据洞察。"""
    )

    # 6. 结束节点
    end = EndNode(outputs=[
        {"variable": "answer", "value_selector": ["分析结果", "text"]},
        {"variable": "sql", "value_selector": ["生成SQL", "text"]}
    ])

    # 7. 构建连接
    wf.add_nodes([start, sql_gen, execute_sql, analyze, end])
    wf.connect(start, sql_gen)
    wf.connect(sql_gen, execute_sql)
    wf.connect(execute_sql, analyze)
    wf.connect(analyze, end)

    return wf

if __name__ == "__main__":
    wf = create_ai_data_analysis()
    # 导出 YAML
    wf.export("ai_data_analysis.yml")
