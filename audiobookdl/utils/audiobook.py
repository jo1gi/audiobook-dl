import requests
from typing import Dict, Generic, List, Optional, Union, Sequence, Tuple, TypeVar
import json
from attrs import define, Factory


@define
class Chapter:
    # Start time of chapter in milliseconds
    start: int
    # Title of chapter
    title: str


@define
class Cover:
    image: bytes
    extension: str


@define
class AESEncryption:
    key: bytes
    iv: bytes


AudiobookFileEncryption = AESEncryption


@define
class AudiobookFile:
    # Url to audio file
    url: str
    # Output file extension
    ext: str
    # Title of file
    title: Optional[str] = None
    # Headers for request
    headers: Dict[str, str] = Factory(dict)
    # Encryption method
    encryption_method: Optional[AudiobookFileEncryption] = None



@define
class AudiobookMetadata:
    title: str
    series: Optional[str] = None
    authors: List[str] = Factory(list)
    narrators: List[str] = Factory(list)
    language: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None

    def add_author(self, author: str):
        """Add author to metadata"""
        self.authors.append(author)

    def add_narrator(self, narrator: str):
        """Add narrator to metadata"""
        self.narrators.append(narrator)

    def add_authors(self, authors: Sequence[str]):
        self.authors.extend(authors)

    def add_narrators(self, narrators: Sequence[str]):
        self.narrators.extend(narrators)

    def all_properties(self, allow_duplicate_keys = False) -> List[Tuple[str, str]]:
        result: List[Tuple[str, str]] = []
        add = add_if_value_exists(self, result)
        add("title")
        add("series")
        add("language")
        add("description")
        add("isbn")
        if allow_duplicate_keys:
            for author in self.authors:
                result.append(("author", author))
            for narrator in self.narrators:
                result.append(("narrator", narrator))
        else:
            result.append(("author", self.author))
            result.append(("narrator", self.narrator))
        return result

    def all_properties_dict(self) -> Dict[str, str]:
        result = {}
        for (key, value) in self.all_properties(allow_duplicate_keys=False):
            result[key] = value
        return result

    @property
    def author(self) -> str:
        """All authors concatenated into a single string"""
        return "; ".join(self.authors)

    @property
    def narrator(self) -> str:
        """All narrators concatenated into a single string"""
        return "; ".join(self.narrators)


    def as_dict(self) -> dict:
        """
        Export metadata as dictionary

        :returns: Metadata as dictionary
        """
        result: dict = {
            "title": self.title,
            "authors": self.authors,
            "narrators": self.narrators,
        }
        if self.language:
            result["language"] = self.language
        if self.description:
            result["description"] = self.description
        if self.isbn:
            result["isbn"] = self.isbn
        return result


    def as_json(self) -> str:
        """
        Export metadata as json

        :returns: Metadata as json
        """
        return json.dumps(self.as_dict())


def add_if_value_exists(metadata: AudiobookMetadata, l: List[Tuple[str, str]]):
    def add(key: str):
        value = getattr(metadata, key, None)
        if value:
            l.append((key, value))
    return add


@define
class Audiobook:
    session: requests.Session
    metadata: AudiobookMetadata
    files: List[AudiobookFile]
    chapters: List[Chapter] = Factory(list)
    cover: Optional[Cover] = None

    @property
    def title(self) -> str:
        return self.metadata.title

T = TypeVar("T")

@define
class BookId(Generic[T]):
    id: T

@define
class Series(Generic[T]):
    # Title of series
    title: str
    # Internal ids of book in series
    books: List[Union[BookId[T], Audiobook]]

Result = Union[
    Audiobook,
    Series
]
