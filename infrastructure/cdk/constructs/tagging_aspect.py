import jsii
import aws_cdk as cdk
import constructs as _constructs

from stacks.config import EnvironmentConfig


@jsii.implements(cdk.IAspect)
class TaggingAspect:
    """CDK Aspect that applies mandatory tags to all resources."""

    def __init__(self, config: EnvironmentConfig) -> None:
        self._tags = {
            'workload': 'industrial',
            'tenant': 'fin-tek',
            'environment': config.env_name,
            'managed-by': 'cdk',
        }

    def visit(self, node: _constructs.IConstruct) -> None:
        for key, value in self._tags.items():
            cdk.Tags.of(node).add(key, value)
