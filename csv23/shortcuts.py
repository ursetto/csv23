# shortcuts.py - overloaded functions (Python 3 only)

import functools
import io
import itertools
import sys

from . import (DIALECT,
               ENCODING,
               reader as csv23_reader,
               writer as csv23_writer)

__all__ = ['read_csv', 'write_csv']


def iterslices(iterable, size):
    iterable = iter(iterable)
    next_slice = functools.partial(itertools.islice, iterable, size)
    return iter(lambda: list(next_slice()), [])


def read_csv(filename, dialect=DIALECT, encoding=ENCODING):
    raise NotImplementedError


if sys.version_info.major == 2:
    def write_csv(filename, rows, header=None, dialect=DIALECT,
                  encoding=ENCODING):
        raise NotImplementedError('Python 3 only')
    
else:
    import pathlib

    if sys.version_info < (3, 7):
        import contextlib

        @contextlib.contextmanager
        def nullcontext(enter_result=None):
            yield enter_result

    else:
        from contextlib import nullcontext

    def iterrows(f, dialect=DIALECT):
        with f as _f:
            reader = csv23_reader(_f, dialect=dialect, encoding=False)
            for row in reader:
                yield row

    def read_csv(filename, dialect=DIALECT, encoding=ENCODING, as_list=False):
        open_kwargs = {'encoding': encoding, 'newline': ''}
        textio_kwargs = dict(write_through=True, **open_kwargs)

        if hasattr(filename, 'read'):
            if isinstance(filename, io.TextIOBase):
                if encoding is not None:
                    raise TypeError('bytes-like object expected')
                f = filename
            else:
                if encoding is None:
                     raise TypeError('need encoding for wrapping byte-stream')
                f = io.TextIOWrapper(filename, **textio_kwargs)
            f = nullcontext(f)
        else:
            if encoding is None:
                raise TypeError('need encoding for opening file by path')
            f = open(str(filename), 'rt', **open_kwargs)

        rows = iterrows(f, dialect=dialect)
        if as_list:
            rows = list(rows)
        return rows


    def write_csv(filename, rows, header=None, dialect=DIALECT,
                  encoding=ENCODING):
        open_kwargs = {'encoding': encoding, 'newline': ''}
        textio_kwargs = dict(write_through=True, **open_kwargs)

        if filename is None:
            if encoding is None:
                f = io.StringIO()
            else:
                f = io.TextIOWrapper(io.BytesIO(), **textio_kwargs)
        elif hasattr(filename, 'write'):
            result = filename
            if encoding is None:
                f = filename
            else:
                f = io.TextIOWrapper(filename, **textio_kwargs)
            f = nullcontext(f)
        elif hasattr(filename, 'hexdigest'):
            result = filename
            if encoding is None:
                raise TypeError('need encoding for wrapping byte-stream')
            f = io.TextIOWrapper(io.BytesIO(), **textio_kwargs)
            hash_ = filename
        else:
            result = pathlib.Path(filename)
            if encoding is None:
                raise TypeError('need encoding for opening file by path')
            f = open(str(filename), 'wt', **open_kwargs)

        with f as f:
            writer = csv23_writer(f, dialect=dialect, encoding=False)

            if header is not None:
                writer.writerows([header])

            if hasattr(filename, 'hexdigest'):
                buf = f.buffer
                for rows in iterslices(rows, 1000):
                    writer.writerows(rows)
                    hash_.update(buf.getbuffer())
                    # NOTE: f.truncate(0) would prepend zero-bytes
                    f.seek(0)
                    f.truncate()
            else:
                writer.writerows(rows)

            if filename is None:
                if encoding is not None:
                    f = f.buffer
                result = f.getvalue()

        if hasattr(filename, 'write') and encoding is not None:
            f.detach()

        return result
