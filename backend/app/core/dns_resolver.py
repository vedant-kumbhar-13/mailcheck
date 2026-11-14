from __future__ import annotations

import dns.asyncresolver
import dns.exception
import dns.rdatatype
import dns.resolver

from app.core.models import DomainResult


async def resolve_domain(domain: str, timeout: float = 3.0) -> DomainResult:
    """
    Check MX records for domain. If no MX, fall back to A/AAAA.
    - Null MX (priority 0, exchange ".") → is_null_mx=True
    - NXDOMAIN, timeout, SERVFAIL, etc. → dns_error set, has_mx=False
    """
    resolver = dns.asyncresolver.Resolver()
    resolver.lifetime = timeout

    # --- MX lookup ---
    try:
        answer = await resolver.resolve(domain, dns.rdatatype.MX)
        for rdata in answer:
            if rdata.preference == 0 and str(rdata.exchange) == ".":
                return DomainResult(is_null_mx=True)
        return DomainResult(has_mx=True)
    except dns.resolver.NXDOMAIN:
        return DomainResult(dns_error="nxdomain")
    except dns.exception.Timeout:
        return DomainResult(dns_error="timeout")
    except dns.resolver.NoAnswer:
        pass  # no MX records; try A/AAAA below
    except Exception as exc:  # noqa: BLE001
        return DomainResult(dns_error=str(exc)[:80])

    # --- A/AAAA fallback ---
    for rdtype in (dns.rdatatype.A, dns.rdatatype.AAAA):
        try:
            await resolver.resolve(domain, rdtype)
            return DomainResult(has_a_aaaa=True)
        except dns.resolver.NXDOMAIN:
            return DomainResult(dns_error="nxdomain")
        except dns.exception.Timeout:
            return DomainResult(dns_error="timeout")
        except (dns.resolver.NoAnswer, Exception):  # noqa: BLE001
            continue

    return DomainResult(dns_error="no_records")
