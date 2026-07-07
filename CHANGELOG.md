# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

# [0.3.0]

### Added

- Option to add attached files to Digital Shipments.
- API endpoint to get attached files from a shipment.

### Changed

- Updated nginx configuration.
- Made Memo Label optional for Fjernpost.
- Made shipment order of letters stable to ensure proper caching.

## [0.2.0]

### Added

- Shipments can now be sent as physical mail (Fysisk Post) or as Digital Post with physical fallback.

### Fixed

- Added error handling on syntax errors in templates.
- Bumped nginx max file size to 10mb.

## [0.1.0]

### Added

- Changelog!
- PR workflows.
- Version number in UI.
- Letters can now be sent to CVR-numbers.

### Fixed

- Refactored send_post.py and fixed minor issues.

### Changed

- Changed API auth flow to JWT based auth.
- Updated docker file to use uv.lock.
- Bumped dependencies.

## [0.0.1]

- Initial release

[Unreleased]: https://github.com/itk-dev-rpa/OpenPostbud/compare/0.3.0...HEAD
[0.3.0]: https://github.com/itk-dev-rpa/OpenPostbud/releases/tag/0.3.0
[0.2.0]: https://github.com/itk-dev-rpa/OpenPostbud/releases/tag/0.2.0
[0.1.0]: https://github.com/itk-dev-rpa/OpenPostbud/releases/tag/0.1.0
[0.0.1]: https://github.com/itk-dev-rpa/OpenPostbud/releases/tag/0.0.1
