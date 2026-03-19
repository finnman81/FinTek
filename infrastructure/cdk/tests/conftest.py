"""Conftest for CDK tests.

Resolves the naming conflict between the local `constructs/` package
(infrastructure/cdk/constructs/) and the pip-installed `constructs` package
that aws_cdk depends on.

The local `constructs/` directory shadows the installed `constructs` package
when pytest adds infrastructure/cdk/ to sys.path. We fix this by ensuring
the site-packages version of `constructs` is imported first.
"""

import importlib
import sys
from pathlib import Path

# Locate the site-packages constructs package and force-load it before
# the local constructs/ directory can shadow it.
_cdk_root = Path(__file__).resolve().parent.parent

for _p in list(sys.path):
    if "site-packages" in _p and (Path(_p) / "constructs" / "_jsii").is_dir():
        # Temporarily make site-packages the highest priority
        sys.path.remove(_p)
        sys.path.insert(0, _p)
        # Force-load the real constructs package
        if "constructs" in sys.modules:
            del sys.modules["constructs"]
        if "constructs._jsii" in sys.modules:
            del sys.modules["constructs._jsii"]
        import constructs  # noqa: F401
        import constructs._jsii  # noqa: F401
        # Restore path order
        sys.path.remove(_p)
        sys.path.append(_p)
        break

# Ensure infrastructure/cdk/ is on path for local stacks/constructs imports
_cdk_str = str(_cdk_root)
if _cdk_str not in sys.path:
    sys.path.insert(0, _cdk_str)
