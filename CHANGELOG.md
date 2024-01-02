# Changelog
All notable changes to this project will be documented in this file.

## [0.3.0]
- Improve Settings class:
    - Replace properties with TypedValue (seems to improve performance)
    - Improve documentation and typing
- Fix GameList.select_game method for All Games selection (was emitting a signal)
- Remove achivement sorting

## [0.2.3]
- Fix double game selection on startup (make things inconsistent and is useless)

## [0.2.2]
- Load dinamically about.py and input_dialog.py on need (better startup time)

## [0.2.1]
- Add documentation
- Fix typing
- Remove useless GameList serialisation with `pickle`

## [0.2.0]
- Add icon
- Add version in logs
- Add menu bar and About dialog

## [0.1.2]
- Add application version
- Fix file logging handler level

## [0.1.1]
- Fix application name

## [0.1.0]
- Add version command (`-v` or `--version`)
- Add debug command (`-d` or `--debug`)

## [0.0.0]
- Initial release
