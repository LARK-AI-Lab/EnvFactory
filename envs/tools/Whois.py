
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema

class DomainRecord(BaseModel):
    """Represents a domain WHOIS record."""
    domainName: str = Field(..., description="Canonical domain name")
    registrar: str = Field(..., description="Accredited registrar")
    creationDate: str = Field(..., description="ISO 8601 creation timestamp")
    updatedDate: str = Field(..., description="ISO 8601 last update timestamp")
    expirationDate: str = Field(..., description="ISO 8601 expiration timestamp")
    nameServers: List[str] = Field(default=[], description="Authoritative name servers")
    status: List[str] = Field(default=[], description="Registry status codes")
    registrant: Dict[str, Any] = Field(default={}, description="Registrant contact info")

class IpRecord(BaseModel):
    """Represents an IP WHOIS allocation record."""
    ip: str = Field(..., description="Queried IP address")
    range: str = Field(..., description="Allocated IP range")
    netName: str = Field(..., description="Registry network label")
    organization: str = Field(..., description="Organization holding the allocation")
    country: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    cidr: str = Field(..., description="CIDR notation of allocated prefix")
    updatedDate: str = Field(..., description="ISO 8601 last update timestamp")

class AsRecord(BaseModel):
    """Represents an autonomous system WHOIS record."""
    asn: str = Field(..., description="Autonomous system number")
    name: str = Field(..., description="Short AS name")
    organization: str = Field(..., description="Organization owning the AS")
    country: str = Field(..., description="ISO 3166-1 alpha-2 country code")
    routes: List[str] = Field(default=[], description="IP prefixes announced by this AS")
    updatedDate: str = Field(..., description="ISO 8601 last update timestamp")

class TldRecord(BaseModel):
    """Represents a TLD WHOIS record."""
    tld: str = Field(..., description="Canonical TLD suffix")
    sponsor: str = Field(..., description="TLD registry operator")
    whoisServer: str = Field(..., description="Authoritative WHOIS server hostname")
    status: str = Field(..., description="Registry status of the TLD")
    createdDate: str = Field(..., description="ISO 8601 delegation timestamp")
    updatedDate: str = Field(..., description="ISO 8601 last update timestamp")

class WhoisScenario(BaseModel):
    """Main scenario model for WHOIS lookup service."""
    current_time: str = Field(default="", description="Current timestamp in ISO 8601 format")
    domains: Dict[str, Any] = Field(default={}, description="Domain WHOIS records keyed by domain name")
    ips: Dict[str, Any] = Field(default={}, description="IP WHOIS records keyed by IP address")
    asns: Dict[str, Any] = Field(default={}, description="AS WHOIS records keyed by ASN")
    tlds: Dict[str, Any] = Field(default={
        "com": {
            "tld": "com", "sponsor": "VeriSign Global Registry Services",
            "whoisServer": "whois.verisign-grs.com", "status": "active",
            "createdDate": "1985-01-01T00:00:00", "updatedDate": "2023-10-01T00:00:00"
        },
        "org": {
            "tld": "org", "sponsor": "Public Interest Registry",
            "whoisServer": "whois.pir.org", "status": "active",
            "createdDate": "1985-01-01T00:00:00", "updatedDate": "2023-09-15T00:00:00"
        },
        "net": {
            "tld": "net", "sponsor": "VeriSign Global Registry Services",
            "whoisServer": "whois.verisign-grs.com", "status": "active",
            "createdDate": "1985-01-01T00:00:00", "updatedDate": "2023-10-01T00:00:00"
        },
        "io": {
            "tld": "io", "sponsor": "Internet Computer Bureau Ltd",
            "whoisServer": "whois.nic.io", "status": "active",
            "createdDate": "1997-09-26T00:00:00", "updatedDate": "2023-08-20T00:00:00"
        },
        "co": {
            "tld": "co", "sponsor": ".CO Internet S.A.S.",
            "whoisServer": "whois.nic.co", "status": "active",
            "createdDate": "1991-01-01T00:00:00", "updatedDate": "2023-07-10T00:00:00"
        },
        "uk": {
            "tld": "uk", "sponsor": "Nominet UK",
            "whoisServer": "whois.nic.uk", "status": "active",
            "createdDate": "1985-07-24T00:00:00", "updatedDate": "2023-11-01T00:00:00"
        },
        "de": {
            "tld": "de", "sponsor": "DENIC eG",
            "whoisServer": "whois.denic.de", "status": "active",
            "createdDate": "1986-11-05T00:00:00", "updatedDate": "2023-10-15T00:00:00"
        },
        "fr": {
            "tld": "fr", "sponsor": "AFNIC",
            "whoisServer": "whois.nic.fr", "status": "active",
            "createdDate": "1986-09-01T00:00:00", "updatedDate": "2023-09-01T00:00:00"
        },
        "jp": {
            "tld": "jp", "sponsor": "Japan Registry Services Co., Ltd.",
            "whoisServer": "whois.jprs.jp", "status": "active",
            "createdDate": "1986-08-05T00:00:00", "updatedDate": "2023-08-01T00:00:00"
        },
        "au": {
            "tld": "au", "sponsor": "auDA",
            "whoisServer": "whois.auda.org.au", "status": "active",
            "createdDate": "1986-03-05T00:00:00", "updatedDate": "2023-06-01T00:00:00"
        },
        "ca": {
            "tld": "ca", "sponsor": "Canadian Internet Registration Authority",
            "whoisServer": "whois.cira.ca", "status": "active",
            "createdDate": "1987-05-14T00:00:00", "updatedDate": "2023-05-01T00:00:00"
        },
        "info": {
            "tld": "info", "sponsor": "Afilias Limited",
            "whoisServer": "whois.afilias.net", "status": "active",
            "createdDate": "2001-06-26T00:00:00", "updatedDate": "2023-04-01T00:00:00"
        },
        "biz": {
            "tld": "biz", "sponsor": "Neustar, Inc.",
            "whoisServer": "whois.biz", "status": "active",
            "createdDate": "2001-06-26T00:00:00", "updatedDate": "2023-03-01T00:00:00"
        },
        "edu": {
            "tld": "edu", "sponsor": "EDUCAUSE",
            "whoisServer": "whois.educause.edu", "status": "active",
            "createdDate": "1985-01-01T00:00:00", "updatedDate": "2023-02-01T00:00:00"
        },
        "gov": {
            "tld": "gov", "sponsor": "General Services Administration",
            "whoisServer": "whois.dotgov.gov", "status": "active",
            "createdDate": "1985-01-01T00:00:00", "updatedDate": "2023-01-01T00:00:00"
        },
    }, description="TLD WHOIS records keyed by TLD name")

Scenario_Schema = [DomainRecord, IpRecord, AsRecord, TldRecord, WhoisScenario]

# Section 2: Class

class WhoisAPI:
    def __init__(self):
        """Initialize WhoisAPI with empty state."""
        self.current_time: str = ""
        self.domains: Dict[str, Any] = {}
        self.ips: Dict[str, Any] = {}
        self.asns: Dict[str, Any] = {}
        self.tlds: Dict[str, Any] = {}

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the API instance."""
        model = WhoisScenario(**scenario)
        self.current_time = model.current_time
        self.domains = model.domains
        self.ips = model.ips
        self.asns = model.asns
        self.tlds = model.tlds

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "current_time": self.current_time,
            "domains": self.domains,
            "ips": self.ips,
            "asns": self.asns,
            "tlds": self.tlds,
        }

    def whois_domain(self, domain: str) -> dict:
        """Retrieve WHOIS registration data for a domain name."""
        record = self.domains[domain]
        return DomainRecord(**record).model_dump()

    def whois_ip(self, ip: str) -> dict:
        """Retrieve WHOIS allocation data for an IP address."""
        record = self.ips[ip]
        return IpRecord(**record).model_dump()

    def whois_as(self, asn: str) -> dict:
        """Retrieve WHOIS information for an autonomous system number."""
        record = self.asns[asn]
        return AsRecord(**record).model_dump()

    def whois_tld(self, tld: str) -> dict:
        """Retrieve WHOIS information for a top-level domain."""
        key = tld.lstrip(".")
        record = self.tlds[key]
        return TldRecord(**record).model_dump()

# Section 3: MCP Tools

mcp = FastMCP(name="Whois")
api = WhoisAPI()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """
    Load scenario data into the Whois API.

    Args:
        scenario (dict): Scenario dictionary matching WhoisScenario schema.

    Returns:
        success_message (str): Success message.
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
    Save current Whois state as scenario dictionary.

    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return api.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def whois_domain(domain: str) -> dict:
    """
    Retrieve WHOIS registration data for a domain name.

    Args:
        domain (str): The fully-qualified domain name to query, e.g. "example.com".

    Returns:
        domainName (str): The canonical domain name returned by the registry.
        registrar (str): The accredited registrar responsible for the domain registration.
        creationDate (str): ISO 8601 timestamp indicating when the domain was first registered.
        updatedDate (str): ISO 8601 timestamp of the last modification to the domain record.
        expirationDate (str): ISO 8601 timestamp when the current registration expires.
        nameServers (list): List of authoritative name servers for the domain.
        status (list): Registry-level status codes for the domain.
        registrant (dict): Contact information of the registrant.
    """
    try:
        if not domain or not isinstance(domain, str):
            raise ValueError("Domain must be a non-empty string")
        if domain not in api.domains:
            raise ValueError(f"Domain '{domain}' not found")
        return api.whois_domain(domain)
    except Exception as e:
        raise e

@mcp.tool()
def whois_ip(ip: str) -> dict:
    """
    Retrieve WHOIS allocation data for an IPv4 or IPv6 address.

    Args:
        ip (str): IPv4 or IPv6 address to query, e.g. "8.8.8.8".

    Returns:
        ip (str): The queried IP address.
        range (str): Human-readable IP range allocated to the organization.
        netName (str): Registry label for the allocated network block.
        organization (str): Organization name that holds the allocation.
        country (str): ISO 3166-1 alpha-2 country code of the allocating entity.
        cidr (str): CIDR notation of the allocated prefix.
        updatedDate (str): ISO 8601 timestamp when the allocation record was last updated.
    """
    try:
        if not ip or not isinstance(ip, str):
            raise ValueError("IP must be a non-empty string")
        if ip not in api.ips:
            raise ValueError(f"IP '{ip}' not found")
        return api.whois_ip(ip)
    except Exception as e:
        raise e

@mcp.tool()
def whois_as(asn: str) -> dict:
    """
    Retrieve WHOIS information for an autonomous system number.

    Args:
        asn (str): Autonomous system number in ASxxxx format, e.g. "AS16509".

    Returns:
        asn (str): The queried autonomous system number.
        name (str): Short name assigned to the AS by the registry.
        organization (str): Organization name that owns the autonomous system.
        country (str): ISO 3166-1 alpha-2 country code of the AS holder.
        routes (list): List of IP prefixes announced by this AS.
        updatedDate (str): ISO 8601 timestamp when the AS record was last updated.
    """
    try:
        if not asn or not isinstance(asn, str):
            raise ValueError("ASN must be a non-empty string")
        if asn not in api.asns:
            raise ValueError(f"ASN '{asn}' not found")
        return api.whois_as(asn)
    except Exception as e:
        raise e

@mcp.tool()
def whois_tld(tld: str) -> dict:
    """
    Retrieve WHOIS information for a top-level domain.

    Args:
        tld (str): Top-level domain to query, with or without leading dot, e.g. "com" or ".org".

    Returns:
        tld (str): The canonical top-level domain suffix.
        sponsor (str): Entity responsible for operating the TLD registry.
        whoisServer (str): Hostname of the authoritative WHOIS server for this TLD.
        status (str): Registry status of the TLD.
        createdDate (str): ISO 8601 timestamp when the TLD was delegated.
        updatedDate (str): ISO 8601 timestamp when the TLD record was last updated.
    """
    try:
        if not tld or not isinstance(tld, str):
            raise ValueError("TLD must be a non-empty string")
        key = tld.lstrip(".")
        if key not in api.tlds:
            raise ValueError(f"TLD '{tld}' not found")
        return api.whois_tld(tld)
    except Exception as e:
        raise e

# Section 4: Entry Point

if __name__ == "__main__":
    mcp.run()
