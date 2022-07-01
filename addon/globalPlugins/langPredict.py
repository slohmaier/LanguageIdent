import globalPluginHandler
import sys
import os
from scriptHandler import script
from functools import wraps
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

#add dist-folder to PYTHONPATH
#TODO: Support 64bit
distPath = os.path.join(os.path.dirname(os.path.absname(__file__)), 'dist32')
sys.path.append(distPath)

#global variables to hold languages and fasttext model
# for wraping speak function
global synthClass
synthClass = None
global synthLangs
synthLangs = {}
global fasttextModel
fastTextModel = None

def checkSynth():
	curSynthClass = str(.__class__)
	if curSynthClass != synthClass:
		synthClass = curSynthClass
		synthLangs = []
		for voice in speech.synthDriverHandler.getSynth().availableVoices:
			lang = voice.language.split('_')[0]
			if not lang in synthLangs:
				synthLangs[lang] = voice.language

def predictLang(langChangeCmd: LangChangeCommand, text: str):
	#create new langchangecmd if is none
	synth = speech.synthDriverHandler.getSynth()
	defaultLang = synth.availableVoices[synth.voice].language
	if langChangeCmd is None:
		langChangeCmd = LangChangeCommand(defaultLang)
	predictedLang = fastTextModel.predict(text)[0][0][9:] #strip '__label__'

	#don't use a different dialect due to sorting
	if defaultLang.startswith(predictedLang):
		langChangeCmd.lang = defaultLang
	else:
		langChangeCmd.lang = synthLangs.get(predictedLang, defaultLang)
		log.debug('LANGPREDICT: Switching to '+str(predictedLang))
	return langChangeCmd

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()

		#load fasttext langident model
		fastTextModel fasttext.load_model(os.path.join(distPath, 'lid.176.ftz'))

		# Wrap speech.speech.speak, so we can get its output first
		old_speak = speech.speech.speak
		@wraps(speech.speech.speak)
		def new_speak(
			speechSequence: SpeechSequence,
			symbolLevel: Optional[int] = None,
			priority: Spri = Spri.NORMAL):
			checkSynth()
			
			#deconstruct speechsequence
			langChangeCmd = None
			insertLangChangeCmd = None
			text = ''
			for item in speechSequence:
				if type(item) == LangChangeCommand:
					langChangeCmd = item
				elif type(item) == str:
					text += item
				else:
					if langChangeCmd is None:
						insertLangChangeCmd = predictLang(langChangeCmd, text)
					else:
						predictLang(langChangeCmd, text)
					text = ''
			if text and not langChangeCmd is None:
				if langChangeCmd is None:
					insertLangChangeCmd = predictLang(langChangeCmd, text)
				else:
					predictLang(langChangeCmd, text)
			if not insertLangChangeCmd is None:
				speechSequence.insert(0, insertLangChangeCmd)

			return old_speak(sequence, symbolLevel, priority)
		#replace built in speak function
		speech.speech.speak = new_speak
