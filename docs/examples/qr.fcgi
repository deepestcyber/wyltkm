#!/srv/wyltkm/venv/bin/python
"""FastCGI entry point for the WYLTKM web app (Apache with mod_fcgid or
mod_fastcgi). The shebang points to the Python of the app's venv; see
docs/web.md, "Apache with FastCGI"."""

import os

# set here: with mod_fcgid, SetEnv in .htaccess often does not reach the process
os.environ.setdefault("WYLTKM_CONFIG", "/srv/wyltkm/config.toml")

from flup.server.fcgi import WSGIServer  # noqa: E402

from wyltkm.web import create_app  # noqa: E402

if __name__ == "__main__":
    WSGIServer(create_app()).run()
