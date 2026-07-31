from google.antigravity.hooks import on_session_start, post_tool_call, on_session_end
from google.antigravity import types
import json
import os
from datetime import datetime, UTC

# --- Cloud Logging Integration ---
try:
    from google.cloud import logging as cloud_logging
    _logging_client = cloud_logging.Client()
    _logger = _logging_client.logger("financial-audit-agent")
    CLOUD_LOGGING_ENABLED = True
except ImportError:
    CLOUD_LOGGING_ENABLED = False
    print("⚠️  google-cloud-logging not installed. Using console-only logging.")

# --- Cloud Trace Integration ---
try:
    from opentelemetry import trace
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider()
    processor = BatchSpanProcessor(CloudTraceSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("financial-audit-agent")
    CLOUD_TRACE_ENABLED = True
except ImportError:
    CLOUD_TRACE_ENABLED = False
    _tracer = None
    print("⚠️  opentelemetry/cloud-trace not installed. Using console-only tracing.")

# Active trace span for the current session
_active_span = None


def _log(severity, message, **kwargs):
    """Log to both console and Cloud Logging."""
    log_entry = {
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "severity": severity,
        "message": message,
        **kwargs,
    }
    print(f"[AUDIT] {json.dumps(log_entry)}")

    if CLOUD_LOGGING_ENABLED:
        _logger.log_struct(log_entry, severity=severity)


@on_session_start
async def audit_session_start():
    global _active_span
    print(f"\n{'='*60}")
    print(f"🔍 FINANCIAL AUDIT SESSION STARTED — {datetime.now(UTC).isoformat()}Z")
    print(f"{'='*60}\n")

    _log("INFO", "Audit session started", event="SESSION_START")

    if CLOUD_TRACE_ENABLED:
        _active_span = _tracer.start_span("financial-audit-session")
        _active_span.set_attribute("audit.type", "vendor-reconciliation")
        _active_span.set_attribute("audit.quarter", "Q3")


@post_tool_call
async def audit_tool_invocation(data: types.ToolResult):
    """Log every tool call for compliance and create a trace span.

    The @post_tool_call hook receives a types.ToolResult object after
    each tool execution completes. We extract the tool name and log it.
    """
    tool_name = data.name if hasattr(data, 'name') else str(data)
    agent_id = str(data.agent_id) if hasattr(data, 'agent_id') else "unknown"

    _log("INFO", f"Tool invoked: {tool_name}",
         event="TOOL_INVOCATION",
         agent_id=agent_id,
         tool=tool_name)

    if CLOUD_TRACE_ENABLED and _tracer:
        with _tracer.start_as_current_span(f"tool:{tool_name}") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("agent.id", agent_id)


@on_session_end
async def audit_session_end():
    global _active_span
    print(f"\n{'='*60}")
    print(f"✅ FINANCIAL AUDIT SESSION COMPLETED — {datetime.now(UTC).isoformat()}Z")
    print(f"{'='*60}\n")

    _log("INFO", "Audit session completed", event="SESSION_END")

    if CLOUD_TRACE_ENABLED and _active_span:
        _active_span.end()
        _active_span = None


AUDIT_HOOKS = [audit_session_start, audit_tool_invocation, audit_session_end]
