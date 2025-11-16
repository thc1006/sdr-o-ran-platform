# xApp SDK Quick Reference

## Installation

```bash
pip install -r requirements.txt
redis-server --daemonize yes
```

## Create an xApp

```python
from xapp_sdk import XAppBase, XAppConfig, SDLClient

class MyXApp(XAppBase):
    def __init__(self):
        config = XAppConfig(
            name="my-xapp",
            version="1.0.0",
            description="Description",
            e2_subscriptions=[{"ran_function_id": 1}],
            sdl_namespace="my-xapp"
        )
        super().__init__(config)
        self.sdl = SDLClient(namespace=config.sdl_namespace)

    async def init(self):
        self.logger.info("Initializing")

    async def handle_indication(self, indication):
        self.logger.info(f"Received: {indication}")
```

## Run xApp

```python
import asyncio

async def main():
    xapp = MyXApp()
    await xapp.start()
    try:
        while xapp.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await xapp.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## SDL Operations

```python
# Store data
sdl.set("key", {"value": 42})

# Retrieve data
data = sdl.get("key")

# Delete data
sdl.delete("key")

# List keys
keys = sdl.list_keys("pattern:*")
```

## Update Metrics

```python
self.update_metric("metric_name", value)
```

## xApp Manager

```python
from xapp_sdk import XAppManager

manager = XAppManager()
await manager.deploy_xapp(my_xapp)
xapps = manager.list_xapps()
status = manager.get_xapp_status("my-xapp")
await manager.undeploy_xapp("my-xapp")
```

## Run Tests

```bash
pytest tests/ -v
pytest --cov=xapp_sdk --cov=xapps tests/
```

## Docker

```bash
docker build -t my-xapp:1.0.0 .
docker-compose up -d
```

## Kubernetes

```bash
kubectl apply -f k8s/
kubectl get pods -n ric-platform
kubectl logs -f deployment/my-xapp -n ric-platform
```

## Key Files

- `xapp-sdk/xapp_framework.py` - Base classes
- `xapp-sdk/sdl_client.py` - SDL client
- `xapp-sdk/xapp_manager.py` - Lifecycle manager
- `xapps/qos_optimizer_xapp.py` - QoS example
- `xapps/handover_manager_xapp.py` - Handover example

## Documentation

- `docs/XAPP_DEVELOPMENT_GUIDE.md` - Complete tutorial
- `docs/SDK_API_REFERENCE.md` - Full API docs
- `docs/EXAMPLE_XAPPS.md` - Example walkthroughs
- `docs/DEPLOYMENT_GUIDE.md` - Deployment guide

## Common Patterns

### Error Handling
```python
try:
    await self._process()
except Exception as e:
    self.logger.error(f"Error: {e}")
    self.update_metric("errors", 1)
```

### State Persistence
```python
async def init(self):
    self.state = self.sdl.get("state") or {}

async def handle_indication(self, indication):
    # Update state
    self.state["count"] = self.state.get("count", 0) + 1
    self.sdl.set("state", self.state)
```

### Threshold-based Logic
```python
if value < THRESHOLD:
    await self._take_action()
    self.update_metric("actions_taken", 1)
```

## Performance Tips

- Keep `handle_indication()` fast (< 10ms)
- Use SDL for state, not local variables
- Batch SDL operations when possible
- Use async/await properly
- Add metrics for monitoring

## Troubleshooting

```bash
# Check Redis
redis-cli ping

# View logs with verbose output
python xapps/my_xapp.py 2>&1 | tee xapp.log

# Test specific component
pytest tests/test_my_xapp.py -v -s
```
