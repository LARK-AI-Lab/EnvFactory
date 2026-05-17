# Whois Research Notes

## Data Source
- Official Docs: https://github.com/bharathvaj-ganesan/whois-mcp
- API Reference: https://www.iana.org/whois
- SDK/Tutorials: https://github.com/bharathvaj-ganesan/whois-mcp#available-tools
- Base URL: WHOIS registry servers

## API Overview
- **Purpose**: Look up registration and allocation data for domains, IP addresses, ASNs, and TLDs.
- **Category**: Internet registry
- **Target users**: Security, infrastructure, DNS, and domain research workflows.

## Authentication
- **Type**: None
- **How to obtain**: Not applicable.
- **Header/param format**: Not applicable.

## Core Endpoints & Design
- **whois_domain**: Retrieve domain registrar, dates, nameservers, statuses, and contacts.
- **whois_ip**: Retrieve IP allocation range and organization.
- **whois_as**: Retrieve autonomous system owner and route information.
- **whois_tld**: Retrieve TLD sponsor and WHOIS server information.

## Data Models
- `DomainWhois`: domainName, registrar, dates, nameServers, status, registrant
- `IpWhois`: ip, range, netName, organization, country, cidr
- `AsWhois`: asn, name, organization, country, routes
- `TldWhois`: tld, sponsor, whoisServer, status

## Use Cases
- Check who owns or operates a domain.
- Investigate IP ranges and ASNs.
- Resolve TLD registry metadata.

## Response Example
```json
{
  "domainName": "example.com",
  "registrar": "RESERVED-Internet Assigned Numbers Authority",
  "nameServers": ["a.iana-servers.net", "b.iana-servers.net"]
}
```

