from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Protocol

import httpx

from app.core.config import get_settings


@dataclass(slots=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class LLMResult:
    content: str
    tool_calls: list[ToolCall]


class LLMProvider(Protocol):
    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
        temperature: float,
    ) -> LLMResult: ...


class MockLLMProvider:
    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
        temperature: float,
    ) -> LLMResult:
        last_message = next((message for message in reversed(messages) if message["role"] == "user"), None)
        text = (last_message["content"] if last_message else "").lower()
        tool_calls: list[ToolCall] = []
        if "pago" in text or "cuota" in text or "deuda" in text:
            tool_calls.append(ToolCall(name="get_student_payment_status", arguments={"student_id": "STU-1001"}))
        elif "presentismo" in text or "asistencia" in text:
            tool_calls.append(ToolCall(name="get_student_attendance", arguments={"student_id": "STU-1001"}))
        elif "empleado" in text or "fichada" in text:
            tool_calls.append(ToolCall(name="get_employee_attendance", arguments={"employee_id": "EMP-2001"}))
        elif "alumno" in text or "estudiante" in text:
            tool_calls.append(ToolCall(name="get_student", arguments={"query": text or "alumno"}))
        if tool_calls:
            return LLMResult(
                content="Necesito consultar una herramienta autorizada para responder con datos exactos.",
                tool_calls=tool_calls,
            )
        if "hola" in text:
            return LLMResult(content="Hola. Soy el entorno demo de Personal Chat.", tool_calls=[])
        return LLMResult(
            content="Respuesta demo de Personal Chat. La conversación y permisos están funcionando.",
            tool_calls=[],
        )


def _provider_headers(api_key: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _decode_tool_calls(raw_tool_calls: Any) -> list[ToolCall]:
    tool_calls: list[ToolCall] = []
    if not isinstance(raw_tool_calls, list):
        return tool_calls
    for item in raw_tool_calls:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("tool_name") or "").strip()
        if not name:
            continue
        arguments = item.get("arguments") or item.get("input") or item.get("payload") or {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:  # noqa: BLE001
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {"value": arguments}
        tool_calls.append(ToolCall(name=name, arguments=arguments))
    return tool_calls


def _decode_agent_response(data: Any) -> LLMResult:
    if isinstance(data, dict):
        content = str(data.get("content") or data.get("message") or data.get("text") or data.get("output") or "")
        tool_calls = _decode_tool_calls(data.get("tool_calls") or data.get("tools") or [])
        if not content and isinstance(data.get("result"), dict):
            content = str(data["result"].get("content") or data["result"].get("message") or "")
            tool_calls = _decode_tool_calls(data["result"].get("tool_calls") or [])
        return LLMResult(content=content, tool_calls=tool_calls)
    return LLMResult(content=str(data), tool_calls=[])


class RestAgentProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.endpoint = self.settings.external_agent_rest_url
        self.api_key = self.settings.external_agent_rest_api_key
        if not self.endpoint:
            raise RuntimeError("EXTERNAL_AGENT_REST_URL is not configured")

    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
        temperature: float,
    ) -> LLMResult:
        payload = {
            "provider": "rest",
            "model": model,
            "temperature": temperature,
            "system_prompt": system_prompt,
            "messages": messages,
            "tools": tools,
        }
        try:
            with httpx.Client(timeout=self.settings.external_agent_timeout_seconds) as client:
                response = client.post(self.endpoint, json=payload, headers=_provider_headers(self.api_key))
                response.raise_for_status()
                return _decode_agent_response(response.json())
        except Exception:  # noqa: BLE001
            return MockLLMProvider().generate(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools,
                model=model,
                temperature=temperature,
            )


class McpAgentProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.endpoint = self.settings.external_agent_mcp_url
        self.api_key = self.settings.external_agent_mcp_api_key
        if not self.endpoint:
            raise RuntimeError("EXTERNAL_AGENT_MCP_URL is not configured")

    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
        temperature: float,
    ) -> LLMResult:
        payload = {
            "jsonrpc": "2.0",
            "id": "personal-chat",
            "method": "agent.generate",
            "params": {
                "provider": "mcp",
                "model": model,
                "temperature": temperature,
                "system_prompt": system_prompt,
                "messages": messages,
                "tools": tools,
            },
        }
        try:
            with httpx.Client(timeout=self.settings.external_agent_timeout_seconds) as client:
                response = client.post(self.endpoint, json=payload, headers=_provider_headers(self.api_key))
                response.raise_for_status()
                decoded = response.json()
        except Exception:  # noqa: BLE001
            return MockLLMProvider().generate(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools,
                model=model,
                temperature=temperature,
            )
        if isinstance(decoded, dict) and "result" in decoded:
            return _decode_agent_response(decoded["result"])
        return _decode_agent_response(decoded)


class OpenAIProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        try:
            from openai import OpenAI
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("openai package is not installed") from exc
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model: str,
        temperature: float,
    ) -> LLMResult:
        payload_messages = [{"role": "system", "content": system_prompt}, *messages]
        response = self.client.chat.completions.create(
            model=model or self.settings.openai_model,
            messages=payload_messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
            temperature=temperature,
        )
        choice = response.choices[0]
        content = choice.message.content or ""
        tool_calls = []
        for tool_call in choice.message.tool_calls or []:
            arguments = tool_call.function.arguments or "{}"
            try:
                import json

                parsed_arguments = json.loads(arguments)
            except Exception:  # noqa: BLE001
                parsed_arguments = {}
            tool_calls.append(ToolCall(name=tool_call.function.name, arguments=parsed_arguments))
        return LLMResult(content=content, tool_calls=tool_calls)


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    provider_key = (provider_name or "").strip().lower()
    settings = get_settings()
    if provider_key in {"mock"}:
        return MockLLMProvider()
    if provider_key in {"rest", "external_rest", "rest_agent"}:
        try:
            return RestAgentProvider()
        except Exception:
            return MockLLMProvider()
    if provider_key in {"mcp", "external_mcp", "mcp_agent"}:
        try:
            return McpAgentProvider()
        except Exception:
            return MockLLMProvider()
    if provider_key in {"openai", ""} and settings.openai_api_key:
        try:
            return OpenAIProvider()
        except Exception:
            return MockLLMProvider()
    return MockLLMProvider()
