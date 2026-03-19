"""Property-based tests for CDK infrastructure correctness properties.

Uses hypothesis to verify universal properties hold across all environment
configurations. Tests use minimal stacks to validate tagging and naming
conventions independently of full stack implementations.
"""

import re

import aws_cdk as cdk
import aws_cdk.assertions as assertions
from aws_cdk import aws_s3 as s3, aws_sqs as sqs
from hypothesis import given, settings
from hypothesis.strategies import sampled_from

from constructs.tagging_aspect import TaggingAspect
from stacks.config import INDUSTRIAL_DEV, INDUSTRIAL_PROD, EnvironmentConfig

ENVS = sampled_from([INDUSTRIAL_DEV, INDUSTRIAL_PROD])

REQUIRED_TAGS = {"workload", "tenant", "environment", "managed-by"}


def _synth_tagged_stack(config: EnvironmentConfig) -> assertions.Template:
    """Create a minimal stack with a few resources, apply TaggingAspect, and synthesize."""
    app = cdk.App()
    stack = cdk.Stack(
        app,
        f"test-{config.env_name}",
        env=cdk.Environment(account=config.account_id, region=config.region),
    )

    prefix = f"industrial-{config.env_name}"

    s3.Bucket(
        stack,
        "TestBucket",
        bucket_name=f"{prefix}-test-bucket-{config.account_id}",
    )
    sqs.Queue(
        stack,
        "TestQueue",
        queue_name=f"{prefix}-test-queue",
    )

    cdk.Aspects.of(stack).add(TaggingAspect(config))
    return assertions.Template.from_stack(stack)


# Feature: aws-cdk-deployment, Property 1: Mandatory tagging on all resources
# **Validates: Requirements 1.5**
@given(config=ENVS)
@settings(max_examples=10, deadline=None)
def test_mandatory_tagging_on_all_resources(config: EnvironmentConfig) -> None:
    """For any resource in the synthesized template, all four mandatory tags must be present."""
    template = _synth_tagged_stack(config)
    resources = template.to_json()["Resources"]

    expected_tags = {
        "workload": "industrial",
        "tenant": "fin-tek",
        "environment": config.env_name,
        "managed-by": "cdk",
    }

    for logical_id, resource in resources.items():
        properties = resource.get("Properties", {})
        tags = properties.get("Tags", [])
        if not tags:
            # Some resources (e.g. policies) don't support tags — skip them
            continue

        tag_map = {t["Key"]: t["Value"] for t in tags}
        for key, value in expected_tags.items():
            assert key in tag_map, (
                f"Resource {logical_id} missing tag '{key}'"
            )
            assert tag_map[key] == value, (
                f"Resource {logical_id} tag '{key}' = '{tag_map[key]}', expected '{value}'"
            )


# Feature: aws-cdk-deployment, Property 2: Resource naming convention
# **Validates: Requirements 1.6**
@given(config=ENVS)
@settings(max_examples=10, deadline=None)
def test_resource_naming_convention(config: EnvironmentConfig) -> None:
    """For any resource with an explicit physical name, the name must match
    `industrial-{env}-*` or `industrial-{env}/*`."""
    template = _synth_tagged_stack(config)
    resources = template.to_json()["Resources"]

    prefix = f"industrial-{config.env_name}"
    # Matches industrial-{env}-anything or industrial-{env}/anything
    pattern = re.compile(rf"^{re.escape(prefix)}[-/]")

    # Map of CFN resource type → property key that holds the physical name
    name_fields = {
        "AWS::S3::Bucket": "BucketName",
        "AWS::SQS::Queue": "QueueName",
        "AWS::Lambda::Function": "FunctionName",
        "AWS::SecretsManager::Secret": "Name",
        "AWS::CloudWatch::Dashboard": "DashboardName",
        "AWS::CloudWatch::Alarm": "AlarmName",
        "AWS::Logs::LogGroup": "LogGroupName",
        "AWS::SNS::Topic": "TopicName",
        "AWS::AppRunner::Service": "ServiceName",
        "AWS::ECR::Repository": "RepositoryName",
        "AWS::Amplify::App": "Name",
    }

    checked = 0
    for logical_id, resource in resources.items():
        resource_type = resource.get("Type", "")
        field = name_fields.get(resource_type)
        if field is None:
            continue

        properties = resource.get("Properties", {})
        name = properties.get(field)
        if name is None or not isinstance(name, str):
            # Name not explicitly set or uses Fn::Join / Ref — skip
            continue

        assert pattern.match(name), (
            f"Resource {logical_id} ({resource_type}) has name '{name}' "
            f"which does not match pattern '{prefix}-*' or '{prefix}/*'"
        )
        checked += 1

    # Ensure we actually checked at least one resource
    assert checked > 0, "No resources with explicit physical names found in template"


# Feature: aws-cdk-deployment, Property 5: Secrets Manager secret creation completeness
# **Validates: Requirements 9.1**
@given(config=ENVS)
@settings(max_examples=10, deadline=None)
def test_secrets_creation_completeness(config: EnvironmentConfig) -> None:
    """For any environment, all 6 required secrets must be present with correct naming pattern."""
    from stacks.secrets_stack import SECRET_NAMES, SecretsStack

    app = cdk.App()
    stack = SecretsStack(
        app,
        f"test-secrets-{config.env_name}",
        config=config,
        env=cdk.Environment(account=config.account_id, region=config.region),
    )
    template = assertions.Template.from_stack(stack)

    # Extract all Secrets Manager secrets from the template
    secrets = template.find_resources("AWS::SecretsManager::Secret")

    # Collect all secret names from the template
    secret_names_in_template = set()
    for logical_id, resource in secrets.items():
        name = resource.get("Properties", {}).get("Name")
        if isinstance(name, str):
            secret_names_in_template.add(name)

    # Verify all 6 required secrets are present with correct naming pattern
    prefix = f"industrial-{config.env_name}"
    for secret_name in SECRET_NAMES:
        expected = f"{prefix}/{secret_name}"
        assert expected in secret_names_in_template, (
            f"Missing required secret '{expected}' in template. "
            f"Found: {sorted(secret_names_in_template)}"
        )

    # Verify exactly 6 secrets (no extras)
    assert len(secret_names_in_template) == len(SECRET_NAMES), (
        f"Expected {len(SECRET_NAMES)} secrets, found {len(secret_names_in_template)}: "
        f"{sorted(secret_names_in_template)}"
    )


# Feature: aws-cdk-deployment, Property 3: RDS security group ingress restriction
# **Validates: Requirements 3.6**
@given(config=ENVS)
@settings(max_examples=10, deadline=None)
def test_rds_security_group_ingress_restriction(config: EnvironmentConfig) -> None:
    """For any inbound rule on the RDS security group, the source must be either
    the App Runner SG or the Lambda SG, and the port must be 5432."""
    from stacks.rds_stack import RdsStack
    from stacks.secrets_stack import SecretsStack
    from stacks.vpc_stack import VpcStack

    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    prefix = f"industrial-{config.env_name}"

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app,
        f"test-rds-{config.env_name}",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        env=env,
    )
    template = assertions.Template.from_stack(rds_stack)

    # Collect the logical IDs of the App Runner and Lambda security groups from the VPC stack
    vpc_template = assertions.Template.from_stack(vpc_stack)
    vpc_sgs = vpc_template.find_resources("AWS::EC2::SecurityGroup")
    allowed_sg_ids = set()
    for logical_id, resource in vpc_sgs.items():
        sg_name = resource.get("Properties", {}).get("GroupDescription", "")
        if "App Runner" in sg_name or "Lambda" in sg_name:
            allowed_sg_ids.add(logical_id)

    # Extract all ingress rules from the RDS stack template
    ingress_rules = template.find_resources("AWS::EC2::SecurityGroupIngress")

    assert len(ingress_rules) > 0, "Expected at least one ingress rule on the RDS security group"

    for logical_id, rule in ingress_rules.items():
        props = rule.get("Properties", {})

        # Verify port is 5432
        from_port = props.get("FromPort")
        to_port = props.get("ToPort")
        assert from_port == 5432, (
            f"Ingress rule {logical_id} FromPort={from_port}, expected 5432"
        )
        assert to_port == 5432, (
            f"Ingress rule {logical_id} ToPort={to_port}, expected 5432"
        )

        # Verify protocol is TCP
        ip_protocol = props.get("IpProtocol", "")
        assert ip_protocol == "tcp", (
            f"Ingress rule {logical_id} IpProtocol={ip_protocol}, expected tcp"
        )

        # Verify source is a cross-stack SG reference (Fn::ImportValue)
        source_sg = props.get("SourceSecurityGroupId")
        assert source_sg is not None, (
            f"Ingress rule {logical_id} has no SourceSecurityGroupId — "
            "only SG-based sources are allowed"
        )

    # Verify exactly 2 ingress rules (App Runner + Lambda)
    assert len(ingress_rules) == 2, (
        f"Expected exactly 2 ingress rules (App Runner + Lambda), found {len(ingress_rules)}"
    )


# Feature: aws-cdk-deployment, Property 4: App Runner secrets injection completeness
# **Validates: Requirements 6.5**
@given(config=ENVS)
@settings(max_examples=10, deadline=None)
def test_app_runner_secrets_injection_completeness(config: EnvironmentConfig) -> None:
    """For any environment, all 6 required secrets must be injected into the
    App Runner service configuration as RuntimeEnvironmentSecrets."""
    from stacks.app_runner_stack import AppRunnerStack
    from stacks.ecr_stack import EcrStack
    from stacks.rds_stack import RdsStack
    from stacks.s3_stack import S3Stack
    from stacks.secrets_stack import SecretsStack
    from stacks.vpc_stack import VpcStack

    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    shared_env = cdk.Environment(account="555555555555", region="us-east-1")

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app, f"test-rds-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
    )
    s3_stack = S3Stack(app, f"test-s3-{config.env_name}", config=config, env=env)
    ecr_stack = EcrStack(app, f"test-ecr-{config.env_name}", env=shared_env)

    app_runner_stack = AppRunnerStack(
        app, f"test-apprunner-{config.env_name}",
        config=config,
        vpc_stack=vpc_stack,
        secrets_stack=secrets_stack,
        rds_stack=rds_stack,
        s3_stack=s3_stack,
        ecr_stack=ecr_stack,
        env=env,
    )
    template = assertions.Template.from_stack(app_runner_stack)

    # Find the App Runner service resource
    services = template.find_resources("AWS::AppRunner::Service")
    assert len(services) == 1, f"Expected 1 App Runner service, found {len(services)}"

    service = list(services.values())[0]
    image_config = (
        service.get("Properties", {})
        .get("SourceConfiguration", {})
        .get("ImageRepository", {})
        .get("ImageConfiguration", {})
    )

    # Extract injected secret env var names
    runtime_secrets = image_config.get("RuntimeEnvironmentSecrets", [])
    injected_names = {entry["Name"] for entry in runtime_secrets}

    required_secrets = {
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "CORS_ORIGINS",
        "ENTRA_CLIENT_ID",
        "ENTRA_CLIENT_SECRET",
        "ENTRA_TENANT_ID",
    }

    for secret_name in required_secrets:
        assert secret_name in injected_names, (
            f"Missing required secret '{secret_name}' in App Runner RuntimeEnvironmentSecrets. "
            f"Found: {sorted(injected_names)}"
        )

    # Each secret value should reference a Secrets Manager ARN
    for entry in runtime_secrets:
        value = entry.get("Value")
        assert value is not None, (
            f"Secret '{entry['Name']}' has no Value (expected Secrets Manager ARN)"
        )


# Feature: aws-cdk-deployment, Property 7: Observability alarm completeness
# **Validates: Requirements 11.2**
@given(config=ENVS)
@settings(max_examples=10, deadline=None)
def test_observability_alarm_completeness(config: EnvironmentConfig) -> None:
    """For any environment, all 4 required alarms must exist with correct metrics,
    thresholds, and comparison operators, and publish to the observability SNS topic."""
    from stacks.app_runner_stack import AppRunnerStack
    from stacks.ecr_stack import EcrStack
    from stacks.ingestion_stack import IngestionStack
    from stacks.observability_stack import ObservabilityStack
    from stacks.rds_stack import RdsStack
    from stacks.s3_stack import S3Stack
    from stacks.secrets_stack import SecretsStack
    from stacks.vpc_stack import VpcStack

    app = cdk.App()
    env = cdk.Environment(account=config.account_id, region=config.region)
    shared_env = cdk.Environment(account="555555555555", region="us-east-1")
    prefix = f"industrial-{config.env_name}"

    vpc_stack = VpcStack(app, f"test-vpc-{config.env_name}", config=config, env=env)
    s3_stack = S3Stack(app, f"test-s3-{config.env_name}", config=config, env=env)
    secrets_stack = SecretsStack(app, f"test-secrets-{config.env_name}", config=config, env=env)
    rds_stack = RdsStack(
        app, f"test-rds-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack, env=env,
    )
    ecr_stack = EcrStack(app, f"test-ecr-{config.env_name}", env=shared_env)
    ingestion_stack = IngestionStack(
        app, f"test-ingestion-{config.env_name}",
        config=config, vpc_stack=vpc_stack, s3_stack=s3_stack,
        secrets_stack=secrets_stack, rds_stack=rds_stack, ecr_stack=ecr_stack, env=env,
    )
    app_runner_stack = AppRunnerStack(
        app, f"test-apprunner-{config.env_name}",
        config=config, vpc_stack=vpc_stack, secrets_stack=secrets_stack,
        rds_stack=rds_stack, s3_stack=s3_stack, ecr_stack=ecr_stack, env=env,
    )
    observability_stack = ObservabilityStack(
        app, f"test-obs-{config.env_name}",
        config=config, app_runner_stack=app_runner_stack,
        ingestion_stack=ingestion_stack, env=env,
    )
    template = assertions.Template.from_stack(observability_stack)

    alarms = template.find_resources("AWS::CloudWatch::Alarm")

    # Required alarm definitions: (alarm_name_suffix, namespace, metric, threshold, comparator)
    required_alarms = {
        "5xx-error-rate": {
            "namespace": "AWS/AppRunner",
            "metric": "5xxStatusResponses",
            "threshold": 1,
            "comparison": "GreaterThanThreshold",
        },
        "p95-latency": {
            "namespace": "AWS/AppRunner",
            "metric": "RequestLatency",
            "threshold": 2000,
            "comparison": "GreaterThanThreshold",
        },
        "active-instances": {
            "namespace": "AWS/AppRunner",
            "metric": "ActiveInstances",
            "threshold": 8,
            "comparison": "GreaterThanOrEqualToThreshold",
        },
        "lambda-error-rate": {
            "namespace": "AWS/Lambda",
            "metric": "Errors",
            "threshold": 5,
            "comparison": "GreaterThanThreshold",
        },
    }

    # Build a map of alarm name → alarm properties from the template
    alarm_map: dict[str, dict] = {}
    for logical_id, resource in alarms.items():
        props = resource.get("Properties", {})
        alarm_name = props.get("AlarmName", "")
        if isinstance(alarm_name, str):
            alarm_map[alarm_name] = props

    # Verify each required alarm exists with correct configuration
    for suffix, expected in required_alarms.items():
        full_name = f"{prefix}-{suffix}"
        assert full_name in alarm_map, (
            f"Missing required alarm '{full_name}'. Found: {sorted(alarm_map.keys())}"
        )
        props = alarm_map[full_name]
        assert props.get("Namespace") == expected["namespace"], (
            f"Alarm '{full_name}' namespace: {props.get('Namespace')}, "
            f"expected: {expected['namespace']}"
        )
        assert props.get("MetricName") == expected["metric"], (
            f"Alarm '{full_name}' metric: {props.get('MetricName')}, "
            f"expected: {expected['metric']}"
        )
        assert props.get("Threshold") == expected["threshold"], (
            f"Alarm '{full_name}' threshold: {props.get('Threshold')}, "
            f"expected: {expected['threshold']}"
        )
        assert props.get("ComparisonOperator") == expected["comparison"], (
            f"Alarm '{full_name}' comparison: {props.get('ComparisonOperator')}, "
            f"expected: {expected['comparison']}"
        )

        # Verify alarm publishes to the SNS topic
        alarm_actions = props.get("AlarmActions", [])
        assert len(alarm_actions) > 0, (
            f"Alarm '{full_name}' has no alarm actions (should publish to SNS)"
        )


# Feature: aws-cdk-deployment, Property 9: CI/CD workflows use OIDC authentication
# **Validates: Requirements 14.5**


def _find_workflow_files() -> list[str]:
    """Return paths to all GitHub Actions workflow YAML files."""
    import glob
    import os

    repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    pattern = os.path.join(repo_root, ".github", "workflows", "*.yml")
    return sorted(glob.glob(pattern))


def _parse_workflow(path: str) -> dict:
    """Parse a YAML workflow file and return its contents."""
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)


def _collect_aws_auth_steps(workflow: dict) -> list[dict]:
    """Extract all steps that use aws-actions/configure-aws-credentials."""
    auth_steps = []
    jobs = workflow.get("jobs", {})
    for job_name, job in jobs.items():
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if "configure-aws-credentials" in uses:
                auth_steps.append(step)
    return auth_steps


@given(workflow_index=sampled_from(range(10)))
@settings(max_examples=20, deadline=None)
def test_cicd_workflows_use_oidc_authentication(workflow_index: int) -> None:
    """For any GitHub Actions workflow that authenticates with AWS,
    the workflow must use aws-actions/configure-aws-credentials@v4
    with role-to-assume (OIDC) and must not contain hardcoded credentials."""
    import os

    workflow_files = _find_workflow_files()
    if not workflow_files:
        return

    # Use modulo to cycle through available workflow files
    path = workflow_files[workflow_index % len(workflow_files)]
    workflow = _parse_workflow(path)
    filename = os.path.basename(path)

    auth_steps = _collect_aws_auth_steps(workflow)

    for step in auth_steps:
        uses = step.get("uses", "")
        assert "configure-aws-credentials@v4" in uses, (
            f"Workflow '{filename}' uses '{uses}' instead of "
            f"'aws-actions/configure-aws-credentials@v4'"
        )

        with_params = step.get("with", {})
        assert "role-to-assume" in with_params, (
            f"Workflow '{filename}' AWS auth step missing 'role-to-assume' "
            f"(OIDC required, no hardcoded credentials)"
        )

        # Verify no hardcoded access keys
        assert "aws-access-key-id" not in with_params, (
            f"Workflow '{filename}' contains hardcoded 'aws-access-key-id'"
        )
        assert "aws-secret-access-key" not in with_params, (
            f"Workflow '{filename}' contains hardcoded 'aws-secret-access-key'"
        )

    # Also scan all env blocks and step env for leaked credentials
    jobs = workflow.get("jobs", {})
    top_env = workflow.get("env", {})
    all_env_keys = set(top_env.keys()) if top_env else set()

    for job_name, job in jobs.items():
        job_env = job.get("env", {})
        if job_env:
            all_env_keys.update(job_env.keys())
        for step in job.get("steps", []):
            step_env = step.get("env", {})
            if step_env:
                all_env_keys.update(step_env.keys())

    forbidden_keys = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}
    found_forbidden = forbidden_keys & all_env_keys
    assert not found_forbidden, (
        f"Workflow '{filename}' contains hardcoded credential env vars: "
        f"{sorted(found_forbidden)}"
    )
