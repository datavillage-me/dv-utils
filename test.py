from dv_utils import solid_utils
import json
import os
import requests

uname = os.environ.get('SOLID_IDP_USERNAME')
password = os.environ.get('SOLID_IDP_PASSWORD')
token = solid_utils.get_dv_soidp_token('https://control-plane.gke.datavillage.me/.well-known/imohmkmd/webid', 'https://control-plane.gke.datavillage.me/.well-known/imohmkmd/appid')
# token = ""
print(token)
pod_url = "https://storage.sandbox-nl-pod.datanutsbedrijf.be/b6738617-737c-4a03-8178-b21543efe44b"
file_path = "sndk/userProfile.ttl"
vc_derive = "https://vc.sandbox-nl-pod.datanutsbedrijf.be/derive"

# all_grants = solid_utils.get_all_access_grants(vc_derive, token)

grant = {
    "id": "https://vc.sandbox-nl-pod.datanutsbedrijf.be/vc/d44e5b02-7053-4647-8e4e-6bbe502fb4f3",
    "type": [
        "VerifiableCredential",
        "SolidAccessGrant"
    ],
    "proof": {
        "type": "Ed25519Signature2020",
        "created": "2024-11-14T13:29:26.791Z",
        "domain": "solid",
        "proofPurpose": "assertionMethod",
        "proofValue": "z5UHNpFEYR37TfUcYJKmULMofiqCh9GX5KqF6sNC1MpnxUyKQ4DVV6qic8tazMLZNj8UuVGZCfkr3Z77PCJZoe8WB",
        "verificationMethod": "https://vc.sandbox-nl-pod.datanutsbedrijf.be/key/057492b0-796e-36cf-ad4c-f8cc43965d26"
    },
    "credentialStatus": {
        "id": "https://vc.sandbox-nl-pod.datanutsbedrijf.be/status/zlmV#0",
        "type": "RevocationList2020Status",
        "revocationListCredential": "https://vc.sandbox-nl-pod.datanutsbedrijf.be/status/zlmV",
        "revocationListIndex": "0"
    },
    "credentialSubject": {
        "id": "https://886d2620-9088-4904-b585-c5c252af0eed.idp.dev.jouw.id/profile/card#me",
        "providedConsent": {
            "mode": [
                "Read",
                "Write"
            ],
            "forPersonalData": "https://storage.sandbox-nl-pod.datanutsbedrijf.be/b6738617-737c-4a03-8178-b21543efe44b/sndk/",
            "hasStatus": "ConsentStatusExplicitlyGiven",
            "isProvidedTo": "https://control-plane.gke.datavillage.me/.well-known/imohmkmd/webid",
            "inherit": "true"
        }
    },
    "expirationDate": "2024-11-24T13:29:26.339Z",
    "issuanceDate": "2024-11-14T13:29:26.778Z",
    "issuer": "https://vc.sandbox-nl-pod.datanutsbedrijf.be",
    "@context": [
        "https://www.w3.org/2018/credentials/v1",
        "https://schema.inrupt.com/credentials/v1.jsonld",
        "https://w3id.org/security/data-integrity/v1",
        "https://w3id.org/vc-revocation-list-2020/v1",
        "https://w3id.org/vc/status-list/2021/v1",
        "https://w3id.org/security/suites/ed25519-2020/v1"
    ]
}
# content = solid_utils.get_acp_from_pod_url(pod_url, file_path)

file_uri = f"{pod_url}/{file_path}"
uma_token = solid_utils.get_uma_token(token,file_uri , grant)
res = requests.get(file_uri, headers={'Authorization': f"Bearer {uma_token}"})
print(res.status_code)
print(res.text)

