from __future__ import annotations

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Agent, Organization, Role, Tool, User
from app.services.crud import assign_role_to_agent, assign_role_to_user, assign_tool_to_agent


def seed_db(db) -> None:
    settings = get_settings()
    organization = db.query(Organization).filter(Organization.slug == "personal-chat-demo").one_or_none()
    if organization is None:
        organization = Organization(name="Personal Chat Demo", slug="personal-chat-demo", active=True)
        db.add(organization)
        db.flush()

    roles = {}
    for name, desc in [
        ("Administrador", "Acceso completo al panel"),
        ("Docente", "Acceso a alumnos y presentismo"),
        ("Administración", "Acceso a alumnos, pagos y presentismo"),
        ("RRHH", "Acceso a presentismo de empleados"),
    ]:
        role = db.query(Role).filter(Role.organization_id == organization.id, Role.name == name).one_or_none()
        if role is None:
            role = Role(organization_id=organization.id, name=name, description=desc)
            db.add(role)
            db.flush()
        roles[name] = role

    users = {
        "admin": ("admin@personalchat.local", "Administrador", True, True, ["Administrador"]),
        "docente": ("docente@personalchat.local", "Docente", False, True, ["Docente"]),
        "administracion": ("administracion@personalchat.local", "Administración", False, True, ["Administración"]),
        "rrhh": ("rrhh@personalchat.local", "RRHH", False, True, ["RRHH"]),
    }
    for username, (email, first_name, is_superadmin, active, role_names) in users.items():
        user = db.query(User).filter(User.organization_id == organization.id, User.username == username).one_or_none()
        if user is None:
            user = User(
                organization_id=organization.id,
                username=username,
                email=email,
                password_hash=hash_password(settings.demo_seed_password),
                first_name=first_name,
                last_name="",
                active=active,
                is_superadmin=is_superadmin,
            )
            db.add(user)
            db.flush()
        else:
            user.password_hash = hash_password(settings.demo_seed_password)
            user.active = active
            user.is_superadmin = is_superadmin
        for role_name in role_names:
            assign_role_to_user(db, user, roles[role_name])

    tool_data = [
        (
            "get_student",
            "Consulta datos ficticios de alumnos o deriva a N8N si se configura un webhook",
            "get_student",
            {
                "webhook_url_env": "N8N_GET_STUDENT_WEBHOOK_URL",
                "timeout_seconds": 10,
            },
        ),
        ("get_student_payment_status", "Consulta cuotas y deuda ficticia", "get_student_payment_status", {}),
        ("get_student_attendance", "Consulta presentismo ficticio de alumnos", "get_student_attendance", {}),
        ("get_employee_attendance", "Consulta fichadas ficticias de empleados", "get_employee_attendance", {}),
    ]
    tools = {}
    for slug, description, tool_type, configuration in tool_data:
        tool = db.query(Tool).filter(Tool.organization_id == organization.id, Tool.slug == slug).one_or_none()
        if tool is None:
            tool = Tool(
                organization_id=organization.id,
                name=slug.replace("_", " ").title(),
                slug=slug,
                description=description,
                tool_type=tool_type,
                configuration=configuration,
                active=True,
            )
            db.add(tool)
            db.flush()
        tools[slug] = tool

    agents = {
        "alumnos": {
            "name": "Alumnos",
            "slug": "alumnos",
            "description": "Consulta de datos de alumnos",
            "system_prompt": "Eres el agente de alumnos. Responde con claridad y usa herramientas autorizadas.",
            "provider": "mock",
            "model": "mock",
            "temperature": 0.2,
            "roles": ["Administrador", "Docente", "Administración"],
            "tools": ["get_student", "get_student_attendance"],
        },
        "pagos": {
            "name": "Pagos",
            "slug": "pagos",
            "description": "Consulta de cuotas, deuda y estado de cuenta",
            "system_prompt": "Eres el agente de pagos. Solo responde con datos de pagos y deuda.",
            "provider": "mock",
            "model": "mock",
            "temperature": 0.2,
            "roles": ["Administrador", "Administración"],
            "tools": ["get_student_payment_status", "get_student"],
        },
        "presentismo-alumnos": {
            "name": "Presentismo Alumnos",
            "slug": "presentismo-alumnos",
            "description": "Consulta de presentismo de alumnos",
            "system_prompt": "Eres el agente de presentismo de alumnos.",
            "provider": "mock",
            "model": "mock",
            "temperature": 0.2,
            "roles": ["Administrador", "Docente", "Administración"],
            "tools": ["get_student_attendance", "get_student"],
        },
        "presentismo-empleados": {
            "name": "Presentismo Empleados",
            "slug": "presentismo-empleados",
            "description": "Consulta de fichadas de empleados",
            "system_prompt": "Eres el agente de presentismo de empleados.",
            "provider": "mock",
            "model": "mock",
            "temperature": 0.2,
            "roles": ["Administrador", "RRHH"],
            "tools": ["get_employee_attendance"],
        },
        "externo-rest": {
            "name": "Agente Externo REST",
            "slug": "externo-rest",
            "description": "Agente externo conectado por REST",
            "system_prompt": "Eres un agente externo integrado por REST. Responde con precisión y usa el formato solicitado por el backend.",
            "provider": "rest",
            "model": "external-rest",
            "temperature": 0.1,
            "roles": ["Administrador"],
            "tools": [],
        },
        "externo-mcp": {
            "name": "Agente Externo MCP",
            "slug": "externo-mcp",
            "description": "Agente externo conectado por MCP",
            "system_prompt": "Eres un agente externo integrado por MCP. Responde con precisión y usa el formato solicitado por el backend.",
            "provider": "mcp",
            "model": "external-mcp",
            "temperature": 0.1,
            "roles": ["Administrador"],
            "tools": [],
        },
    }
    for key, data in agents.items():
        agent = db.query(Agent).filter(Agent.organization_id == organization.id, Agent.slug == data["slug"]).one_or_none()
        if agent is None:
            agent = Agent(
                organization_id=organization.id,
                name=data["name"],
                slug=data["slug"],
                description=data["description"],
                system_prompt=data["system_prompt"],
                provider=data["provider"],
                model=data["model"],
                temperature=data["temperature"],
                active=True,
            )
            db.add(agent)
            db.flush()
        for role_name in data["roles"]:
            assign_role_to_agent(db, agent, roles[role_name])
        for tool_slug in data["tools"]:
            assign_tool_to_agent(db, agent, tools[tool_slug], permission_level="execute")

    db.commit()


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_db(db)


if __name__ == "__main__":
    seed()
