#!/usr/bin/env python3
"""Rename IC class files to C{n}_{ClassName}.py and update all imports.

Uses Blue Book CosemInterface enum values as class_ids.
Helper/support files and subtypes are NOT renamed.

Usage: python3 rename_ic_classes.py [--dry-run]
"""
import os
import re
import sys
import shutil

COSEM_DIR = 'dlms_cosem/cosem'
DRY_RUN = '--dry-run' in sys.argv

# === RENAME MAPPING ===
# old_filename -> (class_id, ClassName)
# class_id = CosemInterface enum value from Blue Book
# Only files that are actual IC interface classes, NOT helper/subtype files
RENAME_MAP = {
    # Core data/measurement IC classes
    'data.py': (1, 'Data'),
    'register.py': (2, 'Register'),
    'extended_register.py': (3, 'ExtendedRegister'),
    'demand_register.py': (4, 'DemandRegister'),
    'profile_generic.py': (5, 'ProfileGeneric'),
    'clock.py': (6, 'Clock'),
    'script_table.py': (7, 'ScriptTable'),
    'special_day_table.py': (8, 'SpecialDayTable'),
    'action_schedule.py': (9, 'ActionSchedule'),
    'association_sn.py': (10, 'AssociationSN'),
    'register_monitor.py': (13, 'RegisterMonitor'),
    'register_activation.py': (14, 'RegisterActivation'),
    'push_setup.py': (15, 'PushSetup'),
    'disconnect_control.py': (16, 'DisconnectControl'),
    'limiter.py': (17, 'Limiter'),
    'activity_calendar.py': (18, 'ActivityCalendar'),
    'sap_assignment.py': (53, 'SapAssignment'),
    'status_mapping.py': (55, 'StatusMapping'),
    'sensor_manager.py': (57, 'SensorManager'),
    'compact_data.py': (62, 'CompactData'),
    'security_setup.py': (29, 'SecuritySetup'),
    'credit.py': (66, 'Credit'),
    'charge.py': (67, 'Charge'),
    'arbitrator.py': (82, 'Arbitrator'),
    'mbus_diagnostic.py': (83, 'MbusDiagnostic'),
    'ntp_setup.py': (87, 'NTPSetup'),
    'load_profile_switch.py': (90, 'LoadProfileSwitch'),
    'lp_setup.py': (102, 'LocalPortSetup'),
    'rs485_setup.py': (23, 'RS485Setup'),
    'infrared_setup.py': (101, 'InfraredSetup'),
    'ipv4_setup.py': (40, 'IPv4Setup'),
    'ppp_setup.py': (45, 'PPPSetup'),
    'gprs_modem_setup.py': (27, 'GPRSSetup'),
    'modem_setup.py': (24, 'ModemSetup'),
    'modem_configuration.py': (48, 'ModemConfiguration'),
    'mbus_client.py': (26, 'MBusClient'),
    'parameter_monitor.py': (79, 'ParameterMonitor'),
    'power_quality_monitor.py': (110, 'PowerQualityMonitor'),
    'harmonic_monitor.py': (111, 'HarmonicMonitor'),
    'sag_swell_monitor.py': (112, 'SagSwellMonitor'),
    'comm_port_protection.py': (115, 'CommPortProtection'),
    'mac_address_setup.py': (117, 'MACAddressSetup'),
    'value_table.py': (119, 'ValueTable'),
    'iec_public_key.py': (32, 'IecPublicKey'),
    'cosem_data_protection.py': (33, 'CosemDataProtection'),
    'function_control.py': (78, 'FunctionControl'),
    'array_manager.py': (211, 'ArrayManager'),
    'smtp_setup.py': (28, 'SMTPSetup'),
    'max_demand_register.py': (205, 'MaxDemandRegister'),
    'event_log.py': (76, 'EventLog'),
    'account.py': (22, 'Account'),
    'auto_answer.py': (28, 'AutoAnswer'),
    'register_table.py': (61, 'RegisterTable'),
    # IC classes without CLASS_ID but known from Blue Book
    'nbp_setup.py': (106, 'NBIoTProfileSetup'),
    'lora_setup.py': (107, 'LoRaWANSetup'),
    'tcp_udp_setup.py': (39, 'TcpUdpSetup'),
    'zigbee_setup.py': (46, 'ZigBeeSetup'),
    'image_transfer.py': (35, 'ImageTransfer'),
    # association.py -> C11_AssociationLN (ASSOCIATION_LN=11)
    'association.py': (11, 'AssociationLN'),
}

# Build old_module -> new_module mapping
old_to_new = {}
for old, (cid, cname) in RENAME_MAP.items():
    old_to_new[old.replace('.py', '')] = f'C{cid}_{cname}'

def update_imports_in_file(filepath):
    """Update import statements in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    for old_mod, new_mod in old_to_new.items():
        # from dlms_cosem.cosem.{old} import
        content = re.sub(
            rf'from dlms_cosem\.cosem\.{re.escape(old_mod)}\b',
            f'from dlms_cosem.cosem.{new_mod}',
            content
        )
        # Relative import: from .{old} import
        content = re.sub(
            rf'from \.{re.escape(old_mod)}\b',
            f'from .{new_mod}',
            content
        )
        # dlms_cosem.cosem.{old}.ClassName (dotted attribute access)
        content = re.sub(
            rf'dlms_cosem\.cosem\.{re.escape(old_mod)}\b',
            f'dlms_cosem.cosem.{new_mod}',
            content
        )
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    # Step 1: Rename files
    print("=== Step 1: Renaming files ===")
    for old, (cid, cname) in sorted(RENAME_MAP.items(), key=lambda x: x[1][0]):
        old_path = os.path.join(COSEM_DIR, old)
        new_name = f'C{cid}_{cname}.py'
        new_path = os.path.join(COSEM_DIR, new_name)
        if not os.path.exists(old_path):
            print(f"  SKIP (not found): {old}")
            continue
        if os.path.exists(new_path):
            print(f"  SKIP (exists): {new_name}")
            continue
        if DRY_RUN:
            print(f"  RENAME: {old} -> {new_name}")
        else:
            shutil.move(old_path, new_path)
            print(f"  RENAMED: {old} -> {new_name}")
    
    # Step 2: Update imports in all .py files
    print("\n=== Step 2: Updating imports ===")
    updated = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if not f.endswith('.py'):
                continue
            filepath = os.path.join(root, f)
            try:
                if update_imports_in_file(filepath):
                    print(f"  Updated: {filepath}")
                    updated += 1
            except Exception as e:
                print(f"  ERROR: {filepath}: {e}")
    
    print(f"\n=== Done ===")
    print(f"  Files renamed: {len(RENAME_MAP)}")
    print(f"  Files with updated imports: {updated}")
    print(f"  Dry run: {DRY_RUN}")

if __name__ == '__main__':
    main()
