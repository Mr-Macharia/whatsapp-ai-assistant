from typing import Optional

from agno.tools.scheduler import SchedulerTools
from app.db import whatsapp_db


class WhatsAppSchedulerTools(SchedulerTools):
    """SchedulerTools that forces all schedules through our WhatsApp-aware endpoint.

    The LLM often overrides the default_endpoint by explicitly passing
    endpoint="/agents/{id}/runs". This subclass ignores whatever endpoint
    the LLM provides and always uses /scheduled-run/{agent_id} so that
    the agent's response gets delivered to WhatsApp.
    """

    def __init__(self, agent_id: str, **kwargs):
        self._forced_endpoint = f"/scheduled-run/{agent_id}"
        super().__init__(
            db=whatsapp_db,
            default_endpoint=self._forced_endpoint,
            default_timezone="Africa/Nairobi",
            **kwargs,
        )

    def create_schedule(self, name, cron, description=None, endpoint=None,
                        method=None, payload=None, timezone=None):
        # Always force our endpoint, ignore whatever the LLM passes
        return super().create_schedule(
            name=name, cron=cron, description=description,
            endpoint=self._forced_endpoint, method=method,
            payload=payload, timezone=timezone,
        )

    async def acreate_schedule(self, name, cron, description=None, endpoint=None,
                               method=None, payload=None, timezone=None):
        # Always force our endpoint, ignore whatever the LLM passes
        return await super().acreate_schedule(
            name=name, cron=cron, description=description,
            endpoint=self._forced_endpoint, method=method,
            payload=payload, timezone=timezone,
        )


gichogu_scheduler = WhatsAppSchedulerTools(agent_id="gichogu-assistant")
rachael_scheduler = WhatsAppSchedulerTools(agent_id="rachael-assistant")