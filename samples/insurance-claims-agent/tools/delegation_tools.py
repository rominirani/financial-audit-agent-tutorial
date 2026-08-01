import json

_project_id = None
_workspace = None
_adjudicator_policies = None

_research_results = ""
_document_results = []
_expected_document_paths = set()

def configure(project_id: str, workspace: str, adjudicator_policies: list):
    """Initialize delegation tools state and reset accumulators."""
    global _project_id, _workspace, _adjudicator_policies
    global _research_results, _document_results, _expected_document_paths

    _project_id = project_id
    _workspace = workspace
    _adjudicator_policies = adjudicator_policies

    _research_results = ""
    _document_results = []
    _expected_document_paths = set()

def _truncate(text: str, max_length: int = 1000) -> str:
    """Helper to keep orchestrator context small."""
    if len(text) > max_length:
        return text[:max_length] + "... (truncated)"
    return text

async def delegate_to_claims_researcher(claim_type: str = 'all') -> str:
    """Delegate research tasks to the Claims Researcher subagent.
    
    This agent will query pending claims and get policy details.
    
    Args:
        claim_type: Optional filter for claim type.
    """
    import asyncio
    from google.antigravity import Agent
    from agents.claims_researcher import get_researcher_config

    global _research_results, _expected_document_paths

    config = get_researcher_config(_workspace, _project_id)
    
    async with Agent(config) as agent:
        response = await agent.chat(
            f"Research pending claims (type: {claim_type}). Query the claims, "
            "then fetch policy details for each claim. Finally, return a summary of the claims "
            "and a JSON list of claim IDs to process."
        )
        full_text = await response.text()
    
    _research_results = full_text
    
    # We don't have list_claim_documents at the orchestrator level, 
    # but the instructions say "returns concise summary with document paths list".
    # The Claims Researcher doesn't have document tools, it only has claim + policy tools.
    # Ah, the instructions say: 
    # "delegate_to_claims_researcher(claim_type='all') -> spawns Claims Researcher subagent, stores full results, returns concise summary with document paths list"
    # Wait, the analyzer has `list_claim_documents` AND `read_claim_document`.
    # Let me re-read the instructions: Document Analyzer has `list_claim_documents` + `read_claim_document`.
    # Maybe the Claims Researcher provides claim IDs, and the Document Analyzer does listing?
    # Or maybe the Researcher gives a list of claims. 
    # Actually, the user says "returns concise summary with document paths list" for the researcher? 
    # That implies the Researcher lists documents? But Document Analyzer has `list_claim_documents`.
    # I will assume the Researcher outputs claims, and maybe we can extract claim_ids.
    
    return _truncate(full_text)

async def delegate_to_document_analyzer(document_path: str = None) -> str:
    """Delegate document analysis to the Document Analyzer subagent.
    
    Call this for each claim ID or document path to read and extract information.
    
    Args:
        document_path: Path or Claim ID to analyze.
    """
    import asyncio
    from google.antigravity import Agent
    from agents.document_analyzer import get_analyzer_config

    global _document_results

    config = get_analyzer_config(_workspace, _project_id)
    
    async with Agent(config) as agent:
        response = await agent.chat(
            f"List documents for {document_path} and read them to extract claim data."
        )
        full_text = await response.text()
    
    _document_results.append(full_text)
    
    return f"Progress: {len(_document_results)} documents analyzed. {_truncate(full_text)}"

async def delegate_to_adjudicator(execution_id: str = 'CLAIMS-RUN') -> str:
    """Delegate the final validation and recording to the Adjudication Engine.
    
    Args:
        execution_id: Unique ID for this run.
    """
    from google.antigravity import Agent
    from agents.adjudication_engine import get_adjudicator_config
    
    # Simple guardrail
    if not _research_results:
        return "ERROR: You must call delegate_to_claims_researcher first."
    if not _document_results:
        return "ERROR: You must call delegate_to_document_analyzer at least once."

    config = get_adjudicator_config(_adjudicator_policies, _workspace, _project_id)
    
    payload = (
        f"Execution ID: {execution_id}\n\n"
        f"--- RESEARCH RESULTS ---\n{_research_results}\n\n"
        f"--- DOCUMENT ANALYSIS ---\n" + "\n".join(_document_results) + "\n\n"
        "Please validate the claims against coverage rules and fraud indicators, "
        "write the adjudication results, and produce a final report."
    )
    
    async with Agent(config) as agent:
        response = await agent.chat(payload)
        return await response.text()

DELEGATION_TOOLS = [
    delegate_to_claims_researcher,
    delegate_to_document_analyzer,
    delegate_to_adjudicator
]
