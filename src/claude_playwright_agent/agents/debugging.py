"""
Interactive Debugging Mode for Claude Playwright Agent.

This module implements:
- Interactive debugging for test execution
- Breakpoint management
- Step-by-step execution
- State inspection at breakpoints
- Variable inspection
- Call stack navigation
"""

import asyncio
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import traceback


# =============================================================================
# Debugging Models
# =============================================================================


class DebugState(str, Enum):
    """Debug execution state."""

    IDLE = "idle"           # Not debugging
    RUNNING = "running"     # Executing normally
    PAUSED = "paused"       # Paused at breakpoint
    STEPPING = "stepping"   # Stepping through code
    COMPLETED = "completed" # Execution finished
    ERROR = "error"         # Error occurred


class StepMode(str, Enum):
    """Step execution modes."""

    STEP_OVER = "step_over"   # Step over current line
    STEP_INTO = "step_into"   # Step into function call
    STEP_OUT = "step_out"     # Step out of current function
    CONTINUE = "continue"     # Continue to next breakpoint
    NEXT = "next"            # Next line


@dataclass
class Breakpoint:
    """
    A breakpoint in the execution.

    Attributes:
        id: Unique breakpoint identifier
        file_path: Path to file
        line_number: Line number
        condition: Optional condition to trigger breakpoint
        hit_count: Number of times breakpoint was hit
        enabled: Whether breakpoint is enabled
        log_message: Optional message to log when hit
    """

    id: str
    file_path: Path
    line_number: int
    condition: str = ""
    hit_count: int = 0
    enabled: bool = True
    log_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "condition": self.condition,
            "hit_count": self.hit_count,
            "enabled": self.enabled,
            "log_message": self.log_message,
        }


@dataclass
class StackFrame:
    """
    A frame in the call stack.

    Attributes:
        frame_id: Unique frame identifier
        function_name: Name of the function
        file_path: Path to source file
        line_number: Current line number
        locals: Local variables in this frame
        is_current: Whether this is the current frame
    """

    frame_id: str
    function_name: str
    file_path: Path
    line_number: int
    locals: dict[str, Any] = field(default_factory=dict)
    is_current: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frame_id": self.frame_id,
            "function_name": self.function_name,
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "locals": self.locals,
            "is_current": self.is_current,
        }


@dataclass
class Variable:
    """
    A variable in the debug context.

    Attributes:
        name: Variable name
        value: Variable value
        type: Variable type
        is mutable: Whether variable can be modified
    """

    name: str
    value: Any
    type: str = ""
    is_mutable: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": str(self.value),
            "type": self.type or type(self.value).__name__,
            "is_mutable": self.is_mutable,
        }


@dataclass
class DebugSession:
    """
    A debug session for tracking execution state.

    Attributes:
        session_id: Unique session identifier
        state: Current debug state
        breakpoints: List of breakpoints
        call_stack: Current call stack
        current_frame: Current stack frame
        variables: Variables in current scope
        start_time: When session started
    """

    session_id: str
    state: DebugState = DebugState.IDLE
    breakpoints: list[Breakpoint] = field(default_factory=list)
    call_stack: list[StackFrame] = field(default_factory=list)
    current_frame: StackFrame | None = None
    variables: dict[str, Variable] = field(default_factory=dict)
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    output: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "breakpoints": [b.to_dict() for b in self.breakpoints],
            "call_stack": [f.to_dict() for f in self.call_stack],
            "current_frame": self.current_frame.to_dict() if self.current_frame else None,
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
            "start_time": self.start_time,
            "output": self.output,
        }


# =============================================================================
# Interactive Debugger
# =============================================================================


class InteractiveDebugger:
    """
    Interactive debugger for test execution.

    Features:
    - Breakpoint management
    - Step execution
    - Stack inspection
    - Variable inspection
    - Expression evaluation
    - Output capture
    """

    def __init__(self) -> None:
        """Initialize the interactive debugger."""
        self._session: DebugSession | None = None
        self._breakpoint_counter = 0
        self._frame_counter = 0
        self._step_mode: StepMode | None = None
        self._pause_event: asyncio.Event | None = None

    def create_session(self, session_id: str = "") -> DebugSession:
        """
        Create a new debug session.

        Args:
            session_id: Optional session identifier

        Returns:
            New debug session
        """
        import uuid
        if not session_id:
            session_id = f"debug_{uuid.uuid4().hex[:8]}"

        self._session = DebugSession(session_id=session_id)
        self._pause_event = asyncio.Event()
        return self._session

    def get_session(self) -> DebugSession | None:
        """Get the current debug session."""
        return self._session

    def set_breakpoint(
        self,
        file_path: Path | str,
        line_number: int,
        condition: str = "",
        log_message: str = "",
    ) -> Breakpoint:
        """
        Set a breakpoint.

        Args:
            file_path: Path to file
            line_number: Line number
            condition: Optional condition to trigger breakpoint
            log_message: Optional message to log

        Returns:
            Created breakpoint
        """
        self._breakpoint_counter += 1
        bp_id = f"bp_{self._breakpoint_counter}"

        breakpoint = Breakpoint(
            id=bp_id,
            file_path=Path(file_path),
            line_number=line_number,
            condition=condition,
            log_message=log_message,
        )

        if self._session:
            self._session.breakpoints.append(breakpoint)

        return breakpoint

    def clear_breakpoint(self, breakpoint_id: str) -> bool:
        """
        Clear a breakpoint.

        Args:
            breakpoint_id: ID of breakpoint to clear

        Returns:
            True if breakpoint was cleared
        """
        if not self._session:
            return False

        for i, bp in enumerate(self._session.breakpoints):
            if bp.id == breakpoint_id:
                self._session.breakpoints.pop(i)
                return True

        return False

    def clear_all_breakpoints(self) -> None:
        """Clear all breakpoints."""
        if self._session:
            self._session.breakpoints.clear()

    def list_breakpoints(self) -> list[Breakpoint]:
        """List all breakpoints."""
        if self._session:
            return self._session.breakpoints.copy()
        return []

    def check_breakpoint(
        self,
        file_path: Path | str,
        line_number: int,
        context: dict[str, Any] | None = None,
    ) -> Breakpoint | None:
        """
        Check if execution hits a breakpoint.

        Args:
            file_path: Current file path
            line_number: Current line number
            context: Execution context for condition evaluation

        Returns:
            Hit breakpoint or None
        """
        if not self._session:
            return None

        file_path = Path(file_path)

        for bp in self._session.breakpoints:
            if not bp.enabled:
                continue

            if bp.file_path == file_path and bp.line_number == line_number:
                # Check condition if present
                if bp.condition:
                    try:
                        if context:
                            if not eval(bp.condition, {}, context):
                                continue
                    except Exception:
                        continue

                bp.hit_count += 1
                return bp

        return None

    def pause(self, reason: str = "") -> None:
        """
        Pause execution.

        Args:
            reason: Reason for pausing
        """
        if self._session:
            self._session.state = DebugState.PAUSED
            if reason:
                self._session.output.append(f"Paused: {reason}")

        if self._pause_event:
            self._pause_event.set()

    def resume(self) -> None:
        """Resume execution."""
        if self._session:
            self._session.state = DebugState.RUNNING
            self._session.output.append("Resumed")

        if self._pause_event:
            self._pause_event.clear()

    def step(self, mode: StepMode) -> None:
        """
        Step execution.

        Args:
            mode: Step mode
        """
        self._step_mode = mode
        if self._session:
            self._session.state = DebugState.STEPPING
            self._session.output.append(f"Stepping: {mode.value}")

        if self._pause_event:
            self._pause_event.set()

    async def wait_for_continue(self) -> None:
        """Wait for continue signal (used when paused)."""
        if self._pause_event:
            await self._pause_event.wait()
            self._pause_event.clear()

    def update_stack(
        self,
        function_name: str,
        file_path: Path | str,
        line_number: int,
        locals: dict[str, Any] | None = None,
    ) -> None:
        """
        Update the current call stack.

        Args:
            function_name: Current function name
            file_path: Current file path
            line_number: Current line number
            locals: Local variables
        """
        if not self._session:
            return

        self._frame_counter += 1
        frame = StackFrame(
            frame_id=f"frame_{self._frame_counter}",
            function_name=function_name,
            file_path=Path(file_path),
            line_number=line_number,
            locals=locals or {},
            is_current=True,
        )

        # Mark previous frames as not current
        for f in self._session.call_stack:
            f.is_current = False

        self._session.call_stack.append(frame)
        self._session.current_frame = frame

        # Update variables
        if locals:
            self._session.variables = {
                k: Variable(name=k, value=v)
                for k, v in locals.items()
            }

    def pop_stack(self) -> None:
        """Pop the top frame from the call stack."""
        if self._session and self._session.call_stack:
            self._session.call_stack.pop()
            if self._session.call_stack:
                self._session.current_frame = self._session.call_stack[-1]
                self._session.current_frame.is_current = True
            else:
                self._session.current_frame = None

    def get_variable(self, name: str) -> Variable | None:
        """
        Get a variable from the current context.

        Args:
            name: Variable name

        Returns:
            Variable or None if not found
        """
        if self._session:
            return self._session.variables.get(name)
        return None

    def set_variable(self, name: str, value: Any) -> bool:
        """
        Set a variable in the current context.

        Args:
            name: Variable name
            value: New value

        Returns:
            True if variable was set
        """
        if self._session and name in self._session.variables:
            self._session.variables[name] = Variable(
                name=name,
                value=value,
            )
            return True
        return False

    def evaluate_expression(
        self,
        expression: str,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Evaluate an expression in the current context.

        Args:
            expression: Expression to evaluate
            context: Execution context

        Returns:
            Result of evaluation
        """
        if not self._session:
            return None

        # Merge variables with provided context
        eval_context = {k: v.value for k, v in self._session.variables.items()}
        if context:
            eval_context.update(context)

        try:
            return eval(expression, {}, eval_context)
        except Exception as e:
            return f"Error: {e}"

    def log(self, message: str) -> None:
        """
        Log a message to the debug output.

        Args:
            message: Message to log
        """
        if self._session:
            self._session.output.append(message)

    def complete(self) -> None:
        """Mark the debug session as completed."""
        if self._session:
            self._session.state = DebugState.COMPLETED
            self._session.output.append("Debug session completed")


# =============================================================================
# Debug Context Manager
# =============================================================================


class DebugContext:
    """
    Context manager for debug sessions.

    Automatically manages debug session lifecycle.
    """

    def __init__(
        self,
        debugger: InteractiveDebugger,
        session_id: str = "",
    ) -> None:
        """
        Initialize the debug context.

        Args:
            debugger: Interactive debugger instance
            session_id: Optional session identifier
        """
        self._debugger = debugger
        self._session_id = session_id

    async def __aenter__(self) -> DebugSession:
        """Enter debug context."""
        return self._debugger.create_session(self._session_id)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit debug context."""
        if exc_val:
            self._debugger.log(f"Exception: {exc_val}")
        self._debugger.complete()


# =============================================================================
# Test Execution with Debugging
# =============================================================================


class DebuggableTestExecutor:
    """
    Test executor with debugging support.

    Wraps test execution with interactive debugging capabilities.
    """

    def __init__(
        self,
        debugger: InteractiveDebugger | None = None,
    ) -> None:
        """
        Initialize the executor.

        Args:
            debugger: Optional debugger instance (creates new if None)
        """
        self._debugger = debugger or InteractiveDebugger()

    async def execute_with_debugging(
        self,
        test_func: Callable,
        test_args: dict[str, Any] | None = None,
        breakpoints: list[tuple[Path, int]] | None = None,
    ) -> DebugSession:
        """
        Execute a test function with debugging support.

        Args:
            test_func: Test function to execute
            test_args: Arguments to pass to test function
            breakpoints: List of (file_path, line_number) breakpoints

        Returns:
            Debug session with execution results
        """
        session = self._debugger.create_session()
        test_args = test_args or {}

        # Set breakpoints
        if breakpoints:
            for file_path, line_number in breakpoints:
                self._debugger.set_breakpoint(file_path, line_number)

        session.state = DebugState.RUNNING
        self._debugger.log("Starting test execution with debugging...")

        try:
            # Update stack for test entry
            self._debugger.update_stack(
                function_name=test_func.__name__,
                file_path=getattr(test_func, "__code__", {}).co_filename or "unknown",
                line_number=1,
                locals=test_args,
            )

            # Execute test
            result = await self._execute_test_with_breakpoints(
                test_func, test_args
            )

            session.state = DebugState.COMPLETED
            self._debugger.log(f"Test completed: {result}")

        except Exception as e:
            session.state = DebugState.ERROR
            self._debugger.log(f"Test error: {e}")
            self._debugger.log(traceback.format_exc())

        return session

    async def _execute_test_with_breakpoints(
        self,
        test_func: Callable,
        test_args: dict[str, Any],
    ) -> Any:
        """
        Execute test while checking for breakpoints.

        Args:
            test_func: Test function
            test_args: Test arguments

        Returns:
            Test result
        """
        # Get function code object
        code = getattr(test_func, "__code__", None)
        if not code:
            return await test_func(**test_args)

        file_path = code.co_filename
        current_line = code.co_firstlineno

        # Check for breakpoint at entry
        bp = self._debugger.check_breakpoint(file_path, current_line, test_args)
        if bp:
            self._debugger.pause(f"Breakpoint hit: {bp.id}")
            self._debugger.log(f"Breakpoint at {file_path}:{current_line}")
            await self._debugger.wait_for_continue()

        # Execute the test
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func(**test_args)
        else:
            result = test_func(**test_args)

        return result


# =============================================================================
# Convenience Functions
# =============================================================================


def create_debugger() -> InteractiveDebugger:
    """Create a new interactive debugger."""
    return InteractiveDebugger()


def create_debug_context(
    debugger: InteractiveDebugger | None = None,
    session_id: str = "",
) -> DebugContext:
    """
    Create a debug context manager.

    Args:
        debugger: Optional debugger instance
        session_id: Optional session identifier

    Returns:
        Debug context manager
    """
    return DebugContext(debugger or create_debugger(), session_id)
