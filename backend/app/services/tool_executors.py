from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
import os
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Tool


class ToolExecutionError(RuntimeError):
    pass


class ToolExecutor(ABC):
    slug: str

    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        db: Session,
        tool: Tool,
        inputs: dict[str, Any],
        *,
        user_id: int,
        organization_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


def _tool_config_value(tool: Tool, key: str, default: Any = None) -> Any:
    configuration = tool.configuration or {}
    if isinstance(configuration, dict) and key in configuration:
        value = configuration.get(key)
        if value not in (None, ""):
            return value
    return default


def _resolve_env_reference(tool: Tool, value_key: str, env_key_key: str, default: Any = None) -> Any:
    value = _tool_config_value(tool, value_key)
    if value not in (None, ""):
        return value
    env_key = _tool_config_value(tool, env_key_key)
    if env_key:
        env_value = os.environ.get(str(env_key))
        if env_value not in (None, ""):
            return env_value
    return default


def _normalize_json_response(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        for candidate in ("result", "output", "data"):
            nested = data.get(candidate)
            if isinstance(nested, dict):
                return nested
        return data
    return {"result": data}


def _json_response_text(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except Exception:  # noqa: BLE001
        data = {"body": response.text}
    return _normalize_json_response(data)


def _build_context_payload(
    tool: Tool,
    inputs: dict[str, Any],
    *,
    user_id: int,
    organization_id: int,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "tool_slug": tool.slug,
        "tool_name": tool.name,
        "organization_id": organization_id,
        "user_id": user_id,
        "inputs": inputs,
        "context": context or {},
    }


def _post_json(url: str, *, payload: dict[str, Any], timeout_seconds: float, headers: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return _json_response_text(response)
    except Exception as exc:  # noqa: BLE001
        raise ToolExecutionError(f"request failed: {exc}") from exc


class StudentDataStore:
    _students = [
        {
            "student_id": "STU-1001",
            "document_number": "30111222",
            "name": "Camila Herrera",
            "status": "active",
            "grade": "6A",
            "attendance_rate": 0.96,
        },
        {
            "student_id": "STU-1002",
            "document_number": "29444111",
            "name": "Tomás Vega",
            "status": "active",
            "grade": "5B",
            "attendance_rate": 0.89,
        },
        {
            "student_id": "STU-1003",
            "document_number": "28333999",
            "name": "Sofía Luna",
            "status": "inactive",
            "grade": "4C",
            "attendance_rate": 0.91,
        },
    ]

    @classmethod
    def find_student(cls, student_id: str | None, document_number: str | None, query: str | None) -> dict[str, Any]:
        query_lower = (query or "").strip().lower()
        for student in cls._students:
            if student_id and student["student_id"] == student_id:
                return student
            if document_number and student["document_number"] == document_number:
                return student
            if query_lower and query_lower in student["name"].lower():
                return student
        return cls._students[0]


class GetStudentExecutor(ToolExecutor):
    slug = "get_student"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "student_id": {"type": "string"},
                "document_number": {"type": "string"},
                "query": {"type": "string"},
            },
            "additionalProperties": False,
        }

    def execute(
        self,
        db: Session,
        tool: Tool,
        inputs: dict[str, Any],
        *,
        user_id: int,
        organization_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        webhook_url = _resolve_env_reference(tool, "webhook_url", "webhook_url_env", default=None)
        timeout_seconds = float(_tool_config_value(tool, "timeout_seconds", 10))
        if webhook_url:
            payload = _build_context_payload(tool, inputs, user_id=user_id, organization_id=organization_id, context=context)
            try:
                remote_result = _post_json(str(webhook_url), payload=payload, timeout_seconds=timeout_seconds)
                if "source" not in remote_result:
                    remote_result["source"] = "n8n"
                return remote_result
            except ToolExecutionError:
                pass
        student = StudentDataStore.find_student(
            inputs.get("student_id"),
            inputs.get("document_number"),
            inputs.get("query"),
        )
        return {"student": student, "source": "mock"}


class GetStudentPaymentStatusExecutor(ToolExecutor):
    slug = "get_student_payment_status"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"student_id": {"type": "string"}},
            "required": ["student_id"],
            "additionalProperties": False,
        }

    def execute(
        self,
        db: Session,
        tool: Tool,
        inputs: dict[str, Any],
        *,
        user_id: int,
        organization_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        student = StudentDataStore.find_student(inputs["student_id"], None, None)
        invoices = [
            {"period": "2026-05", "amount": 120000, "status": "paid"},
            {"period": "2026-06", "amount": 120000, "status": "paid"},
            {"period": "2026-07", "amount": 125000, "status": "due"},
        ]
        debt = sum(item["amount"] for item in invoices if item["status"] != "paid")
        return {"student": student, "invoices": invoices, "debt": debt, "currency": "ARS", "source": "mock"}


class GetStudentAttendanceExecutor(ToolExecutor):
    slug = "get_student_attendance"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "student_id": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
            },
            "required": ["student_id"],
            "additionalProperties": False,
        }

    def execute(
        self,
        db: Session,
        tool: Tool,
        inputs: dict[str, Any],
        *,
        user_id: int,
        organization_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = date.today() - timedelta(days=10)
        entries = []
        for index in range(8):
            day = start + timedelta(days=index)
            entries.append(
                {
                    "date": day.isoformat(),
                    "present": index % 5 != 2,
                    "reason": "fictitious record",
                }
            )
        return {"student_id": inputs["student_id"], "attendance": entries, "source": "mock"}


class GetEmployeeAttendanceExecutor(ToolExecutor):
    slug = "get_employee_attendance"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string"},
                "date_from": {"type": "string"},
                "date_to": {"type": "string"},
            },
            "required": ["employee_id"],
            "additionalProperties": False,
        }

    def execute(
        self,
        db: Session,
        tool: Tool,
        inputs: dict[str, Any],
        *,
        user_id: int,
        organization_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = date.today() - timedelta(days=7)
        entries = []
        for index in range(6):
            entries.append(
                {
                    "timestamp": (start + timedelta(days=index)).isoformat() + "T08:0{}:00".format(index % 5),
                    "event": "check_in" if index % 2 == 0 else "check_out",
                    "terminal": "main_gate",
                }
            )
        return {"employee_id": inputs["employee_id"], "records": entries, "source": "mock"}


class N8nWebhookExecutor(ToolExecutor):
    slug = "n8n_webhook"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"payload": {"type": "object"}},
            "required": ["payload"],
            "additionalProperties": True,
        }

    def execute(
        self,
        db: Session,
        tool: Tool,
        inputs: dict[str, Any],
        *,
        user_id: int,
        organization_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        webhook_url = (
            _tool_config_value(tool, "webhook_url")
            or _resolve_env_reference(tool, "webhook_url", "webhook_url_env")
            or settings.n8n_sample_webhook_url
        )
        if not webhook_url:
            raise ToolExecutionError("n8n webhook URL not configured")
        timeout = float(_tool_config_value(tool, "timeout_seconds", 10))
        payload = _build_context_payload(tool, inputs, user_id=user_id, organization_id=organization_id, context=context)
        remote_result = _post_json(str(webhook_url), payload=payload, timeout_seconds=timeout)
        remote_result.setdefault("source", "n8n")
        return remote_result


class ExternalAgentExecutor(ToolExecutor):
    slug = "external_agent"

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "payload": {"type": "object"},
            },
            "required": ["payload"],
            "additionalProperties": True,
        }

    def execute(
        self,
        db: Session,
        tool: Tool,
        inputs: dict[str, Any],
        *,
        user_id: int,
        organization_id: int,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        settings = get_settings()
        transport = str(_tool_config_value(tool, "transport", "rest")).strip().lower()
        endpoint = _resolve_env_reference(tool, "endpoint_url", "endpoint_url_env", default=None)
        api_key = _resolve_env_reference(tool, "api_key", "api_key_env", default=None)
        timeout_seconds = float(_tool_config_value(tool, "timeout_seconds", settings.external_agent_timeout_seconds))
        if not endpoint:
            raise ToolExecutionError("external agent endpoint not configured")
        payload = _build_context_payload(
            tool,
            inputs.get("payload", inputs),
            user_id=user_id,
            organization_id=organization_id,
            context={
                **(context or {}),
                "transport": transport,
                "tool_configuration": {
                    key: value
                    for key, value in (tool.configuration or {}).items()
                    if key not in {"api_key", "api_key_env"}
                },
            },
        )
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if transport == "mcp":
            request_payload = {
                "jsonrpc": "2.0",
                "id": f"personal-chat-{tool.id}",
                "method": "agent.generate",
                "params": payload,
            }
            response_data = _post_json(str(endpoint), payload=request_payload, timeout_seconds=timeout_seconds, headers=headers)
            return {
                "source": "mcp",
                **response_data,
            }
        response_data = _post_json(str(endpoint), payload=payload, timeout_seconds=timeout_seconds, headers=headers)
        response_data.setdefault("source", "rest")
        return response_data


EXECUTOR_REGISTRY: dict[str, ToolExecutor] = {
    executor.slug: executor
    for executor in [
        GetStudentExecutor(),
        GetStudentPaymentStatusExecutor(),
        GetStudentAttendanceExecutor(),
        GetEmployeeAttendanceExecutor(),
        N8nWebhookExecutor(),
        ExternalAgentExecutor(),
    ]
}
EXECUTOR_REGISTRY["rest_agent"] = EXECUTOR_REGISTRY["external_agent"]
EXECUTOR_REGISTRY["mcp_agent"] = EXECUTOR_REGISTRY["external_agent"]


def get_executor(tool_type: str) -> ToolExecutor:
    executor = EXECUTOR_REGISTRY.get(tool_type)
    if executor:
        return executor
    return EXECUTOR_REGISTRY["n8n_webhook"]


def tool_schema(tool: Tool) -> dict[str, Any]:
    executor = get_executor(tool.tool_type)
    return {
        "type": "function",
        "function": {
            "name": tool.slug,
            "description": tool.description,
            "parameters": executor.input_schema(),
        },
    }
