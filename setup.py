from setuptools import setup

setup(
    name="audiobook-dl",
    version="0.0.0",
    packages=["audiobookdl"],
    description="Downloads audiobooks",
    install_requires=[
        "requests",
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
