from setuptools import setup, find_packages

setup(
    name="audiobook-dl",
    version="0.3.0",
    packages=find_packages(),
    description="Downloads audiobooks",
    install_requires=[
        "requests",
        "lxml",
        "rich",
        "mutagen",
        "pillow",
        "pydub",
        "cssselect",
        "mypy",
        "m3u8",
        "pycrypto"
    ],
    entry_points={
        'console_scripts': [
            'audiobook-dl=audiobookdl.__main__:run'
        ]
    },
    package_data={
        '': ["*.txt"]
    },
)
