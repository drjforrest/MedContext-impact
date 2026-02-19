import functools
import inspect
import logging
from typing import Any, Callable, TypedDict

logger = logging.getLogger(__name__)


# Re-defining AgentError here for use in the decorator
class AgentError(TypedDict):
    tool: str
    message: str
    fatal: bool


def resilient_node(fatal=False):
    """
    Decorator for LangGraph nodes to catch exceptions and update the state's 'errors' list.
    """

    def decorator(func: Callable):
        def _handle_error(state: Any, e: Exception) -> Any:
            error_msg = f"Error in {func.__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)

            if "errors" not in state or state["errors"] is None:
                state["errors"] = []

            state["errors"].append(
                {"tool": func.__name__, "message": str(e), "fatal": fatal}
            )
            return state

        @functools.wraps(func)
        async def async_wrapper(self, state: Any, **kwargs):
            try:
                if inspect.iscoroutinefunction(func):
                    return await func(self, state, **kwargs)
                return func(self, state, **kwargs)
            except Exception as e:
                return _handle_error(state, e)

        @functools.wraps(func)
        def sync_wrapper(self, state: Any, **kwargs):
            try:
                return func(self, state, **kwargs)
            except Exception as e:
                return _handle_error(state, e)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
