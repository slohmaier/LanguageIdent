# LanguageIdent - NVDA Addon

This NVDA addon processes all spoken text. It identifies the language If the synthesizer supports it, the matching language is used the speak the text.

Features:
- identify language for all spoken text in NVDA with ( https://github.com/saffsd/langid.py )
- change or add LangChangeCmd's with the identified language
- Whiteliste for considered languages for language identification.

# Tested synthesizers

 - builtin One Core
 - IBM TTS ( https://github.com/davidacm/NVDA-IBMTTS-Driver )

# Not working

 - CodeFactory Eloquence
 - Codefactory Vocalizer
