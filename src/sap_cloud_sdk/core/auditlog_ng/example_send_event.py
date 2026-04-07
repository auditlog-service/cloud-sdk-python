#!/usr/bin/env python3
"""
Example: Send audit events to an OTLP endpoint.

Demonstrates sending events in both binary protobuf and JSON formats.

Prerequisites:
    - Update ENDPOINT, DEPLOYMENT_ID, NAMESPACE, TENANT_ID, and certificate paths
    - Ensure the OTLP endpoint is running and accessible
    - source ./setup-python-environment.sh
    - pip install -r requirements-client.txt

Usage:
  python3 example_send_event.py
"""

import os
import sys
import base64
import json
from datetime import datetime, timezone
from pathlib import Path

# Ensure the project src/ directory is on sys.path so that
# `sap_cloud_sdk` can be imported when running this script directly
# (e.g. `python3 example_send_event.py` from the auditlog_ng folder).
_SRC_DIR = str(Path(__file__).resolve().parents[3])  # …/src
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from google.protobuf.json_format import MessageToDict, MessageToJson

from sap_cloud_sdk.core.auditlog_ng import create_client, AuditClient, AuditLogNGConfig

# Import generated protobuf messages
from sap_cloud_sdk.core.auditlog_ng.gen.sap.auditlog.auditevent.v2 import auditevent_pb2 as pb

# Configuration - update these for your environment
# Example: "your-region.als.services.cloud.sap:443"
ENDPOINT = "<your-otlp-endpoint:443>"

# Use your actual deployment ID, namespace, and tenant ID for real testing
DEPLOYMENT_ID = "<your-deployment-id>"
NAMESPACE = "<your-namespace>"
TENANT_ID = "<your-tenant-id>"

# Paths to mTLS certificates (PEM format)
CERT_FILE = "<path-to-your-client-cert.pem>"
KEY_FILE = "<path-to-your-client-key.pem>"


def print_otlp_debug(event, event_type: str, format_type: str = "protobuf-binary"):
    """Print debug information about the OTLP event being sent."""
    import uuid

    print("\n" + "=" * 60)
    print(f"OTLP EVENT DEBUG INFO ({format_type.upper()})")
    print("=" * 60)

    # 1. Event as JSON (readable format)
    print("\n[Proto Event as JSON]")
    event_dict = MessageToDict(event, preserving_proto_field_name=False)
    print(json.dumps(event_dict, indent=2))

    # 2. Format-specific body representation
    if format_type == "json":
        # JSON format - show the JSON string that will be sent
        json_body = MessageToJson(event, preserving_proto_field_name=False)
        auditlog_mime_type = "application/json"
        print("\n[OTLP LogRecord Body - JSON]")
        print("  Type: string_value")
        print("  Content:")
        print(f"    {json_body}")
    else:
        # Binary format - show serialized bytes
        serialized = event.SerializeToString()
        auditlog_mime_type = "application/protobuf"
        print("\n[OTLP LogRecord Body - Binary]")
        print("  Type: bytes_value")
        print(f"  Size: {len(serialized)} bytes")
        print(f"  Base64: {base64.b64encode(serialized).decode()}")

    #3. OTLP Resource attributes that will be set
    print("\n[OTLP Resource Attributes]")
    print(f"  sap.ucl.deployment_id: {DEPLOYMENT_ID}")
    print(f"  sap.ucl.system_namespace: {NAMESPACE}")

    # 4. OTLP LogRecord attributes that will be set
    event_id = str(uuid.uuid4())
    print("\n[OTLP LogRecord Attributes]")
    print(f"  event_name: {event_type}")
    print(f"  cloudevents.event_id: {event_id}")
    print(f"  sap.tenancy.tenant_id: {TENANT_ID}")
    print(f"  sap.auditlogging.mime_type: {auditlog_mime_type}")

    print("\n" + "=" * 60)


def create_sample_event():
    """Create a sample DataAccess event for testing."""
    event = pb.DataAccess()

    # Set common fields
    event.common.timestamp.FromDatetime(datetime.now(timezone.utc))
    event.common.user_initiator_id = "demo-user@example.com"
    event.common.tenant_id = TENANT_ID
    event.common.app_id = "python-audit-sdk-sample"

    # Set event-specific fields
    event.channel_type = "API"
    event.channel_id = "rest-api-v1"
    event.object_type = "customer-record"
    event.object_id = "cust-12345"
    event.attribute = "email"

    return event


def example_insecure():
    """Example: Insecure connection (local testing)."""
    print("Example: Insecure connection (local testing)")
    print("-" * 40)

    with create_client(
        endpoint="localhost:4317",
        deployment_id=DEPLOYMENT_ID,
        namespace=NAMESPACE,
        insecure=True,
    ) as client:
        event = create_sample_event()

        # Send in binary format
        event_id = client.send(event, "DataAccess")
        print(f"  ✓ Sent (binary): {event_id}")

        # Send in JSON format
        event_id = client.send_json(event, "DataAccess")
        print(f"  ✓ Sent (JSON):   {event_id}")


def example_mtls_binary():
    """Example: mTLS connection with binary protobuf format."""
    print("\n" + "=" * 60)
    print("Example: mTLS + Binary Protobuf Format")
    print("=" * 60)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Deployment ID: {DEPLOYMENT_ID}")
    print(f"Namespace: {NAMESPACE}")
    print(f"Tenant ID: {TENANT_ID}")

    # Check certificate files exist
    print("\n[0] Checking certificate files...")
    cert_exists = os.path.exists(CERT_FILE)
    key_exists = os.path.exists(KEY_FILE)

    if cert_exists:
        print(f"    ✓ Cert file exists: {CERT_FILE}")
    else:
        print(f"    ✗ Cert file NOT FOUND: {CERT_FILE}")
    if key_exists:
        print(f"    ✓ Key file exists: {KEY_FILE}")
    else:
        print(f"    ✗ Key file NOT FOUND: {KEY_FILE}")

    if not (cert_exists and key_exists):
        print("\n    ⚠️  Skipping mTLS example - certificates not found")
        print("    Update CERT_FILE and KEY_FILE paths for your environment")
        return None

    # 1. Create protobuf event
    print("\n[1] Creating DataAccess event...")
    event = create_sample_event()

    print(f"    Event: {event.DESCRIPTOR.name}")
    print(f"    User:  {event.common.user_initiator_id}")
    print(f"    Object: {event.object_type} ({event.object_id})")

    # Print OTLP debug info
    print_otlp_debug(event, "DataAccess", format_type="protobuf-binary")

    # 2. Create client and send in BINARY format
    print("\n[2] Sending via OTLP (Binary Protobuf)...")
    client = create_client(
        endpoint=ENDPOINT,
        deployment_id=DEPLOYMENT_ID,
        namespace=NAMESPACE,
        cert_file=CERT_FILE,
        key_file=KEY_FILE,
        insecure=False,
    )

    try:
        event_id = client.send(event, "DataAccess", format="protobuf-binary")
        print(f"    ✓ Sent (binary)! Event ID: {event_id}")
        return event_id
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None
    finally:
        client.close()


def example_mtls_json():
    """Example: mTLS connection with JSON format."""
    print("\n" + "=" * 60)
    print("Example: mTLS + JSON Format")
    print("=" * 60)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Deployment ID: {DEPLOYMENT_ID}")
    print(f"Namespace: {NAMESPACE}")
    print(f"Tenant ID: {TENANT_ID}")

    # Check certificate files exist
    cert_exists = os.path.exists(CERT_FILE)
    key_exists = os.path.exists(KEY_FILE)

    if not (cert_exists and key_exists):
        print("\n    ⚠️  Skipping - certificates not found")
        return None

    # 1. Create protobuf event
    print("\n[1] Creating DataAccess event...")
    event = create_sample_event()

    print(f"    Event: {event.DESCRIPTOR.name}")
    print(f"    User:  {event.common.user_initiator_id}")
    print(f"    Object: {event.object_type} ({event.object_id})")

    # Print OTLP debug info for JSON
    print_otlp_debug(event, "DataAccess", format_type="json")

    # 2. Create client and send in JSON format
    print("\n[2] Sending via OTLP (JSON)...")
    client = create_client(
        endpoint=ENDPOINT,
        deployment_id=DEPLOYMENT_ID,
        namespace=NAMESPACE,
        cert_file=CERT_FILE,
        key_file=KEY_FILE,
        insecure=False,
    )

    try:
        event_id = client.send_json(event, "DataAccess")
        print(f"    ✓ Sent (JSON)! Event ID: {event_id}")
        return event_id
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None
    finally:
        client.close()


def example_mtls():
    """Example: mTLS connection - both binary and JSON formats."""
    print("\n" + "=" * 60)
    print("Example: mTLS connection (both formats)")
    print("=" * 60)

    # Send in binary format
    binary_id = example_mtls_binary()

    # Send in JSON format
    json_id = example_mtls_json()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if binary_id:
        print(f"  ✓ Binary event ID: {binary_id}")
    else:
        print("  ✗ Binary event: FAILED")
    if json_id:
        print(f"  ✓ JSON event ID:   {json_id}")
    else:
        print("  ✗ JSON event: FAILED")


def main():
    print("=" * 60)
    print("Audit Log Client Examples")
    print("=" * 60)

    # Run examples
    # example_insecure()  # Uncomment for local testing
    example_mtls()

    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
