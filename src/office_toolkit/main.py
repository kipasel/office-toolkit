from .bootstrap import bootstrap


def main() -> None:
    """Entry point for Office Toolkit."""
    app = bootstrap()
    app.exec()


if __name__ == "__main__":
    main()
