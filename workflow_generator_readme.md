# Dify 工作流生成器（元工作流）使用指南

## 📦 文件说明

| 文件 | 说明 |
|------|------|
| `workflow_generator.yml` | 基础版工作流生成器，线性执行 |
| `workflow_generator_agent_teams.yml` | Agent Teams 版，多代理并行执行，质量更高 |

## 🚀 快速开始

### 步骤 1: 导入到 Dify

1. 登录 Dify 控制台（https://dify.ai 或你的自建实例）
2. 进入 **工作室 (Studio)**
3. 点击右上角 **导入 DSL 文件 (Import DSL)**
4. 选择 `workflow_generator_agent_teams.yml`
5. 点击确认导入

### 步骤 2: 使用工作流生成器

1. 打开导入的工作流
2. 点击 **预览 (Preview)** 或 **发布 (Publish)**
3. 在对话框中描述你想要创建的工作流，例如：

```
创建一个智能客服工作流，需要：
1. 接收客户消息
2. 分析意图（订单查询/退款/产品咨询）
3. 根据意图路由到不同处理节点
4. 查询订单信息
5. 生成回复

工作流名称：智能客服机器人
```

### 步骤 3: 获取生成的工作流

等待几秒钟，系统会返回：
- 📋 使用文档
- ⚙️ 技术详情（验证结果、优化建议）
- 📄 完整的 YAML 代码

复制 YAML 内容，再次导入到 Dify 即可使用！

## 🏗️ 架构说明

### 基础版 (workflow_generator.yml)

```
[开始] → [意图分析] → [架构设计] → [节点实现] → [DSL验证] → [YAML清理] → [生成文档] → [输出]
```

**特点**：
- 顺序执行，逻辑清晰
- 适合简单工作流生成
- 资源消耗较低

### Agent Teams 版 (workflow_generator_agent_teams.yml)

```
                    ┌→ [需求分析代理]
                   /                    \
[开始] → 并行分析 → [架构师代理] → [聚合] → [实现代理] → 并行处理 → [验证代理]
                   \                    /               \
                    └→ [技术顾问代理]                    → [优化代理]
                                              \
                                               → [文档代理]
                                                        \
                              [YAML清理] → [最终格式化] → [输出]
```

**特点**：
- 7 个专业代理并行/协同工作
- 生成质量更高
- 包含验证和优化环节
- 适合复杂工作流生成

## 🎨 支持的节点类型

生成的工作流可以包含以下 Dify 节点：

| 节点类型 | 用途 |
|----------|------|
| `start` | 工作流入口 |
| `end` | 工作流结束 |
| `llm` | AI 处理节点 |
| `code` | Python/JavaScript 代码执行 |
| `http` | HTTP 请求 |
| `if-else` | 条件分支 |
| `question-classifier` | 问题分类 |
| `knowledge-retrieval` | 知识库检索 |
| `template` | 模板转换 |
| `variable-aggregator` | 变量聚合 |
| `iteration` | 迭代处理 |
| `list-operator` | 列表操作 |
| `parameter-extractor` | 参数提取 |

## 💡 示例需求

### 示例 1: 翻译工作流
```
创建一个翻译工作流：
- 输入：原文和目标语言
- 使用 GPT-4 进行翻译
- 输出翻译结果
名称：智能翻译器
```

### 示例 2: 数据分析工作流
```
创建一个数据分析工作流：
- 接收 CSV 数据
- 使用代码节点统计关键指标
- 生成图表描述
- 输出分析报告
复杂度：medium
```

### 示例 3: 客服机器人
```
创建一个多轮对话客服机器人：
- 理解用户意图
- 查询知识库
- 维护对话上下文
- 生成友好回复
- 复杂度高，需要条件分支
复杂度：complex
```

## 🔧 高级配置

### 修改默认模型

编辑 YAML 文件中的 `model` 部分：

```yaml
model:
  provider: anthropic  # 或 openai
  name: claude-3-opus-20240229  # 更换模型
  mode: chat
  completion_params:
    temperature: 0.3
    max_tokens: 4000
```

### 自定义代理提示词

编辑 YAML 中的 `prompt_template`，修改 `system` 角色的内容。

## 🐛 故障排查

| 问题 | 解决方案 |
|------|----------|
| 生成的 YAML 无法导入 | 检查 YAML 格式，确保以 `app:` 开头 |
| 节点连接错误 | 验证 edges 中的 source/target 是否匹配节点 ID |
| 变量引用失败 | 确保使用 `{{#node_id.variable#}}` 格式 |
| 生成内容不完整 | 增加 LLM 节点的 `max_tokens` 参数 |

## 📚 相关文档

- [Dify 官方文档](https://docs.dify.ai/)
- [Dify DSL 规范](https://docs.dify.ai/guides/workflow/import-export)
- [Claude 模型文档](https://docs.anthropic.com/claude/)

## 🔄 更新日志

- **v1.0** - 基础版工作流生成器
- **v1.1** - Agent Teams 版本，支持多代理并行

## 📄 License

MIT License - 自由使用和修改
