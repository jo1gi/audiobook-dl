from audiobookdl.sources.storytel import StorytelSource

def test_parse_url():
    book_id = StorytelSource.get_book_id("https://www.storytel.com/se/sv/books/shantaram-1404854")
    assert book_id == "1404854"

def test_parse_url_with_params():
    book_id = StorytelSource.get_book_id("https://www.storytel.com/se/sv/books/shantaram-1404854?appRedirect=true")
    assert book_id == "1404854"


