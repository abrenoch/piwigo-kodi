#!/usr/bin/env python
import os
import sys
import urllib
import urllib2
import cookielib
import xbmcgui
import xbmcaddon
import simplejson as json

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__cwd__ = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__icon__ = __addon__.getAddonInfo('icon')

from xbmcapi import XBMCSourcePlugin

cookie_filename = __profile__+'pwg.cookie'
cookieJar = cookielib.LWPCookieJar(cookie_filename)

if os.access(cookie_filename, os.F_OK):
	cookieJar.load(ignore_discard=True)

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11'),]
plugin = XBMCSourcePlugin()

def home():
	opts = {
		__addon__.getLocalizedString(33100):'recent/0',
		__addon__.getLocalizedString(33101):'random/0',
		__addon__.getLocalizedString(33102):'rated/0',
		__addon__.getLocalizedString(33103):'cats',
		__addon__.getLocalizedString(33104):'tags',
		__addon__.getLocalizedString(33105):'search'
	}

	user = serverRequest('pwg.session.getStatus')

	if (user['status'] == 'webmaster') or (user['status'] == 'admin') or (user['status'] == 'administrator') :
		opts[__addon__.getLocalizedString(33114)] = 'sync'

	for key in opts.iteritems():
		listitem = xbmcgui.ListItem(key[0])
		plugin.addDirectoryItem(url='%s/%s' % (plugin.root, key[1]), listitem=listitem, isFolder=True)

	plugin.endOfDirectory()	

def serverLogin():
	url = '%s/ws.php?format=json' % (plugin.getSetting('server'))
	values = {
		'method' : 'pwg.session.login',
		'username' : plugin.getSetting('username'),
		'password' : plugin.getSetting('password')
	}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		conn = opener.open(req)
		cookieJar.save(ignore_discard=True)
		connRead = conn.read()
		conn.close()
	except:
		die(True)
	else:
		try:
			response = json.loads(connRead)
		except:
			die(True)
		else:
			if(response['stat'] == 'ok') :
				return True
			else:
				if(plugin.getSetting('username') != 'guest' and plugin.getSetting('username') != '') :
					xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(33106), __addon__.getLocalizedString(33107))
					die(False)
			pass

def serverRequest(method,extraData = []):
	url = '%s/ws.php?format=json' % (plugin.getSetting('server'))
	values = {
		'method' : method
	}
	try:
		for key in extraData.iteritems():
			values[key[0]] = key[1]
	except:
		pass
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	conn = opener.open(req)
	response = json.loads(conn.read())
	conn.close()
	if(response['stat'] == 'ok') :
		return response['result']
	else :
		xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(33109), '%s: %s' % (__addon__.getLocalizedString(33110), method), response['message'])
		die(False)

def populateDirectory(array):
	for obj in array:
		try:
			thumb = obj['tn_url'];
		except:
			listitem = xbmcgui.ListItem(obj['name'])
		else:
			listitem = xbmcgui.ListItem(obj['name'],iconImage=thumb)
		finally:		
			plugin.addDirectoryItem(url='%s/%s/%s/0' % (plugin.root, plugin.path, obj['id']), listitem=listitem, isFolder=True)
	plugin.endOfDirectory()

def populateImages(imgs):
	for img in imgs['images']:
		if(img['name'] == None) :
			if(img['date_creation'] == None) :
				ttl = img['date_available']
			else :
				ttl = img['date_creation']
		else :
			ttl = img['name']
		listitem = xbmcgui.ListItem(ttl,iconImage=img['derivatives']['thumb']['url'])
		listitem.setInfo('pictures',{'date':img['date_available']})
		commands = []
		# commands.append(( 'Modify Tags', 'runnerAdd', ))
		listitem.addContextMenuItems( commands )
		plugin.addDirectoryItem(url=img['element_url'], listitem=listitem)
	if(int(plugin.getSetting('limit')) <= int(imgs['paging']['count'])) :
		nextString = '> %s' % (__addon__.getLocalizedString(33115))
		nextCount = plugin.getSetting('limit')
		try:
			imgCount = (imgs['paging']['page'] + 1)* imgs['paging']['per_page']
			remainingImageCount = imgs['paging']['total_count'] - imgCount
			if(remainingImageCount < int(plugin.getSetting('limit'))):
				nextCount = remainingImageCount
		except:
			pass
		try:
			nextString += ' %s (%s %s)' % (nextCount, imgs['paging']['total_count'], __addon__.getLocalizedString(33116))
		except:
			nextString += ' %s' % (nextCount)
		listitem = xbmcgui.ListItem(nextString)
		newpath = plugin.path.split('/')
		try:
			if(int(newpath[-1])):
				del newpath[-1]
		except:
			pass
		newpathCon = '/'.join(newpath)
		plugin.addDirectoryItem(url='%s/%s/%s' % (plugin.root, newpathCon, (int(imgs['paging']['page']) + 1)), listitem=listitem, isFolder=True)
	plugin.endOfDirectory()


def recursiveCategoryImages(catId,page):
	if(page == 0) :
		categories = serverRequest('pwg.categories.getList',{'cat_id':catId})['categories']
		del categories[0]
		for catg in categories:
			try:
				thumb = catg['tn_url'];
			except:
				listitem = xbmcgui.ListItem('> '+catg['name'])
			else:
				listitem = xbmcgui.ListItem('> '+catg['name'],iconImage=thumb)
			finally:		
				plugin.addDirectoryItem(url='%s/cats/%s/0' % (plugin.root, catg['id']), listitem=listitem, isFolder=True)
	populateImages(serverRequest('pwg.categories.getImages', {'cat_id':catId, 'page':page, 'per_page':plugin.getSetting('limit')}))	

def allCategories():
	types = serverRequest('pwg.categories.getList')['categories']
	args = []
	for oType in types:
		args.append({'cat_id': oType['id']})
	return args

def die(alert):
	if alert:
		xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(33111), __addon__.getLocalizedString(33107))
	raise SystemExit(0)	

def syncServer():
	url = '%s/admin.php?page=site_update&site=1' % (plugin.getSetting('server'))
	values = {
	    'sync': 'files',
	    'display_info': 1,
	    'add_to_caddie': 1,
	    'privacy_level': 0,
	    'simulate': 0,
	    'subcats-included': 1,
	    'submit': 1
	}
	data = urllib.urlencode(values)
	req = urllib2.Request(url, data)
	try:
		conn = opener.open(req)
	except:
		xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(33112), __addon__.getLocalizedString(33108))
		die(False)
	else:
		response = conn.read()
		conn.close()
		if(response.find('scanning dirs')):
			xbmc.executebuiltin('Notification(%s, %s, 5000, %s)'%(__addonname__, __addon__.getLocalizedString(33117), __icon__))
		else:
			xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(33112), __addon__.getLocalizedString(33108))
			die(False)

if plugin.path:
	split = plugin.path.split('/')
	crntPage = 0
	if(split[0] == 'tags') :
		try:
			typeId0 = split[1]
			crntPage = int(split[2])
		except:
			populateDirectory(serverRequest('pwg.tags.getList')['tags'])
		else :
			populateImages(serverRequest('pwg.tags.getImages', {'tag_id':typeId0,'page':crntPage,'per_page' : plugin.getSetting('limit')}))		
	elif(split[0] == 'cats') :
		try:
			typeId0 = split[1]
			crntPage = int(split[2])
		except:
			populateDirectory(serverRequest('pwg.categories.getList')['categories'])
		else :
			recursiveCategoryImages(typeId0,crntPage)
	elif(split[0] == 'recent'):
		try:
			crntPage = int(split[1])
		except:
			pass
		populateImages(serverRequest('pwg.categories.getImages', {'order':'date_available DESC', 'page':crntPage, 'per_page':plugin.getSetting('limit')}))
	elif(split[0] == 'random'):
		populateImages(serverRequest('pwg.categories.getImages', {'order':'random', 'per_page':plugin.getSetting('limit')}))
	elif(split[0] == 'rated'):
		populateImages(serverRequest('pwg.categories.getImages', {'order':'rating_score desc', 'page':crntPage, 'per_page':plugin.getSetting('limit'), 'f_min_rate':0, 'f_max_rate':5}))
	elif(split[0] == 'sync'):
		syncServer()
	elif(split[0] == 'views'):
		xbmcgui.Window();
		ui = modifyTags.modifyTagsWindow('piwigoTagDialog.xml' , __cwd__, 'Default')
		ui.doModal()
	elif(split[0] == 'search'):
		try:
			crntPage = int(split[2])
		except:
			pass
		if(crntPage > 0):
			populateImages(serverRequest('pwg.images.search', {'query':split[1], 'per_page':plugin.getSetting('limit'), 'page':crntPage}))
		else:
			keyboard = xbmc.Keyboard('', __addon__.getLocalizedString(33118), False)
			keyboard.doModal()
			if keyboard.isConfirmed() and keyboard.getText() != '':
				plugin.path += '/%s' % (keyboard.getText())
				populateImages(serverRequest('pwg.images.search', {'query':keyboard.getText(), 'per_page':plugin.getSetting('limit'), 'page':crntPage}))
			else:
				xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(33113))
	else :
		home()		
else:
	serverLogin()
	home()
