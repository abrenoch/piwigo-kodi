import os
import re
import sys


import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

class XBMCAddon(object):
	def __init__(self, name):
		self.name = name
		self.settings = xbmcaddon.Addon(id=name)
		self.anguage = self.settings.getLocalizedString
		self.home = self.settings.getAddonInfo('path')
		self.icon = xbmc.translatePath( os.path.join( self.home, 'icon.png' ) )

class XBMCSourcePlugin(XBMCAddon):
	def __init__(self):
		self.root = re.match(r'plugin:\/\/[A-Za-z0-9_.-]+', sys.argv[0]).group(0)
		XBMCAddon.__init__(self, self.root[8:])
		self.path = sys.argv[0].replace(self.root,'').lstrip('/').split('?')[0]
		self.query = {}
		if '?' in sys.argv[2]:
			query = sys.argv[2][1:].split('&')
			for q in query:
				k, v = q.split('=')
				self.query[k] = v
		self.id = int(sys.argv[1])

	def getSetting(self, setting):
		return xbmcplugin.getSetting(self.id, setting)

	def endOfDirectory(self):
		xbmcplugin.endOfDirectory(self.id)

	def addDirectoryItem(self, url, listitem=None, isFolder=False):
		return xbmcplugin.addDirectoryItem(handle=self.id, url=url, listitem=listitem, isFolder=isFolder)

