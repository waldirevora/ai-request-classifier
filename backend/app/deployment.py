"""Explicit cloud policy. A request header never selects a security environment."""
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import os,ipaddress
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[2]

def production():return os.getenv('SF_ENV','local')=='production'

@dataclass(frozen=True)
class PublicSettings:
    origin:str
    maintenance:bool=True
    maintenance_token:str=''
    dist:Path=ROOT/'frontend/dist'
    proxy_networks:tuple=()
    require_tls:bool=True

    @classmethod
    def from_env(cls):
        if not production():raise ValueError('SF_ENV=production is required')
        origin=os.getenv('SF_PUBLIC_ORIGIN') or os.getenv('RENDER_EXTERNAL_URL','')
        parts=urlsplit(origin)
        if parts.scheme!='https' or not parts.hostname or parts.username or parts.password or parts.path or parts.query or parts.fragment or '*' in origin:
            raise ValueError('An exact HTTPS public origin is required')
        token=os.getenv('SF_MAINTENANCE_TOKEN','')
        if len(token)<32:raise ValueError('A private maintenance token is required')
        if not os.getenv('PGHOST','').endswith('.neon.tech') or '-pooler' in os.getenv('PGHOST',''):
            raise ValueError('A direct Neon endpoint is required')
        if os.getenv('PGDATABASE')!='solicitaflow_demo' or os.getenv('PGUSER')!='ai_classifier_app':
            raise ValueError('A dedicated public demonstration database and limited role are required')
        if os.getenv('PGSSLMODE')!='verify-full' or not os.getenv('PGSSLROOTCERT'):
            raise ValueError('Verified PostgreSQL TLS is required')
        if os.getenv('SF_SECURE_LEGACY','true')!='true' or os.getenv('SF_QA_MODE','false')!='false':
            raise ValueError('Unsafe public environment flags')
        if os.getenv('SF_CLEANUP_USER')!='ai_classifier_cleanup' or not os.getenv('SF_CLEANUP_PASSWORD'):
            raise ValueError('A separate limited cleanup credential is required')
        from app.ai_control import Policy
        policy=Policy.load()
        if policy.concurrent!=1 or policy.daily_calls>10 or policy.workspace_calls>3 or policy.daily_usd>Decimal('0.05'):
            raise ValueError('Public AI limits exceed the approved conservative envelope')
        networks=tuple(ipaddress.ip_network(v.strip()) for v in os.getenv('SF_TRUSTED_PROXY_CIDRS','').split(',') if v.strip())
        if any(n.prefixlen==0 for n in networks):raise ValueError('Wildcard proxy trust is forbidden')
        return cls(origin,os.getenv('SF_MAINTENANCE','true')!='false',token,proxy_networks=networks)


def client_network(scope,settings):
    """Only explicit transport peers may assert Cloudflare's overwritten client IP."""
    peer=(scope.get('client') or ('unknown',0))[0]
    try:address=ipaddress.ip_address(peer)
    except ValueError:return 'unresolved-peer'
    headers=dict(scope['headers'])
    if any(address in net for net in settings.proxy_networks):
        try:address=ipaddress.ip_address(headers.get(b'cf-connecting-ip',b'').decode('ascii'))
        except (ValueError,UnicodeError):pass
    # X-Forwarded-For and X-Forwarded-Proto from the caller are never trusted.
    return str(ipaddress.ip_network(str(address)+('/24' if address.version==4 else '/56'),strict=False))
