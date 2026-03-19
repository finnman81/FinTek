"""VPC stack for Industrial workload.

Creates a VPC with public/private subnets across 2 AZs, a single NAT gateway
(cost optimization), an S3 gateway endpoint, and security groups for Lambda
and App Runner that downstream stacks reference.
"""

import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from stacks.config import RESOURCE_PREFIX, EnvironmentConfig


class VpcStack(cdk.Stack):
    """Networking foundation: VPC, subnets, NAT, S3 endpoint, security groups."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        prefix = f"{RESOURCE_PREFIX}-{config.env_name}"

        # VPC with 2 public + 2 private subnets, single NAT gateway
        self._vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=f"{prefix}-vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.1.0.0/16"),
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=f"{prefix}-public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name=f"{prefix}-private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # S3 gateway endpoint — avoids NAT charges for S3 traffic
        self._vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # Lambda security group — all outbound for OpenAI API calls via NAT
        self._lambda_security_group = ec2.SecurityGroup(
            self,
            "LambdaSg",
            vpc=self._vpc,
            security_group_name=f"{prefix}-lambda-sg",
            description="Security group for ingestion Lambda functions",
            allow_all_outbound=True,
        )

        # App Runner security group — all outbound
        self._app_runner_security_group = ec2.SecurityGroup(
            self,
            "AppRunnerSg",
            vpc=self._vpc,
            security_group_name=f"{prefix}-app-runner-sg",
            description="Security group for App Runner VPC connector",
            allow_all_outbound=True,
        )

    @property
    def vpc(self) -> ec2.Vpc:
        return self._vpc

    @property
    def private_subnets(self) -> list[ec2.ISubnet]:
        return self._vpc.private_subnets

    @property
    def public_subnets(self) -> list[ec2.ISubnet]:
        return self._vpc.public_subnets

    @property
    def lambda_security_group(self) -> ec2.SecurityGroup:
        return self._lambda_security_group

    @property
    def app_runner_security_group(self) -> ec2.SecurityGroup:
        return self._app_runner_security_group
