try:
    import dateparser
    from dateparser.search import search_dates
    print("DATEPARSER_OK")
except ImportError:
    print("DATEPARSER_MISSING")
