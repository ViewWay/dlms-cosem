# Design Principles

This document explains the core design principles behind `dlms-cosem` and why certain architectural decisions were made.

## Table of Contents

- [Sans-IO Architecture](#sans-io-architecture)
- [Separation of Concerns](#separation-of-concerns)
- [Type Safety](#type-safety)
- [Extensibility](#extensibility)
- [Performance](#performance)
- [Testability](#testability)
- [Compliance](#compliance)

---

## Sans-IO Architecture

### What is Sans-IO?

**Sans-IO** (IO-less) means the library provides protocol logic without implementing the actual network I/O. Instead, the library works with abstract input/output interfaces that users implement.

### Why Sans-IO?

1. **Flexibility**: Users can use any transport (serial, TCP, UDP, TLS, WebSocket, etc.)
2. **Testability**: Protocol logic can be tested without real network connections
3. **Compatibility**: Works with synchronous and asynchronous I/O
4. **Portability**: No dependency on specific networking libraries

### How it Works

```python
# The library provides protocol logic
from dlms_cosem.hdlc import HdlcConnection

# Users provide the IO implementation
class MyTcpIO:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port))

    def write(self, data: bytes):
        self.sock.send(data)

    def read(self) -> bytes:
        return self.sock.recv(1024)

# Combine them
io = MyTcpIO("192.168.1.100", 4059)
hdlc = HdlcConnection(io=io)
```

### Benefits

- ✅ Easy to mock for testing
- ✅ Supports custom transports (e.g., MQTT, SMS)
- ✅ Sync and async implementations coexist
- ✅ No network code in protocol layer

---

## Separation of Concerns

### Layered Architecture

The library is organized into clear layers:

```
┌─────────────────────────────────────────┐
│   Application Layer (Client/Server)    │  ← High-level API
├─────────────────────────────────────────┤
│      DLMS/COSEM Protocol Layer       │  ← APDU, Objects
├─────────────────────────────────────────┤
│         HDLC Framing Layer           │  ← Frame format, CRC
├─────────────────────────────────────────┤
│      Abstract I/O Layer              │  ← Write/Read interface
└─────────────────────────────────────────┘
```

### Why This Matters

1. **Independent Testing**: Each layer can be tested in isolation
2. **Easy Debugging**: Clear boundaries make issues easier to trace
3. **Reuse**: Lower layers can be used without higher layers
4. **Maintenance**: Changes in one layer don't break others

---

## Type Safety

### Type Hints

All public APIs use Python type hints:

```python
def get_attribute(self, attr_id: int) -> Any:
    """Get attribute value by ID.

    Args:
        attr_id: Attribute identifier (1-based)

    Returns:
        Attribute value

    Raises:
        AttributeError: If attribute ID is invalid
    """
```

### Why Type Safety?

1. **IDE Support**: Better autocomplete and error detection
2. **Refactoring**: Find all usages safely
3. **Documentation**: Types serve as inline documentation
4. **Early Errors**: Catch type errors before runtime

### Future: mypy --strict

We're working toward full `mypy --strict` compliance. This means:

- No `typing.Any` in public APIs
- All parameters and return values typed
- `TypedDict` instead of `dict` where appropriate
- `@overload` for complex function signatures

---

## Extensibility

### Factory Pattern

New COSEM IC classes can be added via the factory:

```python
from dlms_cosem.cosem.factory import CosemObjectFactory

class MyCustomIC(CosemObject):
    ...

CosemObjectFactory.register(999, MyCustomIC)

# Now automatically used by client
obj = factory.create_obis(Obis(1, 0, 0, 0, 0, 0))
```

### Custom Transports

Users can implement custom transports:

```python
from dlms_cosem.io import IOInterface

class MyCustomTransport(IOInterface):
    def write(self, data: bytes) -> None:
        ...

    def read(self) -> bytes:
        ...

# Use with any DLMS operation
conn = DlmsConnection(io=MyCustomTransport())
```

### Why Extensibility?

1. **Vendor Extensions**: Support vendor-specific IC classes
2. **Custom Protocols**: Implement proprietary wrappers
3. **Future-Proof**: Easy to add new features without breaking existing code

---

## Performance

### Optimization Goals

1. **Zero-Copy Parsing**: Minimize memory allocations
2. **Lazy Evaluation**: Only compute when needed
3. **Caching**: Cache expensive operations
4. **Benchmarked**: Maintain performance regression tests

### Current Optimizations

- **HdlcConnection**: Reuses buffers to avoid allocation
- **APDU Factory**: Caches parsed objects
- **Selective Access**: Only parse selected columns

### Future Work

- [ ] Rust/Cython extensions for hot paths
- [ ] Vectorized parsing with numpy
- [ ] Streaming for large data

---

## Testability

### Test Pyramid

```
            /\
           /E2E\      ← Integration tests (slow)
          /------\
         /        \
        /Unit Tests\   ← Fast, isolated
       /______________\
```

### Why Test-First?

1. **Regression Prevention**: Catch bugs early
2. **Documentation**: Tests serve as usage examples
3. **Refactoring Confidence**: Change code without fear
4. **Design Feedback**: Hard-to-test code = bad design

### Current Test Coverage

- **6066 unit tests** covering all core functionality
- **Property-based tests** with Hypothesis
- **Fuzzing tests** for robustness

---

## Compliance

### DLMS/COSEM Standards

We follow these standards strictly:

| Standard | Description |
|----------|-------------|
| Blue Book | COSEM Interface Classes |
| Green Book | Architecture and Protocols |
| Yellow Book | Security |
| White Book | HDLC Framing |

### Why Strict Compliance?

1. **Interoperability**: Works with any compliant meter
2. **Future-Proof**: Standards evolve predictably
3. **Credibility**: Professional-grade implementation
4. **Safety**: Security standards protect users

### Deviation Policy

- **Never** deviate from standard behavior
- **Extensions** use standard mechanisms (e.g., vendor-specific tags)
- **Deviations** (if discovered) are reported to DLMS UA

---

## Trade-offs

### Simplicity vs Flexibility

We prioritize **simplicity** for common use cases, with **flexibility** available for power users:

```python
# Simple: Read a register
voltage = client.get(Obis(1, 0, 32, 7, 0, 255))

# Flexible: Custom access with selective access
voltage = client.get(
    Obis(1, 0, 32, 7, 0, 255),
    access_selection=AccessDescriptor(...),
)
```

### Performance vs Safety

We prioritize **correctness** over raw speed:

```python
# Fast but unsafe: Direct access
value = obj.attributes[attr_id]

# Safer: Validated access
value = obj.get_attribute(attr_id)  # Raises on invalid ID
```

---

## Anti-Patterns We Avoid

1. **God Objects**: No single class does everything
2. **Global State**: No hidden mutable state
3. **Implicit Dependencies**: All dependencies explicit
4. **Premature Optimization**: Optimize after measuring
5. **Magic Numbers**: All constants named and documented

---

## Evolution

The design evolves based on:

1. **Real-World Usage**: Feedback from production deployments
2. **Standard Updates**: New DLMS/COSEM versions
3. **Community Contributions**: PRs and issues
4. **Performance Data**: Benchmark results

We follow **semantic versioning** to communicate breaking changes.

---

## Questions?

- [Architecture](ARCHITECTURE.md) — Detailed architecture
- [API Reference](api_reference.md) — Complete API docs
- [Contributing](contributing.md) — How to contribute
