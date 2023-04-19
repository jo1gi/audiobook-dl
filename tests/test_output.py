from audiobookdl import AudiobookMetadata
from audiobookdl.output.output import gen_output_location
from audiobookdl.output.download import get_output_audio_format

TEST_DATA = [
    {
        "template": "{author} - {title}",
        "metadata": AudiobookMetadata("The Way of Kings", authors = ["Brandon Sanderson"]),
        "remove_chars": "",
        "output": "Brandon Sanderson - The Way of Kings"
    },
    {
        "template": "{title}",
        "metadata": AudiobookMetadata("The Deal of a Lifetime: A Novella"),
        "remove_chars": ":,.",
        "output": "The Deal of a Lifetime A Novella",
    }
]

def test_gen_output_location():
    for test in TEST_DATA:
        assert gen_output_location(test["template"], test["metadata"], test["remove_chars"]) == test["output"]


def test_gen_output_audio_format_with_option():
    assert get_output_audio_format("m4b", ["file1.mp3","file2.mp3","file3.mp3"]) == ("mp3","m4b")


def test_gen_output_audio_format_without_option():
    assert get_output_audio_format(None, ["file1.mp3","file2.mp3","file3.mp3"]) == ("mp3", "mp3")
