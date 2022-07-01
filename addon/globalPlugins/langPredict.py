import globalPluginHandler
from scriptHandler import script
from logHandler import log
import speech
import fasttext
from speech.types import SpeechSequence, Optional
from speech.priorities import Spri
from speech.commands import (
	IndexCommand,
	CharacterModeCommand,
	LangChangeCommand,
	BreakCommand,
	PitchCommand,
	RateCommand,
	VolumeCommand,
	PhonemeCommand,
)

global synthClass
synthClass = None
global synthLangs
synthLangs = []


def initLangs():
    synthClass = str(speech.synthDriverHandler.getSynth().__class__)
    synthLangs = []
    for voice in speech.synthDriverHandler.getSynth().availableVoices:
        lang = voice.language.split('_')[0]
        if not lang in synthLangs:
            synthLangs.append(lang)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super().__init__()
        
        # Wrap speech.speech.speak, so we can get its output first
		old_speak = speech.speech.speak
		@wraps(speech.speech.speak)
		def new_speak(
				sequence: SpeechSequence,
				symbolLevel: Optional[int] = None,
				priority: Spri = Spri.NORMAL
		):
			log.debug('LANGPREDICT')
			return old_speak(sequence, symbolLevel, priority)
		speech.speech.speak = new_speak
