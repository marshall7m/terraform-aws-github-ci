from setuptools import setup, find_packages

install_requires = [
    'pytest-terra-fixt @ git+https://github.com/marshall7m/pytest-terra-fixt@v0.3.3#egg=pytest-terra-fixt'
]
setup(
    name='terraform-aws-github-webhook',
    install_requires=install_requires,
    packages=find_packages()
)