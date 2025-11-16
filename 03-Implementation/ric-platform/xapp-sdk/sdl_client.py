"""
SDL (Shared Data Layer) Client for xApps
Provides Redis-based data sharing between xApps
"""

import redis
import json
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class SDLClient:
    """Shared Data Layer Client"""

    def __init__(self, host: str = "localhost", port: int = 6379, namespace: str = "xapp"):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=0,
            decode_responses=True
        )
        self.namespace = namespace

    def _key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.namespace}:{key}"

    def set(self, key: str, value: Dict):
        """Store data in SDL"""
        try:
            self.redis_client.set(
                self._key(key),
                json.dumps(value)
            )
            logger.debug(f"SDL SET: {key}")
            return True
        except Exception as e:
            logger.error(f"SDL SET failed: {e}")
            return False

    def get(self, key: str) -> Optional[Dict]:
        """Retrieve data from SDL"""
        try:
            value = self.redis_client.get(self._key(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"SDL GET failed: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete data from SDL"""
        try:
            self.redis_client.delete(self._key(key))
            logger.debug(f"SDL DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"SDL DELETE failed: {e}")
            return False

    def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching pattern"""
        try:
            keys = self.redis_client.keys(self._key(pattern))
            # Remove namespace prefix
            return [k.replace(f"{self.namespace}:", "") for k in keys]
        except Exception as e:
            logger.error(f"SDL KEYS failed: {e}")
            return []
