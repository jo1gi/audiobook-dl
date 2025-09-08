from audiobookdl.sources import find_compatible_source

TEST_DATA = {
    "https://www.audiobooks.com/book/stream/413879": "Audiobooksdotcom",
    "https://www.audiobooks.com/browse/library": "Audiobooksdotcom",
    "https://www.bookbeat.no/bok/somethingsomething-999999": "BookBeat",
    "https://ereolen.dk/ting/object/870970-basis%3A53978223": "Ereolen",
    "https://www.everand.com/listen/579426746": "Everand",
    "https://www.chirpbooks.com/player/11435746": "Chirp",
    "https://librivox.org/library-of-the-worlds-best-literature-ancient-and-modern-volume-3-by-various/": "Librivox",
    "https://www.nextory.no/bok/somethingsomethingsomething-99999999/": "Nextory",
    "https://ofs-d2b6150a9dec641552f953da2637d146.listen.overdrive.com/?d=...": "Overdrive",
    "https://www.scribd.com/listen/579426746": "Everand",
    "https://www.storytel.com/no/nn/books/somethingsomething-9999999": "Storytel",
}

def test_url_to_source():
    for url, source_name in TEST_DATA.items():
        source = find_compatible_source(url)
        assert source.__name__ == source_name + "Source"
