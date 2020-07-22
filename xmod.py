r"""
🌱 - xmod: Extend a module with any Python object - 🌱
=========================================================================

Give your module the awesome power of an object, or maybe just save a
little typing, with ``xmod``.

Ever wanted to call a module directly, or index it?
Or just sick of seeing ``from foo import foo`` in your examples?

``xmod`` is a tiny library that solves both these issues in one line of code,
by extending a module with the methods and members of a Python object.

This is extremely handy for modules that primarily do one thing.

EXAMPLE: Make a module callable like a function

.. code-block:: python

    # In your_module.py
    import xmod

    A_CONSTANT = 23

    @xmod
    def a_function(*args, **kwargs):
        print('a function!')
        return args, kwargs


    # Test at the command line
    >>> import your_module

    >>> your_module(2, 3, a=5)
    a function!
    (2, 3), {'a': 5}

    >>> assert your_module.A_CONSTANT == 23

EXAMPLE: Make a module look like an object

.. code-block:: python

    # In your_module.py
    import xmod

    A_CONSTANT = 23

    xmod(list(), __name__)

    # Test at the command line
    >>> import your_module

    >>> assert your_module == [] and your_module.A_CONSTANT == 23

    >>> your_module.extend(range(3))

    >>> print(your_module)
    [0, 1, 2]
"""

__all__ = ('xmod',)

import functools
import sys

__version__ = '1.0.1'

MODULE_PROPERTIES = {
    '__all__',
    '__cached__',
    '__doc__',
    '__file__',
    '__loader__',
    '__name__',
    '__package__',
    '__path__',
    '__spec__',
}

OMIT = {
    '__class__',
    '__getattr__',
    '__getattribute__',
    '__init__',
    '__init_subclass__',
    '__new__',
    '__setattr__',
}

EXTENSION_ATTRIBUTE = '_xmod_extension'
WRAPPED_ATTRIBUTE = '_xmod_wrapped'


def xmod(extension=None, name=None, properties=None, omit=None):
    """
    Extend the system module at ``name`` with any Python object.

    The original module is replaced in ``sys.modules`` by a proxy class
    which delegates attributes, first to the extension, and then to the
    original module.

    ``xmod`` can also be used as a decorator, both with and without
    parameters.

    ARGUMENTS
      extension
        The object whose methods and properties extend the namespace.
        This includes magic methods like __call__ and __getitem__.

      name
        The name of this symbol in ``sys.modules``.  If this is ``None``
        then ``xmod`` will use ``extension.__module__``.

        This only needs to be be set if ``extension`` is _not_ a function or
        class defined in the module that's being extended.

        If the ``name`` argument is given, it should almost certainly be
        ``__name__``.

      properties
        There is little need to use this argument.

        Properties in this list are copied directly from the module into the
        custom class - they do not get overridden by the extension.

        If ``properties`` is None, it defaults to ``xmod.MODULE_PROPERTIES``
        which seems to work well.

      omit
        There is little need to use this argument.

        A list of methods _not_ to delegate from the proxy to the extension.
        if ``omit`` is None, it defaults to ``xmod.OMIT``, which seems to work
        well.
    """
    if extension is None:
        # It's a decorator with properties
        assert name is not None or omit is not None or properties is not None
        return functools.partial(
            xmod, name=name, properties=properties, omit=omit
        )

    name = extension.__module__ if name is None else name
    properties = MODULE_PROPERTIES if properties is None else properties
    omit = OMIT if omit is None else omit

    original = sys.modules[name]
    members = {EXTENSION_ATTRIBUTE: extension, WRAPPED_ATTRIBUTE: original}

    def method(f):
        @functools.wraps(f)
        def wrapped(self, *args, **kwargs):
            return f(*args, **kwargs)

        return wrapped

    is_type = isinstance(extension, type)
    for attr in dir(extension):
        if attr not in omit:
            value = getattr(extension, attr)
            if not callable(value):
                members[attr] = value
            elif not is_type:
                members[attr] = method(value)

    if callable(extension):
        members['__call__'] = method(extension)

    members['__getattr__'] = method(original.__getattribute__)
    members['__setattr__'] = method(original.__setattr__)

    none = object()
    for k in properties:
        v = getattr(original, k, none)
        if v is not none:
            members[k] = v

    proxy_class = type(name, (object,), members)
    sys.modules[name] = proxy_class()
    return extension


xmod(xmod)
