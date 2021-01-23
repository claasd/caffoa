from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='caffoa',
    version='0.3.1',
    packages=['caffoa'],
    package_data={
        'caffoa': ['./data/templates/*'],
    },
    include_package_data=True,
    url='https://github.com/claasd/caffoa',
    license='MIT',
    author='Claas Diederichs',
    author_email='',
    description='Create Azure Functions From Open Api (for C#)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "prance",
        "openapi-spec-validator"
    ]
)
