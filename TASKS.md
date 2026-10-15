# TASKS

## Done (1.0.3 preparation)

- Fixed `minimumNVDAVersion` from 2024.1.0 to 2024.2.0 (the
  `speech.extensions.filter_speechSequence` extension point was introduced in NVDA
  2024.2; the add-on did not work on 2024.1).
- Set `lastTestedNVDAVersion` to 2026.2.
- Added the `changelog` field to `buildVars.py` and the manifest templates.
- Fixed translation terminology to match NVDA ("Automatic language switching") for
  de, it and zh_CN; aligned PO headers; added the changelog string; stopped
  translating the add-on name.
- Added Crowdin integration (`.github/workflows/crowdinL10n.yml` and
  `.github/scripts/`) plus `pyproject.toml` and `.python-version`.
- Updated `CLAUDE.md` and `readme.md` to match the current architecture.

## Running

- Cut the 1.0.3 release (tag, GitHub release with the `.nvda-addon` asset).
- Submit 1.0.3 to the NVDA Add-on Store (addon-datastore registration form, channel
  stable, licence GPL v2). Watch the validation PR.

## Open / follow-up

- Crowdin: create a Crowdin account, request developer access to
  `crowdin.com/project/nvdaaddons` (nvda-translations@groups.io or
  nvda-addons@groups.io), generate a scoped API token and add it as the
  `CROWDIN_TOKEN` repository secret. Optionally set `MIN_PERCENTAGE_TRANSLATED`.
- Consider migrating the build system to the current NVDA addonTemplate
  (`site_scons/site_tools/NVDATool`) so the build matches upstream.
- Check whether VirusTotal flags the unsigned bundled `.pyd` files and be ready to
  explain a false positive during store validation.
- Licensing: the bundled `lid.176.ftz` model is CC-BY-SA 3.0 while the add-on is
  GPL-2.0; keep the attribution in `readme.md` / `NOTICE.MD` and review if required.
- Verify the add-on on NVDA 2026.2 before relying on `lastTestedNVDAVersion = 2026.2`.
