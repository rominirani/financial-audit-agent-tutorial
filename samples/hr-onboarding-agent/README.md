# HR Onboarding Agent (Delegation Architecture)

This is the updated HR Onboarding Agent demonstrating the **Delegation Architecture** pattern with state accumulation and explicit guardrails.

## Architecture

This project implements a multi-agent system where a central **Orchestrator** delegates specialized tasks to subagents.

*   **Orchestrator (`gemini-3.6-flash`, location='global')**: The central brain. It has ZERO direct data tools. It uses only `DELEGATION_TOOLS` to command the subagents in a strict sequence.
*   **HR Researcher (`gemini-3.5-flash-lite`, location='global')**: Queries BigQuery for pending hires and department requirements.
*   **Document Verifier (`gemini-3.5-flash-lite`, location='global')**: Lists and reads PDF documents from Cloud Storage.
*   **Compliance Checker (`gemini-3.6-flash`, location='global')**: Evaluates the accumulated data and writes final compliance results. Protected by a guardrail ensuring all documents are verified before execution.

## Features

-   **State Accumulation**: Delegation tools handle the state in memory, keeping the Orchestrator's context window small via truncation (`_truncate()`).
-   **Model Tiering**: Expensive/capable models (`3.6-flash`) for complex reasoning (Orchestrator, Checker), and cheaper/faster models (`3.5-flash-lite`) for routine data tasks (Researcher, Verifier).
-   **Guardrails**: The `delegate_to_compliance_checker` tool refuses to run if there are unverified documents.
-   **Run Modes (Policies)**:
    -   `development`: All operations allowed.
    -   `staging`: Requires Human-in-the-Loop (HR Manager Approval) before writing compliance results.
    -   `production`: fully automated execution.

## Quick Start

1.  **Set up GCP Resources**:
    Ensure your project has the required BigQuery datasets (`hr_onboarding.new_hires`, `hr_onboarding.department_requirements`, `hr_onboarding.compliance_results`) and the GCS bucket (`{PROJECT_ID}-onboarding-documents`).

2.  **Generate Sample Data**:
    ```bash
    export PROJECT_ID=your-project-id
    python scripts/generate_sample_documents.py
    ```

3.  **Run the Agent**:
    ```bash
    # Dev mode (default)
    python main.py

    # Staging mode (Interactive approval)
    ENV=staging python main.py

    # Production mode
    ENV=production python main.py
    ```
