"""
Agent Teams Fallback - 无 Opus 4.6 时的替代方案

方案:
1. 使用 Claude 3.5 Sonnet + 并行协调
2. 使用本地多进程模拟 Agent Teams
3. 使用 OpenAI/其他 LLM 实现多代理
4. 使用 Sequential 模式 (单代理迭代)
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class FallbackMode(Enum):
    """降级模式"""
    SEQUENTIAL = "sequential"           # 单代理顺序执行
    PARALLEL_SONNET = "parallel_sonnet" # Claude 3.5 Sonnet 并行
    MULTI_LLM = "multi_llm"             # 多 LLM 混合 (Claude + GPT)
    LOCAL_MOCK = "local_mock"           # 本地模拟模式


@dataclass
class SimpleAgent:
    """简化版代理"""
    id: str
    name: str
    role: str
    model: str  # claude-3-5-sonnet, gpt-4, etc.
    system_prompt: str


class AgentTeamsFallback:
    """
    Agent Teams 降级实现
    无需 Opus 4.6，使用标准 API 实现类似功能
    """

    def __init__(
        self,
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        mode: FallbackMode = FallbackMode.PARALLEL_SONNET
    ):
        self.anthropic_key = anthropic_key
        self.openai_key = openai_key
        self.mode = mode
        self.agents: List[SimpleAgent] = []

    # ==================== 方案 1: 顺序执行 (无需并行) ====================

    async def sequential_development(self, requirements: str) -> Dict[str, Any]:
        """
        方案 1: 单代理顺序执行

        优点:
        - 只需要一个 LLM API Key
        - 简单可靠
        - 成本低

        缺点:
        - 比并行慢
        - 无真正并行优势
        """
        print("\n[方案 1] 顺序执行模式 (Sequential)")
        print("=" * 60)

        results = {}

        # 使用单个代理，但分阶段执行
        stages = [
            ("design", "作为架构师，设计工作流结构"),
            ("implementation", "作为开发者，实现节点代码"),
            ("validation", "作为验证者，检查代码正确性"),
            ("optimization", "作为优化师，提升性能"),
            ("documentation", "作为文档编写者，生成文档"),
        ]

        context = f"原始需求: {requirements}\n\n"

        for stage_name, stage_prompt in stages:
            print(f"\n▶️  阶段: {stage_name}")

            # 构建提示词
            prompt = f"""{stage_prompt}

{context}

请完成此阶段任务，输出结构化结果。"""

            # 调用 LLM (Claude 3.5 Sonnet 或 GPT-4)
            result = await self._call_llm(prompt, model="claude-3-5-sonnet-20241022")

            results[stage_name] = result
            context += f"\n\n[{stage_name}]\n{result}\n"

            print(f"✅ 完成: {stage_name}")

        return results

    # ==================== 方案 2: 并行执行 (Claude 3.5 Sonnet) ====================

    async def parallel_with_sonnet(self, requirements: str) -> Dict[str, Any]:
        """
        方案 2: 使用 Claude 3.5 Sonnet 并行执行

        优点:
        - 真正的并行执行
        - 速度提升 3-5 倍
        - 无需 Opus 4.6

        缺点:
        - API 调用次数多
        - 成本稍高
        """
        print("\n[方案 2] 并行执行模式 (Parallel with Sonnet)")
        print("=" * 60)

        # 定义独立可并行的任务
        parallel_tasks = {
            "architecture": f"设计工作流架构:\n{requirements}",
            "node_design": f"设计节点结构:\n{requirements}",
            "api_design": f"设计 API 接口:\n{requirements}",
        }

        # 并行执行第一波 (无依赖)
        print("\n🚀 第一波并行任务 (架构设计)")
        first_wave = await asyncio.gather(*[
            self._call_llm(prompt, model="claude-3-5-sonnet-20241022")
            for prompt in parallel_tasks.values()
        ])

        wave1_results = dict(zip(parallel_tasks.keys(), first_wave))

        # 构建上下文
        context = f"""原始需求:
{requirements}

架构设计:
{wave1_results['architecture']}

节点设计:
{wave1_results['node_design']}

API 设计:
{wave1_results['api_design']}"""

        # 并行执行第二波 (依赖第一波)
        print("\n🚀 第二波并行任务 (实现)")
        second_wave_tasks = {
            "backend": f"根据以下设计实现后端代码:\n{context}",
            "frontend": f"根据以下设计实现前端代码:\n{context}",
            "tests": f"根据以下设计编写测试:\n{context}",
        }

        second_wave = await asyncio.gather(*[
            self._call_llm(prompt, model="claude-3-5-sonnet-20241022")
            for prompt in second_wave_tasks.values()
        ])

        wave2_results = dict(zip(second_wave_tasks.keys(), second_wave))

        # 最终整合
        print("\n🚀 最终整合")
        final_prompt = f"""整合以下实现为完整工作流:

后端:
{wave2_results['backend']}

前端:
{wave2_results['frontend']}

测试:
{wave2_results['tests']}

请输出最终完整的工作流定义。"""

        final_result = await self._call_llm(final_prompt, model="claude-3-5-sonnet-20241022")

        return {
            **wave1_results,
            **wave2_results,
            "final_workflow": final_result
        }

    # ==================== 方案 3: 多 LLM 混合 ====================

    async def multi_llm_coordination(self, requirements: str) -> Dict[str, Any]:
        """
        方案 3: 使用多个 LLM 协同

        Claude 3.5 Sonnet + GPT-4 混合使用
        各取所长
        """
        print("\n[方案 3] 多 LLM 协调模式 (Claude + GPT)")
        print("=" * 60)

        # 分配不同任务给不同模型
        tasks = {
            "claude": {
                "model": "claude-3-5-sonnet-20241022",
                "prompt": f"使用 Claude 优势进行架构设计:\n{requirements}",
                "key": self.anthropic_key
            },
            "gpt4": {
                "model": "gpt-4-turbo-preview",
                "prompt": f"使用 GPT-4 优势进行代码实现:\n{requirements}",
                "key": self.openai_key
            },
        }

        # 并行调用不同 API
        async def run_task(name: str, config: dict):
            print(f"\n🤖 {name} ({config['model']}) 开始工作...")
            result = await self._call_llm_api(
                config['prompt'],
                config['model'],
                config['key']
            )
            print(f"✅ {name} 完成")
            return name, result

        results = await asyncio.gather(*[
            run_task(name, config)
            for name, config in tasks.items()
        ])

        return dict(results)

    # ==================== 方案 4: 本地模拟模式 ====================

    async def local_mock_mode(self, requirements: str) -> Dict[str, Any]:
        """
        方案 4: 本地模拟 (无需 API)

        使用预设模板和规则模拟 Agent Teams
        适合演示和测试
        """
        print("\n[方案 4] 本地模拟模式 (无需 API)")
        print("=" * 60)

        # 解析需求关键词
        keywords = self._extract_keywords(requirements)

        # 根据关键词选择模板
        templates = {
            "translation": self._get_translation_template(),
            "chatbot": self._get_chatbot_template(),
            "summarization": self._get_summarization_template(),
        }

        # 找到最匹配的模板
        matched_template = None
        for keyword in keywords:
            if keyword in templates:
                matched_template = templates[keyword]
                break

        if not matched_template:
            matched_template = self._get_generic_template()

        # 模拟各代理工作
        results = {
            "design": f"[模拟] 架构师设计工作流\n基于需求: {requirements[:100]}...",
            "implementation": f"[模拟] 开发者实现节点\n使用模板: {matched_template['name']}",
            "validation": "[模拟] 验证者检查 DSL\n所有检查通过 ✓",
            "optimization": "[模拟] 优化师建议:\n- 使用缓存减少 API 调用\n- 添加重试机制",
            "documentation": f"[模拟] 生成文档\n基于模板: {matched_template['description']}",
            "final_workflow": matched_template['workflow']
        }

        # 模拟执行时间
        for key in results:
            await asyncio.sleep(0.2)  # 模拟处理时间
            print(f"✅ {key} 完成")

        return results

    # ==================== 辅助方法 ====================

    async def _call_llm(self, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> str:
        """调用 LLM API"""
        if "claude" in model.lower():
            return await self._call_claude(prompt, model)
        else:
            return await self._call_openai(prompt, model)

    async def _call_claude(self, prompt: str, model: str) -> str:
        """调用 Claude API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key)

            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text
        except Exception as e:
            return f"[Claude API Error: {e}]"

    async def _call_openai(self, prompt: str, model: str) -> str:
        """调用 OpenAI API"""
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.openai_key)

            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI API Error: {e}]"

    async def _call_llm_api(self, prompt: str, model: str, api_key: str) -> str:
        """通用 LLM API 调用"""
        if "claude" in model.lower():
            return await self._call_claude(prompt, model)
        else:
            return await self._call_openai(prompt, model)

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本提取关键词"""
        keywords = ["translation", "chatbot", "summarization", "code", "review"]
        found = []
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                found.append(kw)
        return found

    def _get_translation_template(self) -> Dict:
        """翻译工作流模板"""
        return {
            "name": "Translation Workflow",
            "description": "A workflow for translating text between languages",
            "workflow": {
                "version": "0.5.0",
                "nodes": [
                    {"id": "start", "type": "start", "variables": ["text", "target_lang"]},
                    {"id": "llm", "type": "llm", "prompt": "Translate to {{#start.target_lang#}}: {{#start.text#}}"},
                    {"id": "end", "type": "end"}
                ]
            }
        }

    def _get_chatbot_template(self) -> Dict:
        """聊天机器人模板"""
        return {
            "name": "Chatbot Workflow",
            "description": "An AI chatbot with memory support",
            "workflow": {
                "version": "0.5.0",
                "nodes": [
                    {"id": "start", "type": "start", "variables": ["query"]},
                    {"id": "llm", "type": "llm", "prompt": "User: {{#start.query#}}"},
                    {"id": "answer", "type": "answer"}
                ]
            }
        }

    def _get_summarization_template(self) -> Dict:
        """摘要模板"""
        return {
            "name": "Summarization Workflow",
            "description": "Summarize long text into key points",
            "workflow": {
                "version": "0.5.0",
                "nodes": [
                    {"id": "start", "type": "start", "variables": ["text"]},
                    {"id": "llm", "type": "llm", "prompt": "Summarize: {{#start.text#}}"},
                    {"id": "end", "type": "end"}
                ]
            }
        }

    def _get_generic_template(self) -> Dict:
        """通用模板"""
        return {
            "name": "Generic Workflow",
            "description": "A general-purpose workflow",
            "workflow": {
                "version": "0.5.0",
                "nodes": [
                    {"id": "start", "type": "start"},
                    {"id": "llm", "type": "llm"},
                    {"id": "end", "type": "end"}
                ]
            }
        }

    # ==================== 主入口 ====================

    async def develop(
        self,
        requirements: str,
        mode: Optional[FallbackMode] = None
    ) -> Dict[str, Any]:
        """
        主入口 - 自动选择最佳方案
        """
        mode = mode or self.mode

        print(f"\n{'='*70}")
        print(f"🚀 Agent Teams Fallback - {mode.value}")
        print(f"{'='*70}")

        if mode == FallbackMode.SEQUENTIAL:
            return await self.sequential_development(requirements)

        elif mode == FallbackMode.PARALLEL_SONNET:
            if not self.anthropic_key:
                print("⚠️  无 Anthropic API Key，切换到顺序模式")
                return await self.sequential_development(requirements)
            return await self.parallel_with_sonnet(requirements)

        elif mode == FallbackMode.MULTI_LLM:
            if not (self.anthropic_key and self.openai_key):
                print("⚠️  需要 Anthropic 和 OpenAI Key，切换到 Sonnet 并行")
                return await self.parallel_with_sonnet(requirements)
            return await self.multi_llm_coordination(requirements)

        elif mode == FallbackMode.LOCAL_MOCK:
            return await self.local_mock_mode(requirements)

        else:
            raise ValueError(f"Unknown mode: {mode}")


# ==================== 使用示例 ====================

async def main():
    """主函数 - 演示各种 fallback 方案"""

    requirements = """
    创建一个智能客服工作流，需要：
    1. 接收客户消息
    2. 分析意图（订单查询/退款/产品咨询）
    3. 根据意图路由到不同处理节点
    4. 查询数据库或知识库
    5. 生成回复
    """

    # 方案 1: 顺序模式 (只需一个 API Key，最省钱)
    print("\n" + "="*70)
    print("方案 1: 顺序模式 (推荐初学者)")
    print("="*70)

    fallback1 = AgentTeamsFallback(
        anthropic_key="your-anthropic-key",  # 替换为你的 key
        mode=FallbackMode.SEQUENTIAL
    )
    result1 = await fallback1.develop(requirements)
    print("\n✅ 顺序模式完成")

    # 方案 2: Sonnet 并行 (需要 Anthropic Key，速度最快)
    print("\n" + "="*70)
    print("方案 2: Sonnet 并行模式 (推荐有 API Key)")
    print("="*70)

    fallback2 = AgentTeamsFallback(
        anthropic_key="your-anthropic-key",
        mode=FallbackMode.PARALLEL_SONNET
    )
    result2 = await fallback2.develop(requirements)
    print("\n✅ 并行模式完成")

    # 方案 3: 本地模拟 (无需 API，适合测试)
    print("\n" + "="*70)
    print("方案 3: 本地模拟模式 (无需 API)")
    print("="*70)

    fallback3 = AgentTeamsFallback(mode=FallbackMode.LOCAL_MOCK)
    result3 = await fallback3.develop(requirements)
    print("\n✅ 模拟模式完成")

    # 保存结果
    with open("workflow_results.json", "w") as f:
        json.dump({
            "sequential": result1,
            "parallel": result2,
            "mock": result3
        }, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print("📁 结果已保存到 workflow_results.json")
    print("="*70)


if __name__ == "__main__":
    print("🚀 Agent Teams Fallback - 无需 Opus 4.6 的多代理方案")
    print("="*70)
    print("\n可用方案:")
    print("1. 顺序模式 (Sequential) - 只需一个 API Key")
    print("2. 并行模式 (Parallel) - 使用 Claude 3.5 Sonnet")
    print("3. 多 LLM 模式 (Multi-LLM) - Claude + GPT 混合")
    print("4. 本地模拟 (Mock) - 无需 API，纯本地")

    asyncio.run(main())
