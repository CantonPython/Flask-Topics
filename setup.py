from setuptools import setup

setup(
    name='topic_creator',
    packages=['topic_creator'],
    include_package_data=True,
    install_requires=[
        'flask',
        'werkzeug'
    ]
)