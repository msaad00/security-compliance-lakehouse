"""SAML SSO configuration and login completion for server mode.

The endpoint-level SAML protocol handling stays optional and is imported only
when a deployment configures SAML. The local identity mapping intentionally
matches OIDC: a verified email resolves to one tenant user, then receives the
same hashed browser session token used by all human SSO flows.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import parse_qs

from sqlalchemy.orm import Session

from security_lakehouse.db import repository
from security_lakehouse.db.models import User

_TRUTHY = {"1", "true", "yes", "on"}
_REQUIRED_ENV = {
    "TRUSTOPS_SAML_SP_ENTITY_ID",
    "TRUSTOPS_SAML_ACS_URL",
    "TRUSTOPS_SAML_IDP_ENTITY_ID",
    "TRUSTOPS_SAML_IDP_SSO_URL",
    "TRUSTOPS_SAML_IDP_X509_CERT",
}
_EMAIL_ATTRIBUTE_NAMES = (
    "email",
    "mail",
    "EmailAddress",
    "emailAddress",
    "urn:oid:0.9.2342.19200300.100.1.3",
)


class SAMLConfigError(RuntimeError):
    """Raised when SAML environment configuration is incomplete."""


class SAMLLoginError(Exception):
    """Raised when a SAML assertion cannot be turned into a local session."""


@dataclass(frozen=True)
class SAMLConfig:
    """Resolved SAML service-provider and identity-provider settings."""

    sp_entity_id: str
    acs_url: str
    idp_entity_id: str
    idp_sso_url: str
    idp_x509_cert: str
    sls_url: str = ""
    tenant_slug: str = "default"
    auto_provision: bool = False
    default_role: str = "read_only"
    name_id_format: str = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"

    def settings(self) -> dict[str, Any]:
        """Return OneLogin python3-saml settings."""
        settings = {
            "strict": True,
            "debug": False,
            "sp": {
                "entityId": self.sp_entity_id,
                "assertionConsumerService": {
                    "url": self.acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "NameIDFormat": self.name_id_format,
            },
            "idp": {
                "entityId": self.idp_entity_id,
                "singleSignOnService": {
                    "url": self.idp_sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self.idp_x509_cert,
            },
            "security": {
                "wantAssertionsSigned": True,
                "wantMessagesSigned": False,
                "wantNameId": True,
                "wantNameIdEncrypted": False,
                "wantAttributeStatement": False,
                "authnRequestsSigned": False,
                "logoutRequestSigned": False,
                "logoutResponseSigned": False,
                "signatureAlgorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                "digestAlgorithm": "http://www.w3.org/2001/04/xmlenc#sha256",
            },
        }
        if self.sls_url:
            settings["sp"]["singleLogoutService"] = {
                "url": self.sls_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            }
        return settings


def load_saml_config() -> SAMLConfig | None:
    """Build SAML config from the environment, or ``None`` when disabled."""
    present = {name for name in _REQUIRED_ENV if os.environ.get(name)}
    if not present:
        return None
    missing = sorted(_REQUIRED_ENV - present)
    if missing:
        raise SAMLConfigError(f"incomplete SAML configuration; missing: {', '.join(missing)}")
    return SAMLConfig(
        sp_entity_id=os.environ["TRUSTOPS_SAML_SP_ENTITY_ID"],
        acs_url=os.environ["TRUSTOPS_SAML_ACS_URL"],
        idp_entity_id=os.environ["TRUSTOPS_SAML_IDP_ENTITY_ID"],
        idp_sso_url=os.environ["TRUSTOPS_SAML_IDP_SSO_URL"],
        idp_x509_cert=os.environ["TRUSTOPS_SAML_IDP_X509_CERT"],
        sls_url=os.environ.get("TRUSTOPS_SAML_SLS_URL", ""),
        tenant_slug=os.environ.get("TRUSTOPS_SAML_TENANT_SLUG", "default"),
        auto_provision=os.environ.get("TRUSTOPS_SAML_AUTO_PROVISION", "").lower() in _TRUTHY,
        default_role=os.environ.get("TRUSTOPS_SAML_DEFAULT_ROLE", "read_only"),
        name_id_format=os.environ.get(
            "TRUSTOPS_SAML_NAME_ID_FORMAT",
            "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        ),
    )


def build_saml_auth(config: SAMLConfig, request_data: dict[str, Any]):
    """Create a OneLogin SAML Auth object for the current request."""
    from onelogin.saml2.auth import OneLogin_Saml2_Auth

    return OneLogin_Saml2_Auth(request_data, old_settings=config.settings())


def saml_request_data(
    *,
    scheme: str,
    host: str,
    port: int | None,
    path: str,
    query: dict[str, str],
    body: bytes = b"",
) -> dict[str, Any]:
    """Convert an ASGI request into python3-saml's request shape."""
    post_data: dict[str, str] = {}
    if body:
        parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
        post_data = {key: values[-1] if values else "" for key, values in parsed.items()}
    return {
        "https": "on" if scheme == "https" else "off",
        "http_host": host,
        "server_port": port,
        "script_name": path,
        "get_data": query,
        "post_data": post_data,
    }


def email_from_saml_assertion(auth: Any) -> str:
    """Extract the best email identifier from a processed SAML assertion."""
    attributes = auth.get_attributes() or {}
    for name in _EMAIL_ATTRIBUTE_NAMES:
        values = attributes.get(name)
        if values:
            return str(values[0])
    name_id = auth.get_nameid()
    return str(name_id or "")


def complete_saml_login(
    session: Session,
    *,
    config: SAMLConfig,
    email: str,
    now: datetime | None = None,
) -> tuple[User, str]:
    """Map a verified SAML email to a local user + browser session token."""
    if not email:
        raise SAMLLoginError("identity provider returned no email")
    tenant = repository.get_tenant_by_slug(session, slug=config.tenant_slug)
    if tenant is None:
        raise SAMLLoginError(f"SAML tenant {config.tenant_slug!r} does not exist")
    user = repository.find_or_provision_user(
        session,
        tenant_id=tenant.id,
        email=email,
        auto_provision=config.auto_provision,
        default_role=config.default_role,
    )
    if user is None:
        raise SAMLLoginError(f"no provisioned user for {email!r} and auto-provisioning is disabled")
    if not user.is_active:
        raise SAMLLoginError(f"user {email!r} is disabled")
    _row, token = repository.create_user_session(session, tenant_id=tenant.id, user_id=user.id, idp="saml", now=now)
    return user, token
