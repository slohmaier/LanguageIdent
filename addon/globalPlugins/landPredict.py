import globalPluginHandler
from scriptHandler import script
from logHandler import log
import speech
import fasttext

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

def speak(speechSequence: list, *args):
    log.debug('LANGPREDICIT: speechSequence={0}'.format(str(speechSequence)))
    speech.___speak(speechSequence, *args)

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self):
        super().__init__()
        speech.___speak = speech.speak
        speech.speak = speech.___speak
