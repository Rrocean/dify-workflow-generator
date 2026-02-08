#!/usr/bin/env python3
"""
CLI 工作流生成器 - 使用 Agent Teams 方式生成 Dify 工作流

用法:
    python cli_workflow_generator.py
    python cli_workflow_generator.py --requirement "创建一个翻译工作流"
    python cli_workflow_generator.py --file workflow_generator.yml
"""

import asyncio
import argparse
import json
import os
import sys
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

# 导入 dify_workflow 框架
from dify_workflow import Workflow, WorkflowBuilder, AgentTeamsFallback, FallbackMode
from dify_workflow.nodes import (
    StartNode, EndNode, LLMNode, CodeNode, TemplateNode,
    VariableAggregatorNode
)


@dataclass
class AgentTask:
    """代理任务"""
    agent_id: str
    agent_name: str
    role: str
    prompt: str
    dependencies: List[str] = None


class CLIWorkflowGenerator:
    """CLI 工作流生成器 - 使用 Agent Teams 架构"""

    def __init__(self, api_key: str = None, mode: str = "parallel"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.mode = mode
        self.agent_teams = None
        if self.api_key:
            self.agent_teams = AgentTeamsFallback(
                anthropic_key=self.api_key,
                mode=FallbackMode.PARALLEL_SONNET if mode == "parallel" else FallbackMode.SEQUENTIAL
            )

    async def generate(self, requirement: str, workflow_name: str = None, complexity: str = "auto") -> Dict[str, Any]:
        """
        使用 Agent Teams 生成工作流

        Args:
            requirement: 工作流需求描述
            workflow_name: 工作流名称
            complexity: 复杂度 (simple/medium/complex/auto)

        Returns:
            包含工作流 YAML 和文档的字典
        """
        print("\n" + "="*70)
        print("🚀 Dify 工作流生成器 (Agent Teams 模式)")
        print("="*70)
        print(f"需求: {requirement[:80]}...")
        print(f"模式: {self.mode}")
        print("="*70 + "\n")

        # 阶段 1: 并行需求分析
        print("📊 阶段 1: 需求分析（多代理并行）")
        analysis = await self._phase1_analysis(requirement, complexity)

        # 阶段 2: 架构设计与技术选型
        print("\n🏗️ 阶段 2: 架构设计")
        design = await self._phase2_design(analysis)

        # 阶段 3: 并行实现与验证
        print("\n🔨 阶段 3: 实现与验证（多代理并行）")
        implementation = await self._phase3_implementation(analysis, design)

        # 阶段 4: 优化与文档
        print("\n✨ 阶段 4: 优化与文档")
        final = await self._phase4_optimize_and_doc(implementation)

        # 阶段 5: 组装最终工作流
        print("\n📦 阶段 5: 组装工作流")
        workflow_yaml = self._assemble_workflow(
            workflow_name or f"Generated_Workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            analysis,
            design,
            final
        )

        return {
            "workflow_yaml": workflow_yaml,
            "analysis": analysis,
            "design": design,
            "documentation": final.get("documentation", ""),
            "optimization": final.get("optimization", ""),
            "validation": final.get("validation", {})
        }

    async def _phase1_analysis(self, requirement: str, complexity: str) -> Dict[str, Any]:
        """阶段 1: 多代理并行需求分析"""

        tasks = {
            "requirement": f"""作为需求分析师，分析以下工作流需求：

{requirement}

提取关键信息并以 JSON 格式返回：
{{
    "core_functions": ["核心功能列表"],
    "inputs": [{{"name": "", "type": "", "description": ""}}],
    "outputs": [{{"name": "", "type": "", "description": ""}}],
    "business_rules": ["业务规则"],
    "complexity": "simple|medium|complex",
    "special_requirements": ["特殊需求"]
}}""",
            "user_experience": f"""作为用户体验设计师，分析以下工作流的用户交互需求：

{requirement}

分析内容：
1. 用户输入方式
2. 反馈形式
3. 错误处理
4. 用户体验优化点

返回简洁的分析结果。""",
            "technical": f"""作为技术顾问，分析以下工作流的技术需求：

{requirement}

分析内容：
1. 需要的 AI 模型
2. 外部工具/API
3. 数据处理需求
4. 性能考虑

返回技术方案建议。"""
        }

        # 并行执行分析
        results = {}
        if self.agent_teams:
            # 使用 Agent Teams 并行执行
            analysis_tasks = [
                self._call_llm_async(name, prompt)
                for name, prompt in tasks.items()
            ]
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            for name, result in zip(tasks.keys(), analysis_results):
                if isinstance(result, Exception):
                    print(f"  ⚠️ {name} 分析失败: {result}")
                    results[name] = {"error": str(result)}
                else:
                    print(f"  ✅ {name} 分析完成")
                    results[name] = result
        else:
            # 顺序执行
            for name, prompt in tasks.items():
                print(f"  🔄 {name} 分析中...")
                results[name] = await self._call_llm_simple(prompt)
                print(f"  ✅ {name} 分析完成")

        return results

    async def _phase2_design(self, analysis: Dict) -> Dict[str, Any]:
        """阶段 2: 架构设计"""

        design_prompt = f"""作为 Dify 工作流架构师，基于以下分析结果设计工作流架构：

需求分析：{json.dumps(analysis.get('requirement', {}), ensure_ascii=False)}
用户体验：{analysis.get('user_experience', '')}
技术需求：{analysis.get('technical', '')}

设计内容：
1. 架构模式（顺序/并行/条件/迭代）
2. 节点清单（类型、ID、功能、依赖关系）
3. 数据流描述
4. 错误处理策略

以 JSON 格式返回设计：
{{
    "architecture_pattern": "sequential|parallel|conditional|iterative",
    "nodes": [
        {{"id": "", "type": "", "purpose": "", "dependencies": []}}
    ],
    "data_flow": "描述",
    "error_handling": "策略"
}}"""

        design_text = await self._call_llm_simple(design_prompt)
        print(f"  ✅ 架构设计完成")

        try:
            # 尝试解析 JSON
            design_json = json.loads(design_text)
            return {"design": design_json, "raw": design_text}
        except json.JSONDecodeError:
            return {"design": {}, "raw": design_text}

    async def _phase3_implementation(self, analysis: Dict, design: Dict) -> Dict[str, Any]:
        """阶段 3: 并行实现与验证"""

        # 实现任务
        impl_prompt = f"""作为 Dify DSL 专家，根据以下设计生成完整的 DSL YAML：

需求分析：{json.dumps(analysis, ensure_ascii=False)}
架构设计：{json.dumps(design, ensure_ascii=False)}

严格遵循 Dify DSL 0.5.0 格式：
1. 使用有效的节点类型
2. 设置正确的 position (x, y)
3. 变量引用格式 {{#node_id.variable#}}
4. 包含所有必需的字段

直接输出 YAML 内容（从 app: 开始），不要添加 markdown 代码块。"""

        # 验证任务
        validate_prompt = f"""作为 DSL 验证专家，等待实现完成后进行验证。

验证要点：
1. YAML 语法正确
2. 节点 ID 唯一
3. 变量引用有效
4. 节点连接合理

返回验证报告 JSON：
{{"valid": true/false, "issues": [], "suggestions": []}}"""

        # 优化任务
        optimize_prompt = f"""作为性能优化专家，分析以下需求并提前准备优化建议：

需求：{json.dumps(analysis, ensure_ascii=False)}

优化方向：
1. 减少不必要的节点
2. 合并相似操作
3. 建议模型选择
4. 并行化机会

返回优化建议。"""

        print("  🔄 并行执行：实现、验证、优化...")

        if self.mode == "parallel":
            # 并行执行
            impl_task = self._call_llm_simple(impl_prompt)
            optimize_task = self._call_llm_simple(optimize_prompt)

            impl_result, optimize_result = await asyncio.gather(impl_task, optimize_task)

            # 验证依赖实现结果
            validate_prompt_with_impl = validate_prompt + f"\n\n实现内容：\n{impl_result}"
            validate_result = await self._call_llm_simple(validate_prompt_with_impl)
        else:
            # 顺序执行
            impl_result = await self._call_llm_simple(impl_prompt)
            validate_prompt_with_impl = validate_prompt + f"\n\n实现内容：\n{impl_result}"
            validate_result = await self._call_llm_simple(validate_prompt_with_impl)
            optimize_result = await self._call_llm_simple(optimize_prompt)

        print(f"  ✅ 实现完成")
        print(f"  ✅ 验证完成")
        print(f"  ✅ 优化建议完成")

        return {
            "implementation": impl_result,
            "validation": validate_result,
            "optimization": optimize_result
        }

    async def _phase4_optimize_and_doc(self, implementation: Dict) -> Dict[str, Any]:
        """阶段 4: 优化与文档"""

        doc_prompt = f"""作为技术文档专家，为以下工作流编写使用文档：

实现代码：
{implementation.get('implementation', '')[:2000]}...

文档内容：
1. 功能概述
2. 输入参数说明
3. 使用步骤
4. 示例场景
5. 注意事项

使用 Markdown 格式，简洁明了。"""

        final_optimize_prompt = f"""作为性能优化专家，基于验证结果给出最终优化建议：

实现：{implementation.get('implementation', '')[:1000]}...
验证：{implementation.get('validation', '')}
初始优化：{implementation.get('optimization', '')}

返回最终的、可执行的优化建议。"""

        doc_task = self._call_llm_simple(doc_prompt)
        optimize_task = self._call_llm_simple(final_optimize_prompt)

        doc_result, optimize_result = await asyncio.gather(doc_task, optimize_task)

        print(f"  ✅ 文档生成完成")
        print(f"  ✅ 最终优化完成")

        return {
            "documentation": doc_result,
            "optimization": optimize_result,
            "validation": implementation.get("validation", {})
        }

    def _assemble_workflow(self, name: str, analysis: Dict, design: Dict, final: Dict) -> str:
        """组装最终的工作流 YAML"""
        impl = final.get("implementation", "")

        # 清理 YAML
        import re

        # 移除 markdown 代码块
        impl = re.sub(r'^```yaml\s*', '', impl)
        impl = re.sub(r'^```yml\s*', '', impl)
        impl = re.sub(r'^```\s*', '', impl)
        impl = re.sub(r'\n```\s*$', '', impl)
        impl = impl.strip()

        # 确保以 app: 开头
        if not impl.startswith('app:'):
            idx = impl.find('app:')
            if idx != -1:
                impl = impl[idx:]

        return impl

    async def _call_llm_async(self, task_name: str, prompt: str) -> str:
        """异步调用 LLM"""
        if self.agent_teams:
            # 使用 Agent Teams Fallback
            return await self.agent_teams._call_claude(prompt, "claude-3-5-sonnet-20241022")
        else:
            return await self._call_llm_simple(prompt)

    async def _call_llm_simple(self, prompt: str) -> str:
        """简单 LLM 调用（模拟）"""
        # 这里可以接入实际的 LLM API
        # 目前返回模拟结果用于演示

        if not self.api_key:
            # 模拟模式
            await asyncio.sleep(0.5)
            return f"[模拟响应] 基于提示词分析：{prompt[:100]}..."

        # 实际调用 Claude API
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text
        except Exception as e:
            print(f"  ⚠️ API 调用失败: {e}")
            return f"[Error: {e}]"


def interactive_mode():
    """交互式模式"""
    print("\n" + "="*70)
    print("🤖 Dify 工作流生成器 - 交互模式")
    print("="*70)
    print("\n请输入你的工作流需求（描述想要创建的工作流）：")
    print("示例：创建一个翻译工作流，输入文本和目标语言")
    print("输入 'quit' 退出\n")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    generator = CLIWorkflowGenerator(api_key=api_key)

    while True:
        print("\n" + "-"*70)
        requirement = input("\n需求描述: ").strip()

        if requirement.lower() in ['quit', 'exit', 'q']:
            print("\n再见！")
            break

        if not requirement:
            print("请输入有效的需求描述")
            continue

        workflow_name = input("工作流名称（可选，直接回车跳过）: ").strip()
        complexity = input("复杂度 (simple/medium/complex/auto) [auto]: ").strip() or "auto"
        mode = input("模式 (parallel/sequential) [parallel]: ").strip() or "parallel"

        generator.mode = mode

        try:
            result = asyncio.run(generator.generate(
                requirement=requirement,
                workflow_name=workflow_name,
                complexity=complexity
            ))

            # 保存结果
            output_file = f"generated_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result['workflow_yaml'])

            print("\n" + "="*70)
            print(f"✅ 工作流已生成并保存到: {output_file}")
            print("="*70)

            # 显示预览
            print("\n工作流预览（前 2000 字符）:")
            print("-"*70)
            print(result['workflow_yaml'][:2000])
            if len(result['workflow_yaml']) > 2000:
                print(f"\n... (共 {len(result['workflow_yaml'])} 字符)")

        except Exception as e:
            print(f"\n❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Dify 工作流生成器 - 使用 Agent Teams 架构'
    )
    parser.add_argument(
        '--requirement', '-r',
        help='工作流需求描述'
    )
    parser.add_argument(
        '--name', '-n',
        help='工作流名称'
    )
    parser.add_argument(
        '--complexity', '-c',
        choices=['simple', 'medium', 'complex', 'auto'],
        default='auto',
        help='工作流复杂度'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['parallel', 'sequential'],
        default='parallel',
        help='执行模式'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出文件路径'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='进入交互式模式'
    )

    args = parser.parse_args()

    if args.interactive or (not args.requirement):
        interactive_mode()
        return

    # 命令行模式
    api_key = os.getenv("ANTHROPIC_API_KEY")
    generator = CLIWorkflowGenerator(api_key=api_key, mode=args.mode)

    try:
        result = asyncio.run(generator.generate(
            requirement=args.requirement,
            workflow_name=args.name,
            complexity=args.complexity
        ))

        # 输出结果
        output_file = args.output or f"generated_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['workflow_yaml'])

        print(f"\n✅ 工作流已生成: {output_file}")

        # 同时输出分析结果
        analysis_file = output_file.replace('.yml', '_analysis.json')
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump({
                'analysis': result['analysis'],
                'design': result['design'],
                'documentation': result['documentation'],
                'optimization': result['optimization']
            }, f, ensure_ascii=False, indent=2)

        print(f"📊 分析结果: {analysis_file}")

    except Exception as e:
        print(f"\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
