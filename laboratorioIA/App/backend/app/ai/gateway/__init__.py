def __getattr__(name):
    if name == "run_agent_chat":
        from .orchestrator import run_agent_chat

        return run_agent_chat
    raise AttributeError(name)


__all__ = ["run_agent_chat"]
