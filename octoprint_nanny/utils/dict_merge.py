"""
This module bundles commonly used utility methods or helper classes that are used in multiple places within
OctoPrint's source code.

Vendored in OctoPrint-Nanny to avoid native build dependency on OctoPrint (and OctoPrint's large dependency tree) in Yocto build system
"""


__author__ = "Gina Häußge <osd@foosel.net>"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"

import copy
import pickle


def fast_deepcopy(obj):
    # the best way to implement this would be as a C module, that way we'd be able to use
    # the fast path every time.
    try:
        # implemented in C and much faster than deepcopy:
        # https://stackoverflow.com/a/29385667
        return pickle.loads(pickle.dumps(obj, pickle.HIGHEST_PROTOCOL))
    except (AttributeError, pickle.PicklingError):
        # fall back when something unpickable is found
        return copy.deepcopy(obj)


def dict_merge(a, b, leaf_merger=None, in_place=False):
    """
    Recursively deep-merges two dictionaries.
    Based on https://www.xormedia.com/recursively-merge-dictionaries-in-python/
    Example::
        >>> a = dict(foo="foo", bar="bar", fnord=dict(a=1))
        >>> b = dict(foo="other foo", fnord=dict(b=2, l=["some", "list"]))
        >>> expected = dict(foo="other foo", bar="bar", fnord=dict(a=1, b=2, l=["some", "list"]))
        >>> dict_merge(a, b) == expected
        True
        >>> dict_merge(a, None) == a
        True
        >>> dict_merge(None, b) == b
        True
        >>> dict_merge(None, None) == dict()
        True
        >>> def leaf_merger(a, b):
        ...     if isinstance(a, list) and isinstance(b, list):
        ...         return a + b
        ...     raise ValueError()
        >>> result = dict_merge(dict(l1=[3, 4], l2=[1], a="a"), dict(l1=[1, 2], l2="foo", b="b"), leaf_merger=leaf_merger)
        >>> result.get("l1") == [3, 4, 1, 2]
        True
        >>> result.get("l2") == "foo"
        True
        >>> result.get("a") == "a"
        True
        >>> result.get("b") == "b"
        True
        >>> c = dict(foo="foo")
        >>> dict_merge(c, {"bar": "bar"}) is c
        False
        >>> dict_merge(c, {"bar": "bar"}, in_place=True) is c
        True
    Arguments:
        a (dict): The dictionary to merge ``b`` into
        b (dict): The dictionary to merge into ``a``
        leaf_merger (callable): An optional callable to use to merge leaves (non-dict values)
        in_place (boolean): If set to True, a will be merged with b in place, meaning a will be modified
    Returns:
        dict: ``b`` deep-merged into ``a``
    """

    if a is None:
        a = {}
    if b is None:
        b = {}

    if not isinstance(b, dict):
        return b

    if in_place:
        result = a
    else:
        result = fast_deepcopy(a)

    for k, v in b.items():
        if k in result and isinstance(result[k], dict):
            result[k] = dict_merge(
                result[k], v, leaf_merger=leaf_merger, in_place=in_place
            )
        else:
            merged = None
            if k in result and callable(leaf_merger):
                try:
                    merged = leaf_merger(result[k], v)
                except ValueError:
                    # can't be merged by leaf merger
                    pass

            if merged is None:
                merged = fast_deepcopy(v)

            result[k] = merged
    return result
