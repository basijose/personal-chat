from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Agent, AgentTool, Conversation, Message, Tool, User
from app.services.audit import write_audit
from app.services.llm_providers import LLMProvider, ToolCall, get_llm_provider
from app.services.rbac import permission_allows
from app.services.tool_executors import ToolExecutionError, get_executor, tool_schema


@dataclass(slots=True)
class ChatResult:
    conversation: Conversation
    assistant_message: Message


def _authorized_agent_query(user: User, organization_id: int):
    stmt = select(Agent).where(Agent.organization_id == organization_id, Agent.active.is_(True))
    if user.is_superadmin:
        return stmt
    role_ids = [role.id for role in user.roles]
    if not role_ids:
        return stmt.where(False)
    return stmt.join(Agent.roles).where(Agent.roles.any())


def user_can_use_agent(user: User, agent: Agent) -> bool:
    if not user.active or not agent.active:
        return False
    if user.is_superadmin:
        return True
    user_role_ids = {role.id for role in user.roles}
    agent_role_ids = {role.id for role in agent.roles}
    return bool(user_role_ids.intersection(agent_role_ids))


def get_allowed_tools_for_agent(db: Session, agent: Agent) -> list[Tool]:
    stmt = (
        select(Tool)
        .join(AgentTool, AgentTool.tool_id == Tool.id)
        .where(
            Tool.organization_id == agent.organization_id,
            Tool.active.is_(True),
            AgentTool.agent_id == agent.id,
            AgentTool.active.is_(True),
        )
    )
    return list(db.execute(stmt).scalars().all())


def _tool_permission_for_agent(db: Session, agent_id: int, tool_id: int) -> AgentTool | None:
    stmt = select(AgentTool).where(
        AgentTool.agent_id == agent_id,
        AgentTool.tool_id == tool_id,
        AgentTool.active.is_(True),
    )
    return db.execute(stmt).scalar_one_or_none()


def build_messages_history(conversation: Conversation) -> list[dict[str, Any]]:
    return [
        {"role": message.role, "content": message.content, "metadata": message.metadata_}
        for message in conversation.messages
    ]


def execute_tool_call(
    db: Session,
    *,
    conversation: Conversation,
    user: User,
    agent: Agent,
    tool_call: ToolCall,
) -> tuple[dict[str, Any], Tool]:
    tool = db.execute(
        select(Tool).where(Tool.organization_id == conversation.organization_id, Tool.slug == tool_call.name)
    ).scalar_one_or_none()
    if not tool:
        raise ToolExecutionError(f"Tool {tool_call.name} not found")
    agent_tool = _tool_permission_for_agent(db, agent.id, tool.id)
    if not agent_tool or not permission_allows("execute", agent_tool.permission_level):
        raise ToolExecutionError(f"Tool {tool.slug} is not authorized for this agent")
    executor = get_executor(tool.tool_type)
    result = executor.execute(
        db,
        tool,
        tool_call.arguments,
        user_id=user.id,
        organization_id=conversation.organization_id,
        context={
            "conversation_id": conversation.id,
            "conversation_title": conversation.title,
            "agent_id": agent.id,
            "agent_slug": agent.slug,
            "agent_name": agent.name,
        },
    )
    write_audit(
        db,
        organization_id=conversation.organization_id,
        user_id=user.id,
        agent_id=agent.id,
        tool_id=tool.id,
        action="tool_execution",
        request_summary=f"{tool.slug} inputs={tool_call.arguments}",
        result_summary=str(result)[:1000],
        status="ok",
    )
    return result, tool


def run_agent_chat(
    db: Session,
    *,
    user: User,
    agent: Agent,
    user_message: str,
    conversation: Conversation,
    llm_provider: LLMProvider | None = None,
) -> ChatResult:
    provider = llm_provider or get_llm_provider(agent.provider)
    tool_models = get_allowed_tools_for_agent(db, agent)
    history = build_messages_history(conversation)
    history.append({"role": "user", "content": user_message, "metadata": {}})

    tool_defs = [tool_schema(tool) for tool in tool_models]
    result = provider.generate(
        system_prompt=agent.system_prompt or "You are a corporate assistant.",
        messages=history,
        tools=tool_defs,
        model=agent.model,
        temperature=agent.temperature,
    )

    assistant_text = result.content
    if result.tool_calls:
        tool_outputs = []
        for tool_call in result.tool_calls:
            execution_result, tool = execute_tool_call(
                db,
                conversation=conversation,
                user=user,
                agent=agent,
                tool_call=tool_call,
            )
            tool_outputs.append({"tool": tool.slug, "result": execution_result})
        assistant_text = (
            "Consulté herramientas autorizadas y obtuve: "
            + " | ".join([str(output["result"]) for output in tool_outputs])[:3500]
        )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_text,
        metadata_={"provider": agent.provider, "model": agent.model},
    )
    db.add(assistant_message)
    db.flush()
    write_audit(
        db,
        organization_id=conversation.organization_id,
        user_id=user.id,
        agent_id=agent.id,
        tool_id=None,
        action="chat_response",
        request_summary=user_message[:1000],
        result_summary=assistant_text[:1000],
        status="ok",
    )
    return ChatResult(conversation=conversation, assistant_message=assistant_message)
