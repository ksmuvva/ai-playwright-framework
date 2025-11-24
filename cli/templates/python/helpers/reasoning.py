"""
Advanced Reasoning Strategies for AI-Powered Test Generation

This module implements:
1. Chain of Thought (CoT) - Step-by-step reasoning
2. Tree of Thought (ToT) - Multi-path exploration and evaluation

These strategies enhance AI capabilities for complex test scenarios.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from opentelemetry import trace
from opentelemetry.trace import StatusCode

try:
    from .phoenix_tracer import PhoenixTracer, get_tracer, create_llm_span_attributes, add_llm_response_attributes
except ImportError:
    # Tracing is optional
    PhoenixTracer = None
    get_tracer = None

try:
    from .logger import get_logger, log_ai_request, log_ai_response, log_error
    logger = get_logger("reasoning")
except ImportError:
    # Fallback if logger not available
    import logging
    logger = logging.getLogger("reasoning")
    logger.setLevel(logging.INFO)


@dataclass
class ReasoningStep:
    """Represents a single step in chain of thought reasoning"""
    step: int
    thought: str
    action: Optional[str] = None
    result: Any = None
    confidence: float = 0.0


@dataclass
class ChainOfThoughtResult:
    """Result of chain of thought reasoning"""
    steps: List[ReasoningStep]
    final_answer: Any
    reasoning: str


@dataclass
class ThoughtNode:
    """Node in tree of thought reasoning"""
    id: str
    thought: str
    state: Dict[str, Any]
    children: List['ThoughtNode']
    evaluation: float
    depth: int
    is_leaf: bool = False


@dataclass
class TreeOfThoughtResult:
    """Result of tree of thought reasoning"""
    best_path: List[ThoughtNode]
    all_paths: List[List[ThoughtNode]]
    final_answer: Any
    reasoning: str


class ChainOfThought:
    """
    Chain of Thought (CoT) Reasoning
    Breaks down complex problems into sequential reasoning steps
    """

    def __init__(self, ai_client, model: str = None):
        """
        Initialize Chain of Thought reasoner

        Args:
            ai_client: AI client instance (Anthropic or OpenAI)
            model: Model to use (optional)
        """
        self.ai_client = ai_client
        self.model = model or os.getenv('AI_MODEL', 'claude-sonnet-4-5-20250929')

        logger.info(
            "cot_initialized",
            model=self.model,
            message="Chain of Thought reasoner initialized"
        )

        # Initialize Phoenix tracing if available
        if PhoenixTracer and not PhoenixTracer.is_initialized():
            try:
                logger.debug("cot_phoenix_init", message="Initializing Phoenix tracing from CoT...")
                PhoenixTracer.initialize()
            except Exception as e:
                logger.warning(
                    "cot_phoenix_init_failed",
                    error=str(e),
                    message="Failed to initialize Phoenix tracing from CoT"
                )

        self.tracer = get_tracer() if get_tracer else None

    def reason(
        self,
        prompt: str,
        context: str,
        max_steps: int = 5
    ) -> ChainOfThoughtResult:
        """
        Execute Chain of Thought reasoning

        Args:
            prompt: The problem or task to reason about
            context: Additional context for reasoning
            max_steps: Maximum number of reasoning steps

        Returns:
            ChainOfThoughtResult with steps and final answer
        """
        logger.info(
            "cot_reasoning_started",
            max_steps=max_steps,
            prompt_length=len(prompt),
            message="🧠 Starting Chain of Thought reasoning..."
        )

        cot_prompt = self._build_cot_prompt(prompt, context, max_steps)

        try:
            start_time = time.time()

            # Call AI with the prompt
            response = self._call_ai(cot_prompt)
            result = self._parse_cot_response(response)

            duration = (time.time() - start_time) * 1000

            logger.info(
                "cot_reasoning_complete",
                steps_generated=len(result.steps),
                duration_ms=duration,
                message=f"✅ Chain of Thought reasoning completed with {len(result.steps)} steps"
            )

            return result

        except Exception as e:
            logger.error(
                "cot_reasoning_failed",
                error_type=type(e).__name__,
                error_message=str(e),
                message="❌ Chain of Thought reasoning failed",
                exc_info=True
            )
            raise

    def _build_cot_prompt(self, prompt: str, context: str, max_steps: int) -> str:
        """Build the Chain of Thought prompt"""
        return f"""You are an expert at systematic problem-solving using Chain of Thought reasoning.

Task: {prompt}

Context: {context}

Instructions:
1. Break down the problem into {max_steps} clear reasoning steps
2. For each step, explain your thought process
3. Build on previous steps to reach the final answer
4. Use logical, step-by-step thinking

Provide your response in the following JSON format:
{{
  "steps": [
    {{
      "step": 1,
      "thought": "Initial analysis and understanding of the problem...",
      "action": "What action to take based on this thought",
      "confidence": 0.9
    }}
  ],
  "finalAnswer": "The complete solution or answer",
  "reasoning": "Summary of the reasoning process"
}}

Begin your step-by-step analysis:"""

    def _call_ai(self, prompt: str) -> str:
        """Call AI client with the prompt"""
        ai_provider = os.getenv('AI_PROVIDER', 'anthropic')
        start_time = time.time()

        logger.debug(
            "cot_ai_request",
            provider=ai_provider,
            model=self.model,
            prompt_length=len(prompt),
            message=f"Calling {ai_provider} API for Chain of Thought..."
        )

        # Create span for tracing
        span_context = self.tracer.start_as_current_span(
            f'{ai_provider}.chainOfThought',
            attributes=create_llm_span_attributes(ai_provider, self.model, prompt, 4000) if create_llm_span_attributes else {}
        ) if self.tracer else None

        try:
            if ai_provider == 'anthropic':
                from anthropic import Anthropic
                client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

                response = client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = response.content[0].text
                duration = (time.time() - start_time) * 1000

                # Log token usage
                if hasattr(response, 'usage'):
                    logger.info(
                        "cot_ai_response",
                        provider=ai_provider,
                        model=self.model,
                        input_tokens=response.usage.input_tokens,
                        output_tokens=response.usage.output_tokens,
                        total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                        duration_ms=duration,
                        response_length=len(response_text),
                        message=f"✅ AI response received ({response.usage.input_tokens + response.usage.output_tokens} tokens, {duration:.0f}ms)"
                    )

                # Add tracing attributes
                if span_context and add_llm_response_attributes:
                    span = trace.get_current_span()
                    add_llm_response_attributes(
                        span,
                        response_text,
                        response.usage.input_tokens if hasattr(response, 'usage') else None,
                        response.usage.output_tokens if hasattr(response, 'usage') else None
                    )
                    span.set_attribute('llm.latency_ms', duration)
                    span.set_status(StatusCode.OK)

                return response_text

            elif ai_provider == 'openai':
                from openai import OpenAI
                client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = response.choices[0].message.content
                duration = (time.time() - start_time) * 1000

                # Log token usage
                if hasattr(response, 'usage'):
                    logger.info(
                        "cot_ai_response",
                        provider=ai_provider,
                        model=self.model,
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens,
                        duration_ms=duration,
                        response_length=len(response_text),
                        message=f"✅ AI response received ({response.usage.total_tokens} tokens, {duration:.0f}ms)"
                    )

                # Add tracing attributes
                if span_context and add_llm_response_attributes:
                    span = trace.get_current_span()
                    add_llm_response_attributes(
                        span,
                        response_text,
                        response.usage.prompt_tokens if hasattr(response, 'usage') else None,
                        response.usage.completion_tokens if hasattr(response, 'usage') else None
                    )
                    span.set_attribute('llm.latency_ms', duration)
                    span.set_status(StatusCode.OK)

                return response_text

            else:
                raise ValueError(f"Unsupported AI provider: {ai_provider}")

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                "cot_ai_request_failed",
                provider=ai_provider,
                model=self.model,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration,
                message=f"❌ AI request failed after {duration:.0f}ms",
                exc_info=True
            )

            # Record error in span
            if span_context:
                span = trace.get_current_span()
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
            raise
        finally:
            if span_context:
                span_context.__exit__(None, None, None)

    def _parse_cot_response(self, response_text: str) -> ChainOfThoughtResult:
        """Parse AI response into ChainOfThoughtResult"""
        try:
            # Remove markdown code blocks if present
            json_text = response_text.strip()
            if json_text.startswith('```'):
                json_text = json_text.split('```')[1]
                if json_text.startswith('json'):
                    json_text = json_text[4:]
                json_text = json_text.strip()

            parsed = json.loads(json_text)

            # Convert dict steps to ReasoningStep objects
            steps = []
            for step_data in parsed.get('steps', []):
                steps.append(ReasoningStep(
                    step=step_data.get('step', 0),
                    thought=step_data.get('thought', ''),
                    action=step_data.get('action'),
                    confidence=step_data.get('confidence', 0.0)
                ))

            return ChainOfThoughtResult(
                steps=steps,
                final_answer=parsed.get('finalAnswer'),
                reasoning=parsed.get('reasoning', '')
            )

        except Exception as e:
            print(f"Failed to parse CoT response: {e}")
            # Return fallback structure
            return ChainOfThoughtResult(
                steps=[ReasoningStep(step=1, thought=response_text)],
                final_answer=response_text,
                reasoning='Failed to parse structured response'
            )


class TreeOfThought:
    """
    Tree of Thought (ToT) Reasoning
    Explores multiple reasoning paths and selects the best one
    """

    def __init__(self, ai_client, model: str = None):
        """
        Initialize Tree of Thought reasoner

        Args:
            ai_client: AI client instance
            model: Model to use (optional)
        """
        self.ai_client = ai_client
        self.model = model or os.getenv('AI_MODEL', 'claude-sonnet-4-5-20250929')

        logger.info(
            "tot_initialized",
            model=self.model,
            message="Tree of Thought reasoner initialized"
        )

    def reason(
        self,
        prompt: str,
        context: str,
        branching_factor: int = 3,
        max_depth: int = 3,
        evaluation_criteria: str = "correctness and completeness"
    ) -> TreeOfThoughtResult:
        """
        Execute Tree of Thought reasoning

        Args:
            prompt: The problem or task
            context: Additional context
            branching_factor: Number of alternative paths to explore
            max_depth: Maximum depth of reasoning tree
            evaluation_criteria: Criteria for evaluating paths

        Returns:
            TreeOfThoughtResult with best path and answer
        """
        # Create root node
        root = ThoughtNode(
            id='root',
            thought='Analyzing problem...',
            state={'prompt': prompt, 'context': context},
            children=[],
            evaluation=0.0,
            depth=0
        )

        # Expand tree
        self._expand_node(root, branching_factor, max_depth, evaluation_criteria)

        # Get all paths
        all_paths = self._get_all_paths(root)

        # Select best path
        best_path = self._select_best_path(all_paths)

        # Synthesize final answer
        final_answer = self._synthesize_final_answer(best_path, prompt, context)

        return TreeOfThoughtResult(
            best_path=best_path,
            all_paths=all_paths,
            final_answer=final_answer,
            reasoning=self._build_reasoning_explanation(best_path)
        )

    def _expand_node(
        self,
        node: ThoughtNode,
        branching_factor: int,
        max_depth: int,
        evaluation_criteria: str
    ):
        """Recursively expand the thought tree"""
        if node.depth >= max_depth:
            node.is_leaf = True
            return

        # Generate alternative thoughts
        thoughts = self._generate_thoughts(node, branching_factor)

        # Create child nodes
        for i, thought in enumerate(thoughts):
            child = ThoughtNode(
                id=f"{node.id}-{i}",
                thought=thought['text'],
                state=thought.get('state', node.state),
                children=[],
                evaluation=thought.get('evaluation', 0.5),
                depth=node.depth + 1
            )

            node.children.append(child)

            # Recursively expand promising nodes
            if thought.get('evaluation', 0.5) > 0.5:
                self._expand_node(child, branching_factor, max_depth, evaluation_criteria)
            else:
                child.is_leaf = True

    def _generate_thoughts(
        self,
        node: ThoughtNode,
        branching_factor: int
    ) -> List[Dict[str, Any]]:
        """Generate alternative thought branches"""
        prompt = f"""Given the current reasoning state:
{json.dumps(node.state, indent=2)}

Current thought: {node.thought}

Generate {branching_factor} different alternative reasoning approaches or next steps.
Each should explore a different angle or strategy.

Provide your response in JSON format:
{{
  "thoughts": [
    {{
      "text": "Description of this reasoning approach",
      "evaluation": 0.85,
      "state": {{"updated": "state"}}
    }}
  ]
}}"""

        try:
            response = self._call_ai(prompt)

            # Parse response
            json_text = response.strip()
            if json_text.startswith('```'):
                json_text = json_text.split('```')[1]
                if json_text.startswith('json'):
                    json_text = json_text[4:]
                json_text = json_text.strip()

            parsed = json.loads(json_text)
            return parsed.get('thoughts', [])

        except Exception as e:
            print(f"Failed to generate thoughts: {e}")
            return [{
                'text': 'Continue with current approach',
                'state': node.state,
                'evaluation': 0.6
            }]

    def _call_ai(self, prompt: str) -> str:
        """Call AI client"""
        ai_provider = os.getenv('AI_PROVIDER', 'anthropic')

        if ai_provider == 'anthropic':
            from anthropic import Anthropic
            client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        elif ai_provider == 'openai':
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.choices[0].message.content

    def _get_all_paths(
        self,
        node: ThoughtNode,
        current_path: List[ThoughtNode] = None
    ) -> List[List[ThoughtNode]]:
        """Get all paths from root to leaves"""
        if current_path is None:
            current_path = []

        new_path = current_path + [node]

        if node.is_leaf or not node.children:
            return [new_path]

        all_paths = []
        for child in node.children:
            child_paths = self._get_all_paths(child, new_path)
            all_paths.extend(child_paths)

        return all_paths

    def _select_best_path(self, paths: List[List[ThoughtNode]]) -> List[ThoughtNode]:
        """Select the best reasoning path"""
        best_path = paths[0] if paths else []
        best_score = 0.0

        for path in paths:
            # Calculate path score
            avg_eval = sum(node.evaluation for node in path) / len(path) if path else 0
            depth_bonus = len(path) * 0.1
            score = avg_eval + depth_bonus

            if score > best_score:
                best_score = score
                best_path = path

        return best_path

    def _synthesize_final_answer(
        self,
        path: List[ThoughtNode],
        original_prompt: str,
        context: str
    ) -> str:
        """Synthesize final answer from best path"""
        path_description = "\n".join([
            f"Step {i+1}: {node.thought}"
            for i, node in enumerate(path)
        ])

        synthesis_prompt = f"""Based on this reasoning path:

{path_description}

Original task: {original_prompt}
Context: {context}

Synthesize the final answer or solution based on this reasoning path.
Provide a clear, actionable result."""

        try:
            return self._call_ai(synthesis_prompt)
        except Exception as e:
            print(f"Failed to synthesize final answer: {e}")
            return path[-1].thought if path else ""

    def _build_reasoning_explanation(self, path: List[ThoughtNode]) -> str:
        """Build human-readable reasoning explanation"""
        if not path:
            return ""

        explanation = []
        for i, node in enumerate(path):
            if i == 0:
                prefix = "🌱 Initial:"
            elif i == len(path) - 1:
                prefix = "🎯 Conclusion:"
            else:
                prefix = f"🔗 Step {i}:"

            explanation.append(f"{prefix} {node.thought}")

        return "\n\n".join(explanation)


def create_reasoning_engine(ai_client=None, model: str = None):
    """
    Factory function to create reasoning engines

    Args:
        ai_client: Optional AI client instance
        model: Optional model name

    Returns:
        Dictionary with chainOfThought and treeOfThought instances
    """
    return {
        'chain_of_thought': ChainOfThought(ai_client, model),
        'tree_of_thought': TreeOfThought(ai_client, model)
    }
