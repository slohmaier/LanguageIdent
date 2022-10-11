import os
import sys
from functools import wraps

import addonHandler
import config
import globalPluginHandler
import gui
import speech
import wx
from gui import SettingsPanel
from logHandler import log
from scriptHandler import script
from speech.commands import (BreakCommand, CharacterModeCommand, IndexCommand,
                             LangChangeCommand, PhonemeCommand, PitchCommand,
                             RateCommand, VolumeCommand)
from speech.priorities import Spri
from speech.types import Optional, SpeechSequence

distdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist32')
sys.path.append(distdir)

from .langid import classify, set_languages

#make _() available
addonHandler.initTranslation()

#configuration for settings
config.conf.spec["langPredict"] = {
	'whitelist': 'string(default=\'\')'
}

#global variables to hold languages and fasttext model
# for wraping speak function
synthClass = None
synthLangs = {}

def get_whitelist():
	whitelist = config.conf['langPredict']['whitelist'].strip()
	if whitelist:
		return [i.strip() for i in whitelist.split(',')]
	else:
		return []

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

		#initialize whitelist if not all languages are in Synthesizer
		whitelist = get_whitelist()
		for lang in whitelist:
			if not lang in synthLangs.keys():
				whitelist = []
				break
		
		#initialize with all supported languages, if whitelist empty or reset
		if not whitelist:
			#TODO: Show messagebox?
			config.conf['langPredict']['whitelist'] = ', '.join(synthLangs.keys())

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
	log.debug('langPredict predictLang: '+text)
	whitelist = get_whitelist()
	#create new langchangecmd if is none
	synth = speech.synthDriverHandler.getSynth()
	defaultLang = synth.availableVoices[synth.voice].language
	if langChangeCmd is None:
		langChangeCmd = LangChangeCommand(defaultLang)
	text = text.replace('\n', ' ').replace('\r', ' ') #fasttext doe not like newlines
	predictedLang = classify(text)[0]
	if predictedLang == None:
		predictedLang = defaultLang
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

		#add settings to nvda
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(langPredictSettings)

		#setting languages
		set_languages(get_whitelist())

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

class langPredictSettings(SettingsPanel):
	title = 'langPredict'
	panelDescription = 'langPredict automaticly changes the language '+\
		'for every text, that is spoken. the fasttext-langident AI'+\
		' model is used, which is trained with Wikipedia.'

	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		introItem = sHelper.addItem(wx.StaticText(self, label=self.panelDescription))
		self._whitelist  = sHelper.addLabeledControl(_('Language Whitelist'), wx.TextCtrl)
		self._loadSettings()
	
	def _loadSettings(self):
		self._whitelist.SetValue(config.conf['langPredict']['whitelist'])

	def onSave(self):
		newWhitelist = [i.strip() for i in self._whitelist.GetValue().split(',')]
		try:
			set_languages(newWhitelist)
			config.conf['langPredict']['whitelist'] = self._whitelist.GetValue()
		except:
			log.debug('langPredict: Invalid languages: ' + self._whitelist.GetValue())
			config.conf['langPredict']['whitelist'] = ', '.join(synthLangs.keys())
			self._whitelist.SetValue(config.conf['langPredict']['whitelist'])
	
	def onPanelActivated(self):
		self._loadSettings()
		self.Show()
