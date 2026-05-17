from setuptools import setup, find_packages

# Basic requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Optional dependencies


setup(
    name='MCPFactory',
    version='0.1.0',
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        'sglang': ['sglang==0.5.9'],
        'vllm': ['vllm==0.8.5'],
    },
    author='Roland Xu',
    author_email='mxubh@connect.hkust-gz.edu.cn',
    url='https://github.com/RolandXMR/MCPFactory',
    description='MCPFactory',
)