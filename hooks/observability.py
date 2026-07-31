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

# Agent identity — set this to match your orchestrator config name
AGENT_NAME = "audit-orchestrator"

# Active session span (parent for all tool spans)
_active_span = None
# Tool call counter for ordering
_tool_call_count = 0


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
    global _active_span, _tool_call_count
    _tool_call_count = 0

    print(f"\n{'='*60}")
    print(f"🔍 FINANCIAL AUDIT SESSION STARTED — {datetime.now(UTC).isoformat()}Z")
    print(f"{'='*60}\n")

    _log("INFO", "Audit session started", event="SESSION_START", agent=AGENT_NAME)

    if CLOUD_TRACE_ENABLED:
        # Start the root session span. Tool spans will be explicitly
        # parented under this span using set_span_in_context().
        _active_span = _tracer.start_span("financial-audit-session")
        _active_span.set_attribute("audit.type", "vendor-reconciliation")
        _active_span.set_attribute("agent.name", AGENT_NAME)


@post_tool_call
async def audit_tool_invocation(data: types.ToolResult):
    """Log every tool call for compliance and create a child trace span.

    The @post_tool_call hook receives a types.ToolResult object after
    each tool execution completes. We create a child span explicitly
    parented under the session span so it appears nested in Cloud Trace.
    """
    global _tool_call_count
    _tool_call_count += 1

    tool_name = data.name if hasattr(data, 'name') else str(data)

    _log("INFO", f"Tool invoked: {tool_name}",
         event="TOOL_INVOCATION",
         agent=AGENT_NAME,
         tool=tool_name,
         tool_call_index=_tool_call_count)

    if CLOUD_TRACE_ENABLED and _tracer and _active_span:
        # Create a child span explicitly parented under the session span.
        # set_span_in_context() tells the tracer to use _active_span as
        # the parent, so the tool span appears nested in the trace view.
        parent_ctx = trace.set_span_in_context(_active_span)
        tool_span = _tracer.start_span(
            f"tool:{tool_name}",
            context=parent_ctx,
        )
        tool_span.set_attribute("tool.name", tool_name)
        tool_span.set_attribute("tool.call_index", _tool_call_count)
        tool_span.set_attribute("agent.name", AGENT_NAME)
        # End the span immediately — this records it with a non-zero
        # duration (start → end) in the trace timeline.
        tool_span.end()


@on_session_end
async def audit_session_end():
    global _active_span
    print(f"\n{'='*60}")
    print(f"✅ FINANCIAL AUDIT SESSION COMPLETED — {datetime.now(UTC).isoformat()}Z")
    print(f"{'='*60}\n")

    _log("INFO", "Audit session completed",
         event="SESSION_END",
         agent=AGENT_NAME,
         total_tool_calls=_tool_call_count)

    if CLOUD_TRACE_ENABLED and _active_span:
        _active_span.set_attribute("audit.total_tool_calls", _tool_call_count)
        _active_span.end()
        _active_span = None


AUDIT_HOOKS = [audit_session_start, audit_tool_invocation, audit_session_end]
