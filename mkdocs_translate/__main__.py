"""To-Do entry point script."""
# message/__main__.py

import sys
from mkdocs_translate import cli, __app_name__


def main():
    print(f"[BEFORE-APP-CALL] About to call cli.app()", flush=True)
    sys.stderr.write(f"[STDERR-BEFORE-APP-CALL] About to call cli.app()\n")
    sys.stderr.flush()
    try:
        result = cli.app(prog_name=__app_name__)
        print(f"[AFTER-APP-CALL] cli.app() returned: {result}", flush=True)
        sys.stderr.write(f"[STDERR-AFTER-APP-CALL] cli.app() returned: {result}\n")
        sys.stderr.flush()
    except Exception as e:
        print(f"[EXCEPTION-IN-APP] {type(e).__name__}: {e}", flush=True)
        sys.stderr.write(f"[STDERR-EXCEPTION-IN-APP] {type(e).__name__}: {e}\n")
        sys.stderr.flush()
        raise


if __name__ == "__main__":
    main()
