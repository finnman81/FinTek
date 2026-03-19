from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class EnvironmentConfig:
    env_name: Literal['dev', 'prod']
    account_id: str
    region: str
    api_domain_prefix: str
    app_domain_prefix: str
    branch: str
    branch_previews_enabled: bool


INDUSTRIAL_DEV = EnvironmentConfig(
    env_name='dev',
    account_id='666666666666',
    region='us-east-1',
    api_domain_prefix='api.industrial-dev',
    app_domain_prefix='app.industrial-dev',
    branch='develop',
    branch_previews_enabled=True,
)

INDUSTRIAL_PROD = EnvironmentConfig(
    env_name='prod',
    account_id='777777777777',
    region='us-east-1',
    api_domain_prefix='api.industrial',
    app_domain_prefix='app.industrial',
    branch='main',
    branch_previews_enabled=False,
)

SHARED_SERVICES_ACCOUNT = '555555555555'
LOG_ARCHIVE_ACCOUNT = '444444444444'
HOSTED_ZONE_NAME = 'munitor.ai'
RESOURCE_PREFIX = 'industrial'
GITHUB_REPO = 'munitor-ai/industrial-kb'
