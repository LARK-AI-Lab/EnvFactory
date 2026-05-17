
import httpx
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class StudySummary(BaseModel):
    nctId: str
    briefTitle: str = ""
    overallStatus: str = ""
    conditions: List[str] = Field(default_factory=list)
    interventions: List[str] = Field(default_factory=list)
    phases: List[str] = Field(default_factory=list)

class ClinicalTrialsScenario(BaseModel):
    base_url: str = "https://clinicaltrials.gov/api/v2"
    default_page_size: int = Field(default=10, ge=1, le=1000)
    cached_studies: Dict[str, Any] = Field(default_factory=dict)

Scenario_Schema = [StudySummary, ClinicalTrialsScenario]

# Section 2: Class
class ClinicalTrialsAPI:
    def __init__(self):
        self.base_url: str = ""
        self.default_page_size: int = 10
        self.cached_studies: Dict[str, Any] = {}

    def load_scenario(self, scenario: dict) -> None:
        model = ClinicalTrialsScenario(**scenario)
        self.base_url = model.base_url
        self.default_page_size = model.default_page_size
        self.cached_studies = model.cached_studies

    def save_scenario(self) -> dict:
        return {
            "base_url": self.base_url,
            "default_page_size": self.default_page_size,
            "cached_studies": self.cached_studies,
        }

    def _extract_study_summary(self, study: dict) -> dict:
        proto = study.get("protocolSection", {})
        id_mod = proto.get("identificationModule", {})
        status_mod = proto.get("statusModule", {})
        cond_mod = proto.get("conditionsModule", {})
        design_mod = proto.get("designModule", {})
        arms_mod = proto.get("armsInterventionsModule", {})
        interventions = [i.get("name", "") for i in arms_mod.get("interventions", [])]
        return {
            "nctId": id_mod.get("nctId", ""),
            "briefTitle": id_mod.get("briefTitle", ""),
            "overallStatus": status_mod.get("overallStatus", ""),
            "conditions": cond_mod.get("conditions", []),
            "interventions": interventions,
            "phases": design_mod.get("phases", []),
        }

    def list_studies(self, query: Optional[dict], page_size: int, page_token: Optional[str]) -> dict:
        params = {"format": "json", "pageSize": page_size}
        if query:
            if "term" in query:
                params["query.term"] = query["term"]
            for k, v in query.items():
                if k != "term":
                    params[f"query.{k}"] = v
        if page_token:
            params["pageToken"] = page_token
        resp = httpx.get(f"{self.base_url}/studies", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        studies = [self._extract_study_summary(s) for s in data.get("studies", [])]
        result = {"studies": studies, "totalCount": data.get("totalCount", 0)}
        if "nextPageToken" in data:
            result["nextPageToken"] = data["nextPageToken"]
        return result

    def get_study(self, nct_ids: str) -> dict:
        ids = [i.strip() for i in nct_ids.split(",")]
        studies = []
        for nct_id in ids:
            resp = httpx.get(f"{self.base_url}/studies/{nct_id}", params={"format": "json"}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            proto = data.get("protocolSection", {})
            id_mod = proto.get("identificationModule", {})
            record = {
                "nctId": id_mod.get("nctId", nct_id),
                "protocolSection": proto,
                "resultsSection": data.get("resultsSection", {}),
                "derivedSection": data.get("derivedSection", {}),
            }
            self.cached_studies[nct_id] = record
            studies.append(record)
        return {"studies": studies}

    def search_studies(self, condition: Optional[str], intervention: Optional[str],
                       location: Optional[str], status: Optional[str], page_size: int) -> dict:
        params = {"format": "json", "pageSize": page_size}
        if condition:
            params["query.cond"] = condition
        if intervention:
            params["query.intr"] = intervention
        if location:
            params["query.locn"] = location
        if status:
            params["filter.overallStatus"] = status.upper()
        resp = httpx.get(f"{self.base_url}/studies", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        studies = [self._extract_study_summary(s) for s in data.get("studies", [])]
        return {"studies": studies, "totalCount": data.get("totalCount", 0)}

    def get_results(self, nct_id: str) -> dict:
        resp = httpx.get(f"{self.base_url}/studies/{nct_id}", params={"format": "json"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("resultsSection", {})
        return {
            "nctId": nct_id,
            "outcomeMeasures": results.get("outcomeMeasuresModule", {}).get("outcomeMeasures", []),
            "adverseEvents": results.get("adverseEventsModule", {}).get("adverseEvents", []),
            "participantFlow": results.get("participantFlowModule", {}),
        }

    def analyze_trends(self, query: dict, group_by: str) -> dict:
        params = {"format": "json", "pageSize": 1000}
        if "term" in query:
            params["query.term"] = query["term"]
        for k, v in query.items():
            if k != "term":
                params[f"query.{k}"] = v
        all_studies = []
        page_token = None
        while True:
            if page_token:
                params["pageToken"] = page_token
            resp = httpx.get(f"{self.base_url}/studies", params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            all_studies.extend(data.get("studies", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        counts: Dict[str, int] = {}
        for study in all_studies:
            proto = study.get("protocolSection", {})
            if group_by == "phase":
                keys = proto.get("designModule", {}).get("phases", ["N/A"])
            elif group_by == "status":
                keys = [proto.get("statusModule", {}).get("overallStatus", "N/A")]
            elif group_by == "condition":
                keys = proto.get("conditionsModule", {}).get("conditions", ["N/A"])
            elif group_by == "sponsor":
                keys = [proto.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "N/A")]
            else:
                keys = ["N/A"]
            for key in keys:
                counts[key] = counts.get(key, 0) + 1
        buckets = [{"key": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]
        return {"group_by": group_by, "buckets": buckets, "totalCount": len(all_studies)}


# Section 3: MCP Tools
mcp = FastMCP(name="ClinicalTrialsGov")
api = ClinicalTrialsAPI()
api.load_scenario({})


@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the ClinicalTrials API.

    Args:
        scenario: Scenario dictionary matching ClinicalTrialsScenario schema.

    Returns:
        success_message: Confirmation message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        api.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e


@mcp.tool()
def save_scenario() -> dict:
    """
    Save current state as scenario dictionary.

    Returns:
        scenario: Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e


@mcp.tool()
def clinicaltrials_list_studies(
    query: Optional[dict] = None,
    pageSize: Optional[int] = None,
    pageToken: Optional[str] = None,
) -> dict:
    """
    Search and paginate through clinical studies using flexible query objects.

    Args:
        query: Query object (e.g., {"term": "diabetes"}) defining search filters.
        pageSize: Maximum number of studies to return (1-1000).
        pageToken: Pagination token from a previous call.

    Returns:
        studies: List of matching studies with brief metadata.
        nextPageToken: Token for the next page (absent when no more pages).
        totalCount: Total number of matching studies across all pages.
    """
    try:
        size = pageSize if pageSize is not None else api.default_page_size
        return api.list_studies(query, size, pageToken)
    except Exception as e:
        raise e


@mcp.tool()
def clinicaltrials_get_study(nctIds: str) -> dict:
    """
    Retrieve full protocol, results, and derived sections for one or more studies by NCT ID.

    Args:
        nctIds: Comma-separated list of ClinicalTrials.gov NCT IDs to fetch.

    Returns:
        studies: Detailed study records for each requested NCT ID, each containing
            nctId, protocolSection, resultsSection, derivedSection.
    """
    try:
        if not nctIds or not isinstance(nctIds, str):
            raise ValueError("nctIds must be a non-empty string")
        return api.get_study(nctIds)
    except Exception as e:
        raise e


@mcp.tool()
def clinicaltrials_search_studies(
    condition: Optional[str] = None,
    intervention: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    pageSize: Optional[int] = None,
) -> dict:
    """
    Quickly find studies using high-level filters for condition, intervention, location, and status.

    Args:
        condition: Disease or medical condition being studied.
        intervention: Drug, device, procedure, or behavioral intervention.
        location: Geographic location where recruitment occurs.
        status: Study recruitment or review status (e.g., recruiting, completed).
        pageSize: Maximum number of studies to return (1-1000).

    Returns:
        studies: Array of study summaries matching the provided filters.
        totalCount: Total number of matching studies across all pages.
    """
    try:
        size = pageSize if pageSize is not None else api.default_page_size
        return api.search_studies(condition, intervention, location, status, size)
    except Exception as e:
        raise e


@mcp.tool()
def clinicaltrials_get_results(nctId: str) -> dict:
    """
    Obtain reported results, outcome measures, adverse events, and participant flow for a study.

    Args:
        nctId: The unique ClinicalTrials.gov identifier (NCT ID) whose results are requested.

    Returns:
        nctId: The NCT ID of the study.
        outcomeMeasures: Primary and secondary outcome measures with analyzed data.
        adverseEvents: Adverse events reported by arm and severity.
        participantFlow: Participant progression numbers through trial phases.
    """
    try:
        if not nctId or not isinstance(nctId, str):
            raise ValueError("nctId must be a non-empty string")
        return api.get_results(nctId)
    except Exception as e:
        raise e


@mcp.tool()
def clinicaltrials_analyze_trends(query: dict, group_by: Optional[str] = None) -> dict:
    """
    Aggregate statistics on groups of trials by a chosen attribute.

    Args:
        query: Query object used to select the cohort of studies to analyze.
        group_by: Attribute to group studies by: "phase", "status", "condition", or "sponsor".

    Returns:
        group_by: The attribute used for grouping.
        buckets: Each bucket has key and count.
        totalCount: Total number of studies included in the analysis.
    """
    try:
        if not isinstance(query, dict):
            raise ValueError("query must be a dictionary")
        gb = group_by if group_by else "status"
        return api.analyze_trends(query, gb)
    except Exception as e:
        raise e


# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()
