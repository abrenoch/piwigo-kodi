#!/usr/bin/env python
import os
import sys
import urllib
import urllib.request
import http.cookiejar
import xbmcgui
import xbmcaddon
import simplejson as json

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') )
# __cwd__ = xbmc.translatePath( __addon__.getAddonInfo('path') )
__icon__ = __addon__.getAddonInfo('icon')
localize = __addon__.getLocalizedString

from xbmcapi import XBMCSourcePlugin

cookie_filename = __profile__+'pwg.cookie'
cookieJar = http.cookiejar.LWPCookieJar(cookie_filename)

if os.access(cookie_filename, os.F_OK):
	cookieJar.load(ignore_discard=True)

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookieJar))
opener.add_handler(urllib.request.HTTPSHandler())
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11'),]
plugin = XBMCSourcePlugin()

def checkMethods():
	opts = [
		{'dependancies': ['pwg.categories.getImages'], 'urivar': 'recent', 'labelid': 43100, 'adminonly': False},
		{'dependancies': ['pwg.categories.getImages'], 'urivar': 'random', 'labelid': 43101, 'adminonly': False},
		{'dependancies': ['pwg.categories.getImages'], 'urivar': 'rated', 'labelid': 43102, 'adminonly': False},
		{'dependancies': ['pwg.categories.getList'], 'urivar': 'cats', 'labelid': 43103, 'adminonly': False},
		{'dependancies': ['pwg.tags.getList', 'pwg.tags.getImages'], 'urivar': 'tags', 'labelid': 43104, 'adminonly': False},
		{'dependancies': ['pwg.collections.getList', 'pwg.collections.getImages'], 'urivar': 'collection', 'labelid': 43119, 'adminonly': False},
		{'dependancies': ['pwg.users.getFavorites'], 'urivar': 'favorites', 'labelid': 43120, 'adminonly': False},
		{'dependancies': ['pwg.images.search'], 'urivar': 'search', 'labelid': 43105, 'adminonly': False},
		{'dependancies': False, 'urivar': 'sync', 'labelid': 43114, 'adminonly': True},
	]

	returnopts = {}
	user = serverRequest('pwg.session.getStatus')
	methods = serverRequest('reflection.getMethodList')['methods']

	for opt in opts :
		addOpt = False
		if opt['dependancies'] != False :
			approved = 0
			for optDep in opt['dependancies'] :
				for method in methods :
					if method == optDep :
						approved += 1
						break
			if len(opt['dependancies']) <= approved :
				addOpt = True
		else :
			addOpt = True
		if opt['adminonly'] == True and (user['status'] != 'webmaster' and user['status'] != 'admin' and user['status'] != 'administrator') :
			addOpt = False

		if addOpt == True:
			# returnopts[localize(opt['labelid'])] = opt['urivar']
			returnopts[opt['urivar']] = opt['urivar']

	return returnopts

def home():
	opts = checkMethods()

	for key in opts.items():
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
	data = urllib.parse.urlencode(values).encode('utf-8')
	req = urllib.request.Request(url, data)
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
					xbmcgui.Dialog().ok(__addonname__, localize(43106), localize(43107))
					die(False)
			pass

def serverRequest(method,extraData = []):
	url = '%s/ws.php?format=json' % (plugin.getSetting('server'))
	values = {
		'method' : method
	}
	try:
		for key in extraData.items():
			values[key[0]] = key[1]
	except:
		pass
	data = urllib.parse.urlencode(values).encode('utf-8')
	req = urllib.request.Request(url, data)
	conn = opener.open(req)
	response = json.loads(conn.read())
	conn.close()
	if(response['stat'] == 'ok') :
		return response['result']
	else :
		xbmcgui.Dialog().ok(__addonname__, localize(43109), '%s: %s' % (localize(43110), method), response['message'])
		die(False)

def populateDirectory(array):
	for obj in array:
		try:
			thumb = obj['tn_url'];
		except:
			listitem = xbmcgui.ListItem(obj['name'])
		else:
			listitem = xbmcgui.ListItem(obj['name'])
			listitem.setArt(thumb)
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
		listitem = xbmcgui.ListItem(ttl)
		listitem.setArt(img['derivatives']['thumb']['url'])
		listitem.setInfo('pictures',{'date':img['date_available']})
		commands = []
		# commands.append(( 'Modify Tags', 'runnerAdd', ))
		listitem.addContextMenuItems( commands )
		try:
			thumb = img['element_url']
		except:
			thumb = img['derivatives']['xxlarge']['url']
		plugin.addDirectoryItem(url=thumb, listitem=listitem)
	if(int(plugin.getSetting('limit')) <= int(imgs['paging']['count'])) :
		nextString = '> %s' % (localize(43115))
		nextCount = plugin.getSetting('limit')
		try:
			imgCount = (imgs['paging']['page'] + 1)* imgs['paging']['per_page']
			remainingImageCount = imgs['paging']['total_count'] - imgCount
			if(remainingImageCount < int(plugin.getSetting('limit'))):
				nextCount = remainingImageCount
		except:
			pass
		try:
			nextString += ' %s (%s %s)' % (nextCount, imgs['paging']['total_count'], localize(43116))
		except:
			nextString += ' %s' % (nextCount)
		listitem = xbmcgui.ListItem(nextString)
		newpath = plugin.path.split('/')
		try:
			if(int(newpath[-1]) >= 0):
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
		xbmcgui.Dialog().ok(localize(43111), localize(43107))
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
	data = urllib.parse.urlencode(values).encode('utf-8')
	req = urllib.request.Request(url, data)
	try:
		conn = opener.open(req)
	except:
		xbmcgui.Dialog().ok(__addonname__, localize(43112), localize(43108))
		die(False)
	else:
		response = conn.read()
		conn.close()
		if(response.find('scanning dirs')):
			xbmc.executebuiltin('Notification(%s, %s, 5000, %s)'%(__addonname__, localize(43117), __icon__))
		else:
			xbmcgui.Dialog().ok(__addonname__, localize(43112), localize(43108))
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
	elif(split[0] == 'collection') :
		try:
			typeId0 = split[1]
			crntPage = int(split[2])
		except:
			populateDirectory(serverRequest('pwg.collections.getList', {'page':0, 'per_page':plugin.getSetting('limit')})['collections'])
		else :
			populateImages(serverRequest('pwg.collections.getImages', {'col_id':typeId0, 'page':crntPage, 'per_page':plugin.getSetting('limit')}))
	elif(split[0] == 'recent'):
		try:
			crntPage = int(split[1])
		except:
			pass
		populateImages(serverRequest('pwg.categories.getImages', {'order':'date_available DESC', 'page':crntPage, 'per_page':plugin.getSetting('limit')}))
	elif(split[0] == 'random'):
		populateImages(serverRequest('pwg.categories.getImages', {'order':'random', 'per_page':plugin.getSetting('limit')}))
	elif(split[0] == 'rated'):
		try:
			crntPage = int(split[1])
		except:
			pass
		populateImages(serverRequest('pwg.categories.getImages', {'order':'rating_score desc', 'page':crntPage, 'per_page':plugin.getSetting('limit'), 'f_min_rate':0, 'f_max_rate':5}))
	elif(split[0] == 'favorites'):
		try:
			crntPage = int(split[1])
		except:
			pass
		populateImages(serverRequest('pwg.users.getFavorites', {'page':crntPage, 'per_page':plugin.getSetting('limit')}))
	elif(split[0] == 'sync'):
		syncServer()
	# elif(split[0] == 'views'):
	# 	xbmcgui.Window();
	# 	ui = modifyTags.modifyTagsWindow('piwigoTagDialog.xml' , __cwd__, 'Default')
	# 	ui.doModal()
	elif(split[0] == 'search'):
		try:
			crntPage = int(split[2])
		except:
			pass
		if(crntPage > 0):
			populateImages(serverRequest('pwg.images.search', {'query':split[1], 'per_page':plugin.getSetting('limit'), 'page':crntPage}))
		else:
			keyboard = xbmc.Keyboard('', localize(43118), False)
			keyboard.doModal()
			if keyboard.isConfirmed() and keyboard.getText() != '':
				plugin.path += '/%s' % (keyboard.getText())
				populateImages(serverRequest('pwg.images.search', {'query':keyboard.getText(), 'per_page':plugin.getSetting('limit'), 'page':crntPage}))
			else:
				xbmcgui.Dialog().ok(__addonname__, localize(43113))
	else :
		home()
else:
	serverLogin()
	home()
