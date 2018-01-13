from setuptools import setup

setup(
    name='topic-creator',
    packages=['topic-creator'],
    include_package_data=True,
    install_requires=[
        'flask',
        'werkzeug'
    ]
)