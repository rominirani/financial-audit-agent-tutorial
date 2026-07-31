from google.antigravity import LocalAgentConfig
from google.antigravity.hooks import policy


def get_data_researcher_config(workspace):
    return LocalAgentConfig(
        system_instructions="""
        You are a Data Research Specialist. Your job is to query BigQuery
        for vendor transaction records. You have READ-ONLY access.

        Return results as a structured JSON summary with:
        - Total transactions found
        - List of vendor_id, invoice_num, amount, currency, tax_rate
        - Any data quality issues noted
        """,
        policies=[
            policy.deny_all(),
            policy.allow(
                "bigquery_query",
                when=lambda args: args.get("Query", "")
                .strip()
                .upper()
                .startswith("SELECT"),
                name="allow_bq_select_only",
            ),
        ],
        workspaces=[workspace],
    )
