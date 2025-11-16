"""
xApp Lifecycle Manager
Manages deployment, lifecycle, and monitoring of xApps
"""

import asyncio
import logging
from typing import Dict, List
from datetime import datetime

from xapp_framework import XAppBase

logger = logging.getLogger(__name__)


class XAppManager:
    """Manages xApp lifecycle"""

    def __init__(self):
        self.xapps: Dict[str, XAppBase] = {}
        self.running = False

    async def deploy_xapp(self, xapp: XAppBase):
        """Deploy and start an xApp"""
        xapp_name = xapp.config.name

        if xapp_name in self.xapps:
            logger.warning(f"xApp {xapp_name} already deployed")
            return False

        logger.info(f"Deploying xApp: {xapp_name}")

        # Start xApp
        await xapp.start()

        # Register xApp
        self.xapps[xapp_name] = xapp

        logger.info(f"xApp {xapp_name} deployed successfully")
        return True

    async def undeploy_xapp(self, xapp_name: str):
        """Stop and remove an xApp"""
        if xapp_name not in self.xapps:
            logger.warning(f"xApp {xapp_name} not found")
            return False

        logger.info(f"Undeploying xApp: {xapp_name}")

        xapp = self.xapps[xapp_name]
        await xapp.stop()

        del self.xapps[xapp_name]

        logger.info(f"xApp {xapp_name} undeployed")
        return True

    def list_xapps(self) -> List[Dict]:
        """List all deployed xApps"""
        return [
            {
                "name": xapp.config.name,
                "version": xapp.config.version,
                "running": xapp.running,
                "metrics": xapp.metrics
            }
            for xapp in self.xapps.values()
        ]

    def get_xapp_status(self, xapp_name: str) -> Dict:
        """Get status of specific xApp"""
        if xapp_name not in self.xapps:
            return {"error": "xApp not found"}

        xapp = self.xapps[xapp_name]
        return {
            "name": xapp.config.name,
            "version": xapp.config.version,
            "description": xapp.config.description,
            "running": xapp.running,
            "metrics": xapp.metrics
        }
