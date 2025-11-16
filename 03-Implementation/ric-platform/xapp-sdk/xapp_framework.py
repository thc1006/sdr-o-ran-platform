"""
xApp Development Framework SDK
Provides base class and utilities for xApp development
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class XAppConfig:
    """xApp Configuration"""
    name: str
    version: str
    description: str
    e2_subscriptions: List[Dict]
    sdl_namespace: str
    metrics_enabled: bool = True


class XAppBase(ABC):
    """Base class for all xApps"""

    def __init__(self, config: XAppConfig):
        self.config = config
        self.logger = logging.getLogger(f"xapp.{config.name}")
        self.running = False
        self.metrics = {}

    @abstractmethod
    async def init(self):
        """Initialize xApp (override this)"""
        pass

    @abstractmethod
    async def handle_indication(self, indication):
        """Handle E2 indication (override this)"""
        pass

    async def start(self):
        """Start xApp"""
        self.logger.info(f"Starting xApp: {self.config.name} v{self.config.version}")
        await self.init()
        self.running = True

    async def stop(self):
        """Stop xApp"""
        self.logger.info(f"Stopping xApp: {self.config.name}")
        self.running = False

    def update_metric(self, name: str, value: float):
        """Update xApp metric"""
        self.metrics[name] = {
            "value": value,
            "timestamp": datetime.now()
        }
