# pathobject

The aim of this library is to provide an `easy_install`-able update of Jason
Orendorff’s [path](http://pypi.python.org/pypi/path.py) library, free from
deprecation warnings and compatible with Python 2.3+.

Another major goal of this library is to be path module-agnostic. Using a
different path module is quite simple:

    >>> from pathobject import Path
    >>> import ntpath
    >>> import posixpath
    
    >>> POSIXPath = Path.for_path_module(posixpath, name='POSIXPath')
    >>> POSIXPath('/a/b/c').splitall()
    [POSIXPath(u'/'), u'a', u'b', u'c']
    
    >>> NTPath = Path.for_path_module(ntpath, name='NTPath')
    >>> NTPath(u'C:\\Documents and Settings\\Zack').splitdrive()
    (NTPath(u'C:'), u'\\Documents and Settings\\Zack')
    
The benefit of this is that you can manipulate Windows paths from a UNIX system,
and vice versa—something simple reliance on `os.path` doesn’t allow.


## (Un)license

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this
software, either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this
software dedicate any and all copyright interest in the software to the public
domain. We make this dedication for the benefit of the public at large and to
the detriment of our heirs and successors. We intend this dedication to be an
overt act of relinquishment in perpetuity of all present and future rights to
this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
