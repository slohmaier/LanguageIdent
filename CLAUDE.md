# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```powershell
# Requires gettext (msgfmt/xgettext) in PATH - install via: winget install GnuWin32.GetText
# Then add to PATH: $env:PATH += ";C:\Program Files (x86)\GnuWin32\bin"
# The repo also bundles msgfmt.exe and xgettext.exe in the root for convenience.

# Build the addon (creates LangDetectSpeech-X.Y.Z.nvda-addon)
scons

# Build with a specific version
scons version=0.5.0

# Build a development version (adds a date stamp)
scons dev=1

# Build and install directly to the NVDA addons folder (requires NVDA restart)
scons install

# Generate the translation template (LangDetectSpeech.pot)
scons pot

# Merge the POT into the existing PO files (requires msgmerge in PATH)
scons updatePo

# Run linting
flake8 addon/globalPlugins/LangDetectSpeech.py
```

## Architecture Overview

LangDetectSpeech is a lightweight NVDA add-on that automatically detects the language
of spoken text and switches to the appropriate synthesizer voice. It uses a vendored
copy of fast-langdetect (FastText-based) for offline language detection across 176
languages.

### Core Components

**`addon/globalPlugins/LangDetectSpeech.py`** - Main entry point.
- `GlobalPlugin.__init__` - registers the speech sequence filter, adds the settings
  panel, and hooks `core.postNvdaStartup` to warn if automatic language switching is
  disabled.
- `speechSequenceFilter(speechSequence)` - the `speech.extensions.filter_speechSequence`
  handler. It collects the text, calls `detectLanguage`, and prepends a single
  `LangChangeCommand` for the detected language (existing `LangChangeCommand`s are
  stripped).
- `detectLanguage(text)` - runs the detector, picks the first candidate that is in the
  whitelist and supported by the current synthesizer, applies the fallback, and
  returns a language suitable for `synthDriverHandler`.
- `updateSynthLangs()` - caches the voices/languages reported by the current
  synthesizer and initializes the whitelist when the synthesizer changes.
- `LangDetectSpeechSettings` - settings panel with one checkbox per synthesizer
  language and a fallback language choice.

**`addon/globalPlugins/fast_langdetect/`** - Bundled language detection library
(vendored subset of fast-langdetect 1.0.x, MIT).
- `infer.py` - `LangDetector` class using the bundled FastText lite model.
- `fasttext/` - FastText Python wrapper (MIT, Facebook).
- `fasttext_pybind.cp311-win32.pyd` - Compiled FastText binary (Python 3.11, 32-bit,
  NVDA 2024.2 up to 2025.x).
- `fasttext_pybind.cp313-win_amd64.pyd` - Compiled FastText binary (Python 3.13,
  64-bit, NVDA 2026.1+).
- `resources/lid.176.ftz` - Bundled lite model (~1 MB, 176 languages, CC-BY-SA 3.0).

### Data Flow

```
speech.speak() called
    ↓ [filter_speechSequence extension point]
speechSequenceFilter(speechSequence)
    ↓
updateSynthLangs() → detectLanguage(text) → LangDetector.detect()
    ↓
[LangChangeCommand(detectedLang)] + speechSequence (LangChangeCommands stripped)
    ↓
NVDA speaks with the detected language voice
```

### Configuration

Stored in NVDA config under `[LangDetectSpeech]`:
- `whitelist` - comma-separated list of languages considered for detection
  (auto-populated with the synthesizer languages).
- `fallback` - language used when the detected language is not supported (default "en").

### Key Global Variables (LangDetectSpeech.py)

- `synthClass` - cached synthesizer class, used to detect synthesizer changes.
- `synthLangs` - dict mapping language codes to a voice language the synthesizer supports.
- `detector` - lazily initialized `LangDetector` instance.

## Requirements

- Minimum NVDA version: 2024.2 (the `speech.extensions.filter_speechSequence`
  extension point was introduced in 2024.2).
- Last tested NVDA version: 2026.2.

## Bundled Dependencies

The add-on bundles fast-langdetect with its dependencies:
- `fasttext_pybind.cp311-win32.pyd` - Python 3.11, 32-bit (NVDA 2024.2 - 2025.x)
- `fasttext_pybind.cp313-win_amd64.pyd` - Python 3.13, 64-bit (NVDA 2026.1+)
- `lid.176.ftz` - FastText lite model for offline language detection

To update the `.pyd` for a new Python version (see also `readme.md`):
```powershell
pip download --no-deps --dest _deps --python-version 3.13 --platform win_amd64 --only-binary=:all: fasttext-predict
Expand-Archive _deps\fasttext_predict-*.whl -DestinationPath _deps\extracted
Copy-Item _deps\extracted\fasttext_pybind.cp313-win_amd64.whl\fasttext_pybind.cp313-win_amd64.pyd addon\globalPlugins\fast_langdetect\
```

## Translations

- UI and manifest strings live in `addon/locale/<lang>/LC_MESSAGES/nvda.po`.
- Translations are managed through the NVDA community Crowdin project
  (`crowdin.com/project/nvdaaddons`). The sync runs weekly via
  `.github/workflows/crowdinL10n.yml`, which requires the `CROWDIN_TOKEN` repository
  secret and calls `uv run scons pot` plus the scripts in `.github/scripts/`.
- The add-on summary (the name "LangDetectSpeech") is intentionally not translated.

## NVDA API Reference

The NVDA API stubs are in `..\python-nvda\python\Lib\site-packages\` (use for IDE
autocomplete and API reference). Key modules:
- `speech/` - Speech synthesis API
- `speech/commands.py` - `LangChangeCommand` and other speech commands
- `speech/extensions.py` - `filter_speechSequence` extension point
- `synthDriverHandler` - Synthesizer driver handling
- `globalPluginHandler` - Plugin base class
- `config` - NVDA configuration
- `gui/settingsDialogs.py` - Settings panel base class

## Working with Synthesizers

The plugin queries `synthDriverHandler.getSynth().availableVoices` to discover voice
languages. Some synthesizers raise `NotImplementedError`; the code handles this by
falling back to the configured fallback language.

**Tested working:** OneCore (built-in), IBM TTS, Vocalizer NVDA
**Not working:** CodeFactory Eloquence, CodeFactory Vocalizer

## Debugging

Start NVDA with logging to file, then read the log after startup:

```powershell
# Start NVDA with debug logging
& "$env:ProgramFiles (x86)\NVDA\nvda.exe" --debug-logging --log-file="$env:TEMP\nvda.log"

# Read the log file after testing
Get-Content "$env:TEMP\nvda.log" -Tail 100

# Or follow the log in real-time
Get-Content "$env:TEMP\nvda.log" -Wait -Tail 50
```

The add-on logs with prefix `LANGPREDICT:` for voice detection and `LangDetectSpeech`
for speech processing.

## Code Style

- Tab indentation (see flake8.ini)
- Max line length: 110
- Uses `_()` for translatable strings (requires `addonHandler.initTranslation()`)
