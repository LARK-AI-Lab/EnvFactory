# Data Source: https://github.com/bharathvaj-ganesan/whois-mcp
# Server: Whois
# Category: Internet Registry


def whois_domain(domain: str) -> dict:
    """
    Look up WHOIS registration information for a domain name.

    Args:
        domain (str): Domain name such as "example.com"

    Returns:
        dict: {
            "domainName": str,
            "registrar": str,
            "creationDate": str,
            "updatedDate": str,
            "expirationDate": str,
            "nameServers": list[str],
            "status": list[str],
            "registrant": dict
        }
    """
    pass


def whois_ip(ip: str) -> dict:
    """
    Look up WHOIS allocation information for an IP address.

    Args:
        ip (str): IPv4 or IPv6 address

    Returns:
        dict: {
            "ip": str,
            "range": str,
            "netName": str,
            "organization": str,
            "country": str,
            "cidr": str,
            "updatedDate": str
        }
    """
    pass


def whois_as(asn: str) -> dict:
    """
    Look up WHOIS information for an autonomous system number.

    Args:
        asn (str): Autonomous system number such as "AS16509"

    Returns:
        dict: {
            "asn": str,
            "name": str,
            "organization": str,
            "country": str,
            "routes": list[str],
            "updatedDate": str
        }
    """
    pass


def whois_tld(tld: str) -> dict:
    """
    Look up WHOIS information for a top-level domain.

    Args:
        tld (str): Top-level domain such as "com" or ".org"

    Returns:
        dict: {
            "tld": str,
            "sponsor": str,
            "whoisServer": str,
            "status": str,
            "createdDate": str,
            "updatedDate": str
        }
    """
    pass

