from audiobookdl import AudiobookMetadata
from audiobookdl.output.output import gen_output_location

TEST_DATA = [
    {
        "template": "{author} - {title}",
        "metadata": {"title": "The Way of Kings", "author": "Brandon Sanderson"},
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
