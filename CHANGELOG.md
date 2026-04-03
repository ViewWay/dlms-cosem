# Changelog

All notable changes to the dlms-cosem project will be documented in this file.

## [2026.1.0] - Unreleased

### Added — Iteration 5: Quality & Optimization
- Performance benchmarks for HDLC, AXDR, APDU, SM4, Profile Generic
- Fuzzing tests (4000+ random test cases) for parser robustness
- COSEM completeness verification tests
- Error handling audit documentation
- Supplementary test suites for all major modules (300+ new tests)
- API reference documentation
- Comprehensive README with architecture overview

### Added — Iteration 4: Server, Automation & Analytics
- COSEM server implementation
- Meter automation framework
- WebSocket gateway
- Data analytics module
- COSEM object factory

### Added — Iteration 3: Extensions & Protocols
- TLS transport layer
- Async client support
- Image Transfer IC class
- SML protocol support
- China GB extensions

### Added — Iteration 2: COSEM IC Classes
- 12 new COSEM interface classes
- Profile Generic enhancements
- Meter simulation support

### Added — Iteration 1: Core & Transport
- Blue Book COSEM IC classes
- NB-IoT and LoRaWAN transport
- HLS-ISM security suite
- Comprehensive key management system

## [24.1.0] - 2024

### Fixed
- Append on bytes in DataArray.to_bytes (#76)
- Missing imports in io.py (#104)
- use_rlrq_rlre on DlmsConnectionSetting (#80)
- Various small fixes (#110)

## [23.1.0a1] - 2023

### Changed
- Updated changelog, classifiers, and version

## Earlier versions

See git log for full history.
