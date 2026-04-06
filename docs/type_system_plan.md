# Type System Enhancement Plan

## Current Status
- mypy configured (pyproject.toml + mypy.ini)
- Initial mypy run: 433 type errors
- Configuration: Gradual (not strict mode)

## Strategy: Phased Fixes

### Phase 1: High-Impact Modules (2 days)
Priority: Modules with public API
- dlms_cosem/client.py
- dlms_cosem/connection.py
- dlms_cosem/server.py
- dlms_cosem/async_client.py

### Phase 2: Type Foundation (2 days)
- Fix `from typing import *` imports
- Replace `dict` with `TypedDict` where appropriate
- Add `Protocol` for IO interfaces

### Phase 3: Protocol Layers (2 days)
- dlms_cosem/protocol/ (xdlms, acse)
- dlms_cosem/hdlc/ (connection, frames, state)

### Phase 4: Remaining Modules (2 days)
- Fix remaining type errors
- Enable stricter mypy checks gradually

## Estimated Total: 8 days

## Progress
- [ ] Phase 1: High-Impact Modules
- [ ] Phase 2: Type Foundation
- [ ] Phase 3: Protocol Layers
- [ ] Phase 4: Remaining Modules
- [ ] Final: Enable mypy --strict
