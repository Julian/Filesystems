from __future__ import absolute_import
from unittest import TestCase, skipIf

try:
    import click.testing
except ImportError:
    click = None
else:
    from filesystems import Path
    import filesystems.click


@skipIf(click is None, "Click support not present.")
class TestClick(TestCase):
    def test_path(self):
        path = parse(type=filesystems.click.PATH, value="some/path/provided")
        self.assertEqual(path, Path.from_string("some/path/provided"))


def parse(type, value):
    """
    Invoke a ``ParamType`` to convert a value in integration.

    No idea if there's a simpler way to do this.
    """

    result = []

    @click.command()
    @click.argument("converted", type=type)
    def main(converted):
        result.append(converted)

    click.testing.CliRunner().invoke(main, args=(value,))

    if len(result) != 1:
        raise Exception("Did not produce one value, this shouldn't happen.")
    return result[0]
