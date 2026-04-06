from setuptools import setup, find_packages

setup(
    name='slsm',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Cors',
        'Werkzeug'
    ],
    entry_points={
        'console_scripts': [
            'slsm-server=slsm.server:main',
        ],
    },
)
