# Agent Teams 功能启用指南

## 前提条件

Agent Teams 是 **Claude Opus 4.6** 的 Research Preview 功能，需要：

### 1. API 访问权限

目前处于内测阶段，需要：
- [ ] Anthropic API 账号
- [ ] 申请 Agent Teams Beta 访问权限
- [ ] API Key 具有 `agent-teams` 权限范围

**申请方式：**
```
1. 访问 https://www.anthropic.com/contact
2. 选择 "API Access Request"
3. 在备注中说明需要 "Agent Teams Beta Access"
4. 等待审核（通常 3-5 个工作日）
```

### 2. 安装依赖

```bash
# 确保使用最新版 Anthropic Python SDK
pip install anthropic>=0.40.0

# 或者使用 HTTP API
pip install httpx>=0.25.0
```

## 启用步骤

### 步骤 1: 配置 API Key

```bash
# 方法 1: 环境变量
export ANTHROPIC_API_KEY="your-api-key-here"
export ANTHROPIC_AGENT_TEAMS_ENABLED="true"

# 方法 2: .env 文件
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
echo "ANTHROPIC_AGENT_TEAMS_ENABLED=true" >> .env
```

### 步骤 2: 验证访问权限

```python
import anthropic

client = anthropic.Anthropic()

# 检查 Agent Teams 是否可用
try:
    # 尝试访问 beta API
    response = client.beta.agent_teams.list()
    print("✅ Agent Teams 功能已启用!")
except anthropic.PermissionDeniedError:
    print("❌ 没有 Agent Teams 访问权限")
    print("   请先申请 Beta 访问权限")
except AttributeError:
    print("⚠️  请更新 anthropic SDK: pip install -U anthropic")
```

### 步骤 3: 使用本项目的 Agent Teams 功能

#### 方法 A: 使用 CLI

```bash
# 进入项目目录
cd dify-workflow-generator

# 启动交互式 Agent Team
python -c "
from dify_workflow.agent_teams import AgentTeamCLI
import asyncio

cli = AgentTeamCLI()
asyncio.run(cli.interactive_mode())
"
```

#### 方法 B: Python API

```python
from dify_workflow import DifyWorkflowAgentTeam
import asyncio

async def main():
    # 创建 Agent Team
    team = DifyWorkflowAgentTeam(
        api_key="your-api-key"  # 或从环境变量读取
    )

    # 创建默认团队
    team.create_default_team()

    # 开始开发工作流
    result = await team.develop_workflow(
        requirements="创建一个智能客服工作流，支持多轮对话和知识库检索",
        mode="parallel"  # 并行模式
    )

    print("设计结果:", result["design"])
    print("实现代码:", result["implementation"])
    print("验证报告:", result["validation"])

asyncio.run(main())
```

## 高级配置

### 自定义 Agent 配置

```python
from dify_workflow import AgentConfig, AgentRole

team = DifyWorkflowAgentTeam()

# 添加自定义代理
team.register_agent(AgentConfig(
    id="security_expert",
    name="安全专家",
    role=AgentRole.VALIDATOR,
    model="claude-opus-4-6",
    temperature=0.3,
    system_prompt="""你是 AI 安全专家。
    职责：
    1. 检查提示词注入漏洞
    2. 验证输入输出安全
    3. 建议安全最佳实践
    """
))
```

### 配置并行度

```python
# 控制并发代理数量
result = await team.develop_workflow(
    requirements="...",
    mode="parallel",
    max_concurrent_agents=3  # 最多同时运行3个代理
)
```

## 故障排除

### 问题 1: "Agent Teams not available"

**原因**: 你的 API Key 没有 Agent Teams 权限

**解决**:
```python
# 检查 API Key 权限
import anthropic
client = anthropic.Anthropic(api_key="your-key")

# 查看可用的 beta 功能
try:
    capabilities = client.beta.capabilities()
    print(capabilities)
except:
    print("无法访问 beta API")
```

### 问题 2: "Model claude-opus-4-6 not found"

**原因**: 模型名称错误或该模型对你不可用

**解决**:
```python
# 使用替代模型
agent = AgentConfig(
    model="claude-3-opus-20240229",  # 临时使用 Opus 3
    # ... 其他配置
)
```

### 问题 3: 请求超时

**原因**: Agent Teams 任务较复杂，执行时间长

**解决**:
```python
# 增加超时时间
result = await team.develop_workflow(
    requirements="...",
    timeout=300  # 5分钟超时
)
```

## 模拟模式（无 API 访问时）

如果你没有 Agent Teams 访问权限，可以使用模拟模式：

```python
from dify_workflow import DifyWorkflowAgentTeam

team = DifyWorkflowAgentTeam(
    api_key="dummy",  # 虚拟 key
    mock_mode=True    # 启用模拟
)

# 这会模拟 Agent Teams 的行为，使用本地 LLM 或预设响应
result = await team.develop_workflow(
    requirements="创建一个翻译工作流"
)
```

## 生产环境配置

### Docker 部署

```dockerfile
# Dockerfile.agent-teams
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 配置环境变量
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ENV ANTHROPIC_AGENT_TEAMS_ENABLED=true

# 运行 Agent Team 服务
COPY . .
CMD ["python", "-m", "dify_workflow.agent_teams_server"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  agent-teams:
    build:
      context: .
      dockerfile: Dockerfile.agent-teams
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ANTHROPIC_AGENT_TEAMS_ENABLED=true
    ports:
      - "8766:8766"
```

### 监控和日志

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

# 创建带监控的团队
team = DifyWorkflowAgentTeam(
    api_key="your-key",
    enable_metrics=True,  # 启用指标收集
    log_level="DEBUG"
)

# 查看执行指标
result = await team.develop_workflow("...")
print(team.metrics)  # 显示每个代理的执行时间、token 使用量等
```

## 示例工作流

### 示例 1: 快速启动

```bash
# 克隆仓库
git clone https://github.com/Rrocean/dify-workflow-generator.git
cd dify-workflow-generator

# 安装依赖
pip install -e ".[all]"

# 设置 API Key
export ANTHROPIC_API_KEY="sk-ant-..."

# 运行示例
python agent_teams_example.py
```

### 示例 2: 完整开发流程

```python
# develop_workflow.py
import asyncio
from dify_workflow import DifyWorkflowAgentTeam

async def develop():
    team = DifyWorkflowAgentTeam()
    team.create_default_team()

    # 定义需求
    requirements = """
    创建一个电商客服工作流，需要：
    1. 接收客户咨询
    2. 分析意图（订单查询/退款/产品咨询/投诉）
    3. 根据不同意图路由到不同处理流程
    4. 查询订单信息
    5. 生成回复
    """

    # 并行开发
    result = await team.develop_workflow(requirements, mode="parallel")

    # 导出最终工作流
    workflow = result["final_workflow"]

    # 保存到文件
    import json
    with open("customer_service_workflow.json", "w") as f:
        json.dump(workflow, f, indent=2)

    print("✅ 工作流已生成: customer_service_workflow.json")

if __name__ == "__main__":
    asyncio.run(develop())
```

运行：
```bash
python develop_workflow.py
```

## 更新日志

- **v0.5.1** - 添加 Agent Teams 支持
- 支持 5 个专业代理角色
- 支持并行和顺序执行模式
- 添加交互式 CLI

## 获取帮助

- GitHub Issues: https://github.com/Rrocean/dify-workflow-generator/issues
- Anthropic 支持: https://support.anthropic.com
- 文档: https://docs.anthropic.com/claude/agent-teams
