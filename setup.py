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
        'dev': ['pytest>=8,<10', 'psutil>=7,<8'],
        'mini': ['sentence-transformers>=3'],
        'sglang': ['sglang==0.5.9'],
        # CUDA/PyTorch wheels must be selected against the live driver. Keep
        # this convenience extra unpinned; MoLab uses requirements-molab.txt
        # with uv --torch-backend=auto instead.
        'vllm': ['vllm'],
    },
    python_requires='>=3.12',
    author='Roland Xu',
    author_email='mxubh@connect.hkust-gz.edu.cn',
    url='https://github.com/RolandXMR/MCPFactory',
    description='MCPFactory',
)
