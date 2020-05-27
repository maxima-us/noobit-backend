# Always prefer setuptools over distutils
from os import path
from setuptools import setup, find_packages
# io.open is needed for projects that support Python 2.7
# It ensures open() defaults to text mode with universal newlines,
# and accepts an argument to specify the text encoding
# Python 3 only projects can skip this import
from io import open

here = path.abspath(path.dirname(__file__))


# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='noobit',  # Required
    version='0.0.0',  # Required
    description='Backend to crypto trading framework NooBit',  # Optional
    long_description=long_description,  # Optional
    long_description_content_type='text/markdown',  # Optional
    url='https://github.com/maxima-us/noobit-backend',  # Optional
    author='maximaus',  # Optional
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  # Optional
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    package_dir={'': 'src'},  # Optional
    packages=find_packages(where='src'),  # Required
    python_requires='>=3.7, <4',
    install_requires=[
        'aioredis>=1, <2',
        'click>=7, <8',
        'fastapi>=0, <1',
        'httpx>=0, <1',
        'pytest-asyncio>=0, <1',
        'python-rapidjson>=0, <1',
        'python-dotenv>=0, <1',
        'pandas>=0, <1',
        'requests>=2, <3',
        'stackprinter>=0, <1',
        'structlog>=20, <21',
        'tortoise-orm>=0, <1',
        'typesystem>=0, <1',
        'ujson>=1, <2',
        'uvicorn>=0, <1',
    ],
    entry_points={  # Optional
        'console_scripts': [
            # noobit main module
            'noobit-aggregate=noobit.cli:aggregate_historical_trades',
            'noobit-feedhandler=noobit.cli:run_feedhandler',
            'noobit-server=noobit.cli:run_server',
            'noobit-stratrunner=noobit.cli:run_stratrunner',
            'noobit-backtester=noobit.cli:run_backtester',
            # noobit user module
            'noobit-add-keys=noobit_user.cli:open_env_file',
            'noobit-add-strategy=noobit_user.cli:create_user_strategy'
        ],
    },
)
