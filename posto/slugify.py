# -*- coding: utf-8 -*-

# Original project https://github.com/zacharyvoase/slugify

"""A generic slugifier utility (currently only for Latin-based scripts)."""

import re
import unicodedata

__version__ = '0.0.1'


def slugify(string):

    """
    Slugify a unicode string.

    Example:

        >>> slugify(u"Héllø Wörld")
        u"hello-world"

    """

    return re.sub(r'[-\s]+', '_', re.sub(r'[^\._\w\s-]', '',                unicodedata.normalize('NFKD', string).encode('ascii', 'ignore').decode("ascii")).strip().lower())
