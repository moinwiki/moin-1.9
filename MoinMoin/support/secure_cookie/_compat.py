import sys

PY2 = sys.version_info[0] == 2
_default_encoding = sys.getdefaultencoding()

if not PY2:
    text_type = str

    def to_bytes(x, charset=_default_encoding, errors="strict"):
        if x is None:
            return None

        if isinstance(x, (bytes, bytearray, memoryview)):
            return bytes(x)

        if isinstance(x, str):
            return x.encode(charset, errors)

        raise TypeError("Expected bytes")

    def to_native(x, charset=_default_encoding, errors="strict"):
        if x is None or isinstance(x, str):
            return x

        return x.decode(charset, errors)


else:
    text_type = unicode  # noqa: F821

    def to_bytes(x, encoding=_default_encoding, errors="strict"):
        if x is None:
            return None

        if isinstance(x, (bytes, bytearray, buffer)):  # noqa: F821
            return bytes(x)

        if isinstance(x, unicode):  # noqa: F821
            return x.encode(encoding, errors)

        raise TypeError("Expected bytes")

    def to_native(x, encoding=_default_encoding, errors="strict"):
        if x is None or isinstance(x, str):
            return x

        return x.encode(encoding, errors)
