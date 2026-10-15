# LangDetectSpeech - NVDA Add-on

LangDetectSpeech is a lightweight NVDA add-on that automatically detects the language
of spoken text and switches to the appropriate synthesizer voice. It uses a vendored
copy of fast-langdetect (FastText-based) for efficient, fully offline language
detection across 176 languages.

## Features

- Fast, offline language detection using FastText
- Automatic voice switching based on the detected language
- Whitelist of languages to consider for detection
- Configurable fallback language

## Requirements

- NVDA 2024.2 or later.
- The NVDA speech option "Automatic language switching (when supported)" must be
  enabled. On startup the add-on offers to enable it if it is turned off.
- A synthesizer that exposes language information for its voices. The following
  synthesizers are known to work:
  - OneCore (built into Windows)
  - IBM TTS (NVDA-IBMTTS-Driver)
  - Vocalizer NVDA

  The following are known not to work:
  - CodeFactory Eloquence
  - CodeFactory Vocalizer

## Usage

Once installed, the add-on works automatically: every spoken text is analysed and the
language used to read it is switched when a different language is detected. Detection
requires at least three characters of text.

## Settings

Open NVDA menu, Preferences, Settings, and select "LangDetectSpeech":

- "Languages to detect": one checkbox per language supported by the current
  synthesizer. Only the selected languages are considered when detecting. The list is
  populated automatically from the active synthesizer.
- "Fallback language": used when the detected language is not among the languages
  above.

## Bundled binary dependencies and licenses

This add-on bundles third-party components:

- `fast_langdetect` - a trimmed subset of
  [fast-langdetect](https://github.com/LlmKira/fast-langdetect) (MIT licence).
- `fasttext_pybind*.pyd` from the
  [fasttext-predict](https://pypi.org/project/fasttext-predict/) package
  ([source](https://github.com/facebookresearch/fastText), MIT licence). The `.pyd`
  files are taken unmodified from the official PyPI wheel.
- `resources/lid.176.ftz` - the pre-trained fastText language identification lite
  model, distributed under the
  [Creative Commons Attribution-Share-Alike 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
  licence.

## Included builds

| File | Python | NVDA version |
|------|--------|--------------|
| `fasttext_pybind.cp311-win32.pyd` | 3.11 32-bit | 2024.2 up to 2025.x |
| `fasttext_pybind.cp313-win_amd64.pyd` | 3.13 64-bit | 2026.x |

## Rebuilding for a new Python version

```powershell
pip download --no-deps --dest _deps `
    --python-version <X.Y> `
    --platform <win32|win_amd64> `
    --only-binary=:all: `
    fasttext-predict
Expand-Archive _deps\fasttext_predict-*.whl -DestinationPath _deps\extracted
Copy-Item _deps\extracted\fasttext_pybind.cpXY-<platform>.pyd addon\globalPlugins\fast_langdetect\
```
