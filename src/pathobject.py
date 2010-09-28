# -*- coding: utf-8 -*-

"""pathobject.py - A utility class for operating on pathnames."""

import codecs
import fnmatch
import glob
import hashlib
import os
import shutil
import sys
import warnings

__all__ = ["Path"]
__version__ = "0.0.1"


## Some functional utilities to save code later on.

def update_wrapper(wrapper, wrapped):
    """Update a wrapper function to look like the wrapped function."""

    for attr in ('__module__', '__name__', '__doc__'):
        value = getattr(wrapped, attr, None)
        if value:
            setattr(wrapper, attr, value)
    wrapper.__dict__.update(getattr(wrapped, '__dict__', {}))
    return wrapper


def wrap(function, doc=None):
    """Wrap a basic `os.path` function to return `Path` instances."""

    def method(self, *args, **kwargs):
        return type(self)(function(self, *args, **kwargs))
    method = update_wrapper(method, function)
    if doc:
        method.__doc__ = doc
    return method


def pmethod(name):
    """Return a proxy method to a named function on the current path module."""

    return lambda self, *a, **kw: getattr(self._path, name)(self, *a, **kw)


def defined_if(predicate):

    """
    Declare a method as only defined if `self` meets a given predicate.

        >>> class Test(object):
        ...     x = defined_if(lambda self: True)(lambda self: 1)
        ...     y = defined_if(lambda self: False)(lambda self: 1)

        >>> Test().x()
        1

        >>> Test().y  # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        AttributeError: <lambda> not defined for <pathobject.Test object at 0x...>

    """

    def decorator(method):
        def wrapper(self):
            if not predicate(self):
                raise AttributeError("%s not defined for %r" % (method.__name__, self))

            def function(*args, **kwargs):
                return method(self, *args, **kwargs)
            return update_wrapper(function, method)
        return property(wrapper)
    return decorator


class Path(unicode):

    """A utility class for operating on pathnames."""

    _path = os.path

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, unicode.__repr__(self))

    __add__ = wrap(lambda self, other: unicode(self) + other)
    __radd__ = wrap(lambda self, other: other + self)
    __div__ = wrap(pmethod('join'), "Shortcut for `os.path.join()`.")
    __truediv__ = __div__

    # @classmethod
    def cwd(cls):
        """Return the current working directory as a `Path`."""

        return cls(os.getcwdu())
    cwd = classmethod(cwd)

    # @classmethod
    def for_path_module(cls, pathmod, name=None):

        """
        Return a `Path` class for the given path module.

        This allows you to use `Path` to perform NT path manipulation on UNIX
        machines and vice versa.

        Example:

            >>> import ntpath
            >>> NTPath = Path.for_path_module(ntpath, name="NTPath")
            >>> NTPath(u'C:\\\\A\\\\B\\\\C').splitdrive()
            (NTPath(u'C:'), u'\\\\A\\\\B\\\\C')
        """

        if name is None:
            name = cls.__name__

        return type(name, (cls,), {'_path': pathmod})
    for_path_module = classmethod(for_path_module)

    # Simple proxy methods or properties.

    is_absolute = pmethod('isabs')
    absolute = wrap(pmethod('abspath'))
    normcase = wrap(pmethod('normcase'))
    normalize = wrap(pmethod('normpath'))
    realpath = wrap(pmethod('realpath'))
    joinpath = wrap(pmethod('join'))
    expanduser = wrap(pmethod('expanduser'))
    expandvars = wrap(pmethod('expandvars'))
    dirname = wrap(pmethod('dirname'))
    basename = pmethod('basename')

    parent = property(dirname, None, None,
        """Property synonym for `os.path.dirname()`.

        Example:

            >>> Path('/usr/local/lib/libpython.so').parent
            Path(u'/usr/local/lib')

        """)

    name = property(basename, None, None,
        """Property synonym for `os.path.basename()`.

        Example:

            >>> Path('/usr/local/lib/libpython.so').name
            u'libpython.so'

        """)

    ext = property(lambda self: self._path.splitext(self)[1], None, None,
        """Return the file extension (e.g. '.py').""")

    drive = property(lambda self: self._path.splitdrive(self)[0], None, None,
        """Return the drive specifier (e.g. "C:").""")

    def splitpath(self):

        """
        Return `(p.parent, p.name)`.

        Example:

            >>> Path('/usr/local/lib/libpython.so').splitpath()
            (Path(u'/usr/local/lib'), u'libpython.so')

        """

        parent, child = self._path.split(self)
        return type(self)(parent), child

    def splitdrive(self):

        """
        Return `(p.drive, <the rest of p>)`.

        If there is no drive specifier, `p.drive` is empty (as is always the
        case on UNIX), so the result will just be `(Path(u''), u'')`.

        Example:

            >>> import ntpath
            >>> import posixpath

            >>> Path.for_path_module(ntpath)('C:\\\\A\\\\B\\\\C').splitdrive()
            (Path(u'C:'), u'\\\\A\\\\B\\\\C')

            >>> Path.for_path_module(posixpath)('/a/b/c').splitdrive()
            (Path(u''), u'/a/b/c')

        """

        drive, rel = self._path.splitdrive(unicode(self))
        return type(self)(drive), rel

    def splitext(self):

        """
        Return `(<base filename>, extension)`.

        Splits the filename on the last `.` character, and returns both pieces.
        The extension is prefixed with the `.`, so that the following holds:

            >>> p = Path('/some/path/to/a/file.txt.gz')
            >>> a, b = p.splitext()
            >>> a + b == p
            True

        Example:

            >>> Path('/home/zack/filename.tar.gz').splitext()
            (Path(u'/home/zack/filename.tar'), u'.gz')

        """

        filename, extension = self._path.splitext(self)
        return type(self)(filename), extension

    def stripext(self):

        """
        Remove one file extension from the path.

        Example:

            >>> Path('/home/guido/python.tar.gz').stripext()
            Path(u'/home/guido/python.tar')

        """

        return self.splitext()[0]

    # @defined_if(lambda self: hasattr(self._path, 'splitunc'))
    def splitunc(self):
        unc, rest = self._path.splitunc(self)
        return type(self)(unc), rest
    splitunc = defined_if(lambda self: hasattr(self._path, 'splitunc'))(splitunc)

    uncshare = property(lambda self: self.splitunc()[0], None, None,
        """The UNC mount point for this path. Empty for paths on local drives.""")

    def splitall(self):

        """
        Return a list of the path components in this path.

        The first item in the list will be a `Path`. Its value will be either
        `path.curdir`, `path.pardir`, empty, or the root directory of this path
        (e.g. `'/'` or `'C:\\'`). The other items in the list will be strings.

        By definition, `result[0].joinpath(*result[1:])` will yield the original
        path.

            >>> p = Path(u'/home/guido/python.tar.gz')
            >>> parts = p.splitall()
            >>> parts
            [Path(u'/'), u'home', u'guido', u'python.tar.gz']

            >>> parts[0].joinpath(*parts[1:])
            Path(u'/home/guido/python.tar.gz')

        """

        parts = []
        location = self
        while location not in (self._path.curdir, self._path.pardir):
            previous = location
            location, child = previous.splitpath()
            if location == previous:
                break
            parts.append(child)
        parts.append(location)
        parts.reverse()
        return parts

    def relpath(self):
        """Return the relative path from the current directory to this path."""

        return self.relpathfrom(self.cwd())

    def relpathfrom(self, origin):

        """
        Return a relative path from a given origin to this one.

        This is a simple wrapper over `relpathto()`.
        """

        return type(self)(origin).relpathto(self)

    def relpathto(self, destination):

        """
        Return a relative path from this one to a given destination.

        If no relative path exists (e.g. if they reside on different drives on
        Windows), this will return `destination.absolute()`.

            >>> Path(u'/a/b/c').relpathto('/a/d/e')
            Path(u'../../d/e')

        """

        origin = self.absolute()
        destination = type(self)(destination).absolute()

        orig_list = origin.normcase().splitall()
        dest_list = destination.splitall()

        if orig_list[0] != self._path.normcase(dest_list[0]):
            # No relative path exists.
            return destination

        # Find the location where the two paths diverge.
        common_index = 0
        for orig_part, dest_part in zip(orig_list, dest_list):
            if orig_part != self._path.normcase(dest_part):
                break
            common_index += 1

        # A certain number of pardirs are required to work up from the origin to
        # the point of divergence.
        segments = [self._path.pardir] * (len(orig_list) - common_index)
        segments += dest_list[common_index:]
        if not segments:
            # The paths are identical; return '.' (or equivalent).
            return type(self)(self._path.curdir)
        return type(self)(self._path.join(*segments))

    def fnmatch(self, pattern):
        """Return `True` if `self.name` matches the given glob pattern."""

        return fnmatch.fnmatch(self.name, pattern)

    ## Reading and Writing.

    def open(self, mode='r', bufsize=None):
        if bufsize is not None:
            return open(self, mode, bufsize)
        return open(self, mode)

    def bytes(self):
        """Read the contents of this file as a bytestring."""

        fp = self.open(mode='rb')
        try:
            return fp.read()
        finally:
            fp.close()

    def write_bytes(self, bytes, append=False):

        """
        Open this file and write the given bytes to it.

        The default behavior is to truncate any existing file. Use `append=True`
        to append instead.
        """

        fp = self.open(mode=(append and 'ab' or 'wb'))
        try:
            fp.write(bytes)
        finally:
            fp.close()

    def text(self, encoding=None, errors='strict'):

        """
        Read the contents of this file as text.

        Universal newline mode is used where available, so <CR><LF> and <CR>
        line endings are translated to <LF>.

        Pass `encoding` to decode the contents of the file using the given
        character set, returning a Unicode string. Without this argument, the
        text is returned as a bytestring.

        The `errors` keyword argument will be passed as-is to the decoder (see
        `help(str.decode)` for details). The default value is `'strict'`.
        """

        if encoding is None:
            fp = self.open(mode=(hasattr(file, 'newlines') and 'U' or 'r'))
            try:
                return fp.read()
            finally:
                fp.close()

        fp = codecs.open(self, 'r', encoding, errors)
        try:
            text = fp.read()
        finally:
            fp.close()

        # Universal newline mode isn't supported by `codecs.open()`, so we have
        # to perform the replacement manually.
        return (text.replace(u'\r\n', u'\n')
                    .replace(u'\r\x85', u'\n')
                    .replace(u'\r', u'\n')
                    .replace(u'\x85', u'\n')
                    .replace(u'\u2028', u'\n'))

    def write_text(self, text, encoding=None, errors='strict', linesep=os.linesep, append=False):

        """
        Write the given text to this file.

        There are two differences between `write_text()` and `write_bytes()`:
        newline handling and Unicode handling.

        The default behavior is to truncate any existing file. Use `append=True`
        to append instead.

        If `text` is a Unicode string, the `encoding` and `errors` parameters
        will be used to encode it to a bytestring. In this case, `encoding`
        defaults to `sys.getdefaultencoding()`. If `text` is already a
        bytestring, no encoding occurs, and passing a value for `encoding` will
        raise an `AssertionError`.

        By default, `write_text()` will normalize line endings to `os.linesep`.
        You can customize this by passing a `linesep` keyword argument. If
        `linesep` is `None`, the line endings will be left as-is.
        """

        if isinstance(text, unicode):
            if linesep is not None:
                # Convert all standard end-of-line sequences to
                # ordinary newline characters.
                text = (text.replace(u'\r\n', u'\n')
                            .replace(u'\r\x85', u'\n')
                            .replace(u'\r', u'\n')
                            .replace(u'\x85', u'\n')
                            .replace(u'\u2028', u'\n'))
                text = text.replace(u'\n', linesep)
            if encoding is None:
                encoding = sys.getdefaultencoding()
            bytes = text.encode(encoding, errors)
        else:
            assert encoding is None, "Passed an encoding for a bytestring."

            if linesep is not None:
                text = (text.replace('\r\n', '\n')
                            .replace('\r', '\n'))
                bytes = text.replace('\n', linesep)

        self.write_bytes(bytes, append=append)
