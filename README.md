# Calibrator

Calibrator is a tool to repair the library file managed by [Calibre], the ebook management software.

Specifically, it caters to users who maintain their ebook library in a git repo, and need help repairing the sqlite database when copies of the repo have diverged.

The tool automatically adds any files present in the library directory which are not tracked by calibre's `metadata.db` database.

## Usage
```
$ calibrator
```

## Dependencies
* python2
* calibre - the `calibredb` CLI tool available in your PATH
* calibre >= 2.74 (this tool requires [PR])

## Caveats
* calibrator supports re-adding missing books and formats of existing books. It does not support adding missing authors, although this should be easy
* calibrator does not clean up directories in /tmp - this would require changes to `calibredb` to set exit codes on error conditions

## Contributing
This functionality would be better if it were integrated into `calibredb` itself. PRs accepted, but with that caveat.

Please make `./dolint` pass before filing PRs.



[PR]: <https://github.com/kovidgoyal/calibre/pull/593>
[Calibre]: <https://calibre-ebook.com>
