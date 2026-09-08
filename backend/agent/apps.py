from django.apps import AppConfig


class AgentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "agent"

    def ready(self):
        # Read the knowledge base once, at startup, into memory. A missing or
        # empty file is a deployment error and should stop the process here
        # rather than surface as a broken answer to a visitor.
        from agent.knowledge_base import load_knowledge_base

        load_knowledge_base()
