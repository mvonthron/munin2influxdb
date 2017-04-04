try:
    import unittest.mock as mock
except ImportError:
    try:
        import mock
    except ImportError:
        mock = None
