import globalPluginHandler
from scriptHandler import script
import speech
import fasttext

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	def __init__(self, *args):
        super().__init__(&args)
