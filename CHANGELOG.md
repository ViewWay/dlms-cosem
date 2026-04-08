# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- SM2 stub replaced with real GB/T 32918-2016 implementation via `gmssl`
- Python certificate SM2 calls updated with `public_key` parameter
- Python: all TODOs resolved
- `test_hdlc/test_transport.py`: `FakeHdlcConnection` missing `timeout_config` attribute
- `test_server.py`: incorrect APDU tag bytes (0xE0→0xC1 for SET, 0xD0→0xC3 for ACTION)
- `test_server.py`: malformed GET request data (missing CosemAttribute bytes)
- `server.py`: `SetRequestHandler._handle_set_normal` used `apdu.value` instead of `apdu.data`
- `gmssl` dependency missing from `pyproject.toml`
- `test_connection_security.py`: `AssociationResult.REJECTED` → `REJECTED_PERMANENT`
- `test_hdlc_practical.py`: API adjustments — `FCS.calculate()`→`calculate_for()`, `information`→`payload`, `HDLC_FLAG` as int (0x7E)

### Added
- HDLC timeout/retry configuration (Green Book 8.4.5.6)
- A-XDR unknown tag tolerance (DontCare type for vendor-specific tags)
- SM2 real elliptic curve signing/verification
- `pytest-asyncio` and `hypothesis` to test dependencies
- **Connection security tests** (36 tests) — AARQ/AARE, RLRQ/RLRE, SecurityControlField, SM4 cipher, 5 auth mechanisms, state machine transitions
- **HDLC practical tests** (19 tests, total HDLC: 314) — FCS determinism, frame roundtrip, address validation, invalid frames, APDU extraction, HDLC flag position
- **MockTransport** — configurable mock transport for client/connection testing (inspired by pdlms)
- **Golden vector fixtures** — SAMPLE_AARE_ACCEPTED, system_title, encryption/auth keys
- **Test framework enhancements** — new conftest fixtures, mock transport with queue support

### Changed
- `sm2_sign()` now requires `public_key` parameter
- README test count badge updated to 6243
- MockTransport: _responses stores bytes not strings

---

## [1.0.0] - 2026-04-03

### Added
- **Complete DLMS/COSEM protocol stack** — sans-io architecture with full HDLC framing, A-XDR codec, and COSEM application layer
- **50+ COSEM IC classes**: Register, Clock, Profile Generic, Demand Register, Load Profile, Script Table, Activity Calendar, Event Log, Image Transfer, and many more
- **Multiple transport layers**: HDLC (serial), TCP, UDP, TLS, WebSocket, NB-IoT, LoRaWAN
- **Security suites**: HLS-ISM (AES-GCM), SM4-GMAC, SM4-GCM, AES-GCM-128/256
- **COSEM Server** — simulate meters for testing and development
- **Automation framework** — batch meter reading with parallel collection
- **WebSocket gateway** — browser/cloud integration via WS protocol
- **Key management system** — key generation, rotation, storage, and security suite management
- **SML parser** — Smart Message Language (EDIS) support
- **China GB/T extensions** — GB/T 17215 national standard support
- **CosemObjectFactory** — simplified meter object creation
- **Async client** — full async/await support with modern Python
- **CLI tools** — key management and meter utilities
- **Meter simulation** — complete virtual meter for testing
- **Comprehensive test suite** — 6066 tests with full coverage
- **Fuzzing harnesses** — property-based testing for protocol robustness
- **Performance optimizations** — optimized A-XDR and HDLC parsing

### Changed
- Modernized tooling: migrated to `uv`, updated CI to Node 24
- Reorganized project structure with clear module separation
- Improved error handling and diagnostic messages

### Security
- Implemented SM4 (Chinese national standard) cryptographic support
- Full HLS-ISM authentication with AES-GCM encryption
- Secure key rotation with configurable schedules

---

## [2026.1.0] - 2026-03-16

### Added
- Invoke-id tracking in DlmsClient requests
- Modernized CI/CD pipeline with uv

### Changed
- Migrated from setuptools-based workflow to uv
- Updated GitHub Actions to Node 24

---

## [24.1.0] - 2024-01-22

### Added
- DlmsConnectionSettings for handling special meter behaviour (#75)
- `use_rlrq_rlre` option on DlmsConnectionSetting (#80)

### Fixed
- Append on bytes in DataArray.to_bytes (#76)

---

## [23.1.0a1] - 2023-03-06

### Changed
- Composition of Transport and IO (#63) — decoupled transport from IO layer

---

## [21.3.1] - 2021-06-14

### Added
- DLMS data parser for use in GET.WITH_LIST (#48)

---

## [21.3.0] - 2021-06-08

### Added
- GET.WITH_LIST service (#45)

---

## [21.2.3] - 2021-04-22

### Added
- Timeout management from client level (#36)

### Fixed
- Better decryption error messages (#34)

---

## [21.2.2] - 2021-03-02

### Fixed
- Proper support for ACTION service (#29)

---

## [21.2.1] - 2021-02-18

### Fixed
- Always call `.shutdown()` on socket (#25)
- Fixed typo in AXdrParser (#24)
- Bumped cryptography dependency (#22)

---

## [21.2.0] - 2021-01-28

### Added
- SET service support (#19)
- Timezone parsing (#17)

---

## [21.1.2] - 2021-01-22

### Changed
- Improved TcpTransport (#15)

---

## [21.1.1] - 2021-01-13

### Added
- TCP transport (#14)
- Load profile parsing (#12)
- Selective access (#11)

---

## [21.1.0] - 2021-01-12

### Added
- Initial TCP transport support

---

## Earlier Releases (2018-2020)

### 2020-12
- Initial Association (#2)
- Security (#6)
- Segmented HDLC Information frames (#7)
- Service-specific GET block transfer (#10)
- Robustness improvements (#3)
- Documentation (#4)

### 2020-11
- HDLC implementation: unsegmented lifecycle
- HDLC state machine and frame handling

### 2019-03
- Data notification support
- UDP Wrapper/Message class
- X-ADR decoding support

### 2018-02
- Initial commit and project structure
- Basic DLMS package structure
