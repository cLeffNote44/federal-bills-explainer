"""Setup for fbx_core package."""

from setuptools import setup, find_packages

setup(
    name="fbx-core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pgvector>=0.2.0",
    ],
    python_requires=">=3.9",
    author="Federal Bills Explainer Team",
    description="Core models and database utilities for Federal Bills Explainer",
)
