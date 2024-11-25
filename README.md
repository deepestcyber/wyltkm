# Would you like to know more?
WYLTKM is a tool for generating QR-Codes. It was created for the maker space 
[Attraktor e.V.][attraktor], to make it easy to create QR-Codes that supply 
additional information about projects and workshops. Since version 0.2.0 it can also 
create QR-Codes in the style of 38c3.

The project consists of two parts: a lib-like module `generate.py` that handles the 
generation of the QR code, and a simple [Flask][flask] app, that provides a wsgi-webserver, that 
provides a form for easy generation.

* Icons used in the QR-Codes are free to use icons taken from [Font Awesome][fontawesome].
* The Attraktor Logo belongs to the [Attraktor e.V.][attraktor].
* 38c3 style and carbon icons are taken from https://events.ccc.de/congress/2024/infos/styleguide.html

Fonts used by this project are not provided with it.

[attraktor]: https://www.attraktor.org
[flask]: https://flask.palletsprojects.com
[fontawesome]: https://fontawesome.com
