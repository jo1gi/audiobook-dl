from setuptools import setup, find_packages

setup(
    name="audiobook-dl",
    version="0.1.0",
    packages=find_packages(),
    description="Downloads audiobooks",
    install_requires=[
        "requests",
        "lxml",
        "rich",
        "mutagen"
        "pillow"
        "pydub"
    ],
    entry_points={
        'console_scripts': [
            'audiobook-dl=audiobookdl:run'
        ]
    },
)
