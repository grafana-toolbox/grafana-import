import os

from grafana_import.constants import PKG_NAME, PKG_VERSION
from setuptools import setup, find_packages

# Global variables
requires = [
    'grafana-client<5',
    'jinja2<4',
    'pyyaml<7',
]

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.md")).read()

setup(
    name=PKG_NAME,
    version=PKG_VERSION,
    description='Export and import Grafana dashboards using the Grafana HTTP API.',
    long_description_content_type='text/markdown',
    long_description=README,
    license="Apache 2.0",
    author="Jean-Francois Pik",
    author_email="jfpik78@gmail.com",
    url="https://github.com/peekjef72/grafana-import-tool",
    entry_points={
        'console_scripts': [
            'grafana-import = grafana_import.cli:main'
        ]
    },
    packages=find_packages(),
    install_requires=requires,
    package_data={'': ['conf/*']},
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Science/Research",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications",
        "Topic :: Database",
        "Topic :: Internet",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Archiving",
        "Topic :: System :: Networking :: Monitoring",
    ],
    keywords="grafana http api grafana-client grafana-api http-client "
             "grafana-utils grafana-automation grafana-toolbox dashboard",
)
