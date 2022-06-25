from setuptools import setup, find_packages

extras_require = {
    "unit": ["jsonpath-ng"],
}

setup(
    name="terraform-aws-github-webhook",
    extras_require=extras_require,
    packages=find_packages(),
)
