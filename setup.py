from setuptools import setup, find_packages

setup(
    name="audiobook-dl",
    version="0.0.0",
    packages=find_packages(),
    description="Downloads audiobooks",
    install_requires=[
        "requests",
        "argparse",
        "lxml",
        "rich",
        "mutagen"
    ],
    entry_points={
        'console_scripts': [
            'audiobook-dl=audiobookdl.main:run'
        ]
    },
)
