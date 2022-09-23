import globalPluginHandler
import sys
import os
from scriptHandler import script
from functools import wraps
from logHandler import log
import wx
import speech

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
distPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist32')
sys.path.append(distPath)

#configuration for settings
config.conf.spec["langPredict"] = {
	'whitelist': 'string(default=\'\')'
}

#global variables to hold languages and fasttext model
# for wraping speak function
synthClass = None
synthLangs = {}
fastTextModel = None

def checkSynth():
	global synthClass
	global synthLangs
	curSynthClass = str(speech.synthDriverHandler.getSynth().__class__)
	if curSynthClass != synthClass:
		synthClass = curSynthClass
		synthLangs = {}
		for voiceId in speech.synthDriverHandler.getSynth().availableVoices:
			voice = speech.synthDriverHandler.getSynth().availableVoices[voiceId]
			lang = voice.language.split('_')[0]
			if not lang in synthLangs:
				synthLangs[lang] = voice.language
		log.info('LANGPREDICT:\nFound voices:\n'+
			'\n'.join(
				['- {0}: {1}'.format(key, synthLangs[key]) for key in synthLangs]
			)
		)

		# Wrap speech.speech.speak, so we can get its output first
		old_synth_speak = speech.synthDriverHandler.getSynth().speak
		@wraps(speech.synthDriverHandler.getSynth().speak)
		def new_synth_speak(speechSequence: SpeechSequence):
			speechSequence = fixSpeechSequence(speechSequence)
			log.debug('langPredict.synth.speak: '+str(speechSequence))
			return old_synth_speak(speechSequence)
		#replace built in speak function
		speech.synthDriverHandler.getSynth().speak = new_synth_speak

def fixSpeechSequence(speechSequence: SpeechSequence):
	checkSynth()

	global fastTextModel
	global synthLangs
	
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
	if text:
		if langChangeCmd is None:
			insertLangChangeCmd = predictLang(langChangeCmd, text)
		else:
			predictLang(langChangeCmd, text)			
	if not insertLangChangeCmd is None:
		speechSequence.insert(0, insertLangChangeCmd)
	log.debug('langChagedCmd={0} insertLangChangedCmd={1} text={2}'.format(str(langChangeCmd), str(insertLangChangeCmd), text))
	return speechSequence

def predictLang(langChangeCmd: LangChangeCommand, text: str):
	global fastTextModel
	#create new langchangecmd if is none
	synth = speech.synthDriverHandler.getSynth()
	defaultLang = synth.availableVoices[synth.voice].language
	if langChangeCmd is None:
		langChangeCmd = LangChangeCommand(defaultLang)
	text = text.replace('\n', ' ').replace('\r', ' ') #fasttext doe not like newlines
	predictedLang = fastTextModel.predict(text)[0][0][9:] #strip '__label__'
	log.debug('PREDICTED={0} TEXT={1}'.format(str(predictedLang), text))

	#don't use a different dialect due to sorting
	if defaultLang.startswith(predictedLang):
		langChangeCmd.lang = defaultLang
	else:
		langChangeCmd.lang = synthLangs.get(predictedLang, defaultLang)
	return langChangeCmd

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()

		#load fasttext langident model
		global fastTextModel
		import fasttext
		fastTextModel = fasttext.load_model(os.path.join(distPath, 'lid.176.ftz'))
		log.debug('LANGPREDICT: loaded model '+str(fastTextModel))

		# Wrap speech.speech.speak, so we can get its output first
		old_speak = speech.speech.speak
		@wraps(speech.speech.speak)
		def new_speak(
			speechSequence: SpeechSequence,
			symbolLevel: Optional[int] = None,


			priority: Spri = Spri.NORMAL):
			speechSequence = fixSpeechSequence(speechSequence)
			log.debug('langPredict.speech.speak: '+str(speechSequence))
			return old_speak(speechSequence, symbolLevel, priority)
		speech.speech.speak = new_speak

class SettingsUi(gui.settingsDialogs.SettingsPanel):
	title = 'langPredict'
	panelDescription = 'langPredict automaticly changes the language '+\
		'for every text, that is spoken. the fasttext-langident AI'+\
		' model is used, which is trained with Wikipedia.'

	def makeSettings(self, settingsSizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		introItem = helper.addItem(wx.StaticText(self, label=self.panelDescription))

		groupSizer = wx.StaticBoxSizer(
			wx.VERTICAL, self,
			# Translators: label of the log files location grouping.
			label=_("Log &Directory: ")
		)
		fileGroupHelper = helper.addItem(gui.guiHelper.BoxSizerHelper(self, sizer=groupSizer))
		fileGroupBox = groupSizer.GetStaticBox()
