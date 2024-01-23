from datetime import date
import requests
from typing import Dict, Generic, List, Optional, Union, Sequence, Tuple, TypeVar, Any
import json
from attrs import define, Factory
import pycountry


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
    # Expected content-type of the download request
    expected_content_type: Optional[str] = None
    # Expected status code of the download request
    expected_status_code: Optional[int] = None


@define
class AudiobookMetadata:
    title: str
    scrape_url: Optional[str] = None
    series: Optional[str] = None
    series_order: Optional[int] = None
    authors: List[str] = Factory(list)
    narrators: List[str] = Factory(list)
    genres: List[str] = Factory(list)
    language: Optional["pycountry.db.Language"] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    release_date: Optional[date] = None

    def add_author(self, author: str):
        """Add author to metadata"""
        self.authors.append(author)

    def add_narrator(self, narrator: str):
        """Add narrator to metadata"""
        self.narrators.append(narrator)

    def add_genre(self, genre: str):
        """Add genre to metadata"""
        self.genres.append(genre)

    def add_authors(self, authors: Sequence[str]):
        self.authors.extend(authors)

    def add_narrators(self, narrators: Sequence[str]):
        self.narrators.extend(narrators)

    def add_genres(self, genres: Sequence[str]):
        self.genres.extend(genres)

    def all_properties(self, allow_duplicate_keys = False) -> List[Tuple[str, Any]]:
        result: List[Tuple[str, str]] = []
        add = add_if_value_exists(self, result)
        add("title")
        add("scrape_url")
        add("series")
        add("series_order")
        add("language")
        add("description")
        add("isbn")
        add("publisher")
        add("release_date")
        if allow_duplicate_keys == None: # return original lists
            add("authors")
            add("narrators")
            add("genres")
        elif allow_duplicate_keys == True: # return lists as multiple keys
            for author in self.authors:
                result.append(("author", author))
            for narrator in self.narrators:
                result.append(("narrator", narrator))
            for genre in self.genres:
                result.append(("genre", genre))
        else: # return lists concatenated into a string
            result.append(("author", self.author))
            result.append(("narrator", self.narrator))
            result.append(("genre", self.genre))
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

    @property
    def genre(self) -> str:
        """All genres concatenated into a single string"""
        return "; ".join(self.genres)


    def as_dict(self) -> dict:
        """
        Export metadata as dictionary

        :returns: Metadata as dictionary
        """
        result: dict = {
            "title": self.title,
            "authors": self.authors,
            "narrators": self.narrators,
            "genres": self.genres,
        }
        if self.scrape_url:
            result["scrape_url"] = self.scrape_url
        if self.series:
            result["series"] = self.series
        if self.series_order:
            result["series_order"] = self.series_order
        if self.language:
            result["language"] = self.language
        if self.description:
            result["description"] = self.description
        if self.isbn:
            result["isbn"] = self.isbn
        if self.publisher:
            result["publisher"] = self.publisher
        if self.release_date:
            result["release_date"] = self.release_date

        return result


    def as_json(self) -> str:
        """
        Export metadata as json

        :returns: Metadata as json
        """
        class AudiobookMetadataJSONEncoder(json.JSONEncoder):
            def default(self, z):
                if isinstance(z, date):
                    return str(z)
                elif isinstance(z, pycountry.db.Data) and z.__class__.__name__ == "Language":
                    return z.alpha_3
                else:
                    return super().default(z)
        return json.dumps(self.as_dict(), cls=AudiobookMetadataJSONEncoder)


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
