#!/usr/bin/env python
import sys, urllib, urllib2, cookielib, xbmcgui, xbmcaddon, pickle, simplejson as json

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
# __settings__ = xbmcaddon.Addon(id='script.image.lastfm.slideshow')
# __language__ = __settings__.getLocalizedString

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
		'Recent Photos':'recent',
		'Random Photos':'random',
		'Browse by Categories':'cats',
		'Browse by Tags':'tags'
	}
	for key in opts.iteritems():
		print key[0]
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
	conn = opener.open(req)
	cookieJar.save(ignore_discard=True)
	response = json.loads(conn.read())
	conn.close()
	if(response['stat'] == 'ok') :
		return True
	else :
		xbmcgui.Dialog().ok(__addonname__, 'Username and/or password incorrect.', 'Please check the configuration')

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
		xbmcgui.Dialog().ok(__addonname__, 'There was an error retrieving data', 'Method: '+method, response['message'])

def populateDirectory(array):
	for obj in array:
		try:
			thumb = obj['tn_url'];
		except:
			listitem = xbmcgui.ListItem(obj['name'])
		else:
			listitem = xbmcgui.ListItem(obj['name'],iconImage=thumb)
		finally:		
			plugin.addDirectoryItem(url='%s/%s/%s' % (plugin.root, plugin.path, obj['id']), listitem=listitem, isFolder=True)
	plugin.endOfDirectory()

def populateImages(imgs):
	for img in imgs['images']:
		listitem = xbmcgui.ListItem(img['name'],iconImage=img['derivatives']['thumb']['url'])
		listitem.setInfo('pictures',{'date':img['date_available']})
		plugin.addDirectoryItem(url=img['element_url'], listitem=listitem)
	plugin.endOfDirectory()

def recursiveCategoryImages(catId):
	categories = serverRequest('pwg.categories.getList',{'cat_id':catId})['categories']
	del categories[0]
	for catg in categories:
		try:
			thumb = catg['tn_url'];
		except:
			listitem = xbmcgui.ListItem(catg['name'])
		else:
			listitem = xbmcgui.ListItem('> '+catg['name'],iconImage=thumb)
		finally:		
			plugin.addDirectoryItem(url='%s/cats/%s' % (plugin.root, catg['id']), listitem=listitem, isFolder=True)
	populateImages(serverRequest('pwg.categories.getImages',{'cat_id':catId}))	

# 	posts = dom['response']['posts']
# 	if len(posts) >= 20:
# 		thumbnail = 'http://api.tumblr.com/v2/blog/%s.tumblr.com/avatar/256' % tumblr
# 		listitem = xbmcgui.ListItem('Next Page (%d - %d)' % (start + 20, start + 40), iconImage=thumbnail)
# 		url = plugin.root + plugin.path + '?start=' + str(start + 20)
# 		plugin.addDirectoryItem(url=url, listitem=listitem,isFolder=True)
# 	post_index = start
# 	for post in posts:
# 		index = 1
# 		children = [photo['alt_sizes'][0] for photo in post['photos']]
# 		for tag in children:
# 			if len(children) > 1:
# 				label = 'Post %d - %d' % (post_index, index)
# 			else:
# 				label = 'Post %d' % (post_index)
# 			listitem = xbmcgui.ListItem(label)
# 			url = tag['url']
# 			if (url in urls):
# 				continue
# 			print 'URL:', url
# 			plugin.addDirectoryItem(url=url, listitem=listitem)
# 			index += 1
# 		post_index += 1
# 	plugin.endOfDirectory()

# listitem = xbmcgui.ListItem(plugin.getSetting('username'), iconImage='http://velocityagency.com/wp-content/uploads/2013/08/go.jpg')
# plugin.addDirectoryItem(url='http://velocityagency.com/wp-content/uploads/2013/08/go.jpg', listitem=listitem)
# plugin.endOfDirectory()

def allCategories():
	types = serverRequest('pwg.categories.getList')['categories']
	args = []
	for oType in types:
		args.append({'cat_id': oType['id']})
	return args

if plugin.path:
	split = plugin.path.split('/')
	if(split[0] == 'tags') :
		try:
			typeId = split[1]
		except:
			populateDirectory(serverRequest('pwg.tags.getList')['tags'])
		else :
			populateImages(serverRequest('pwg.tags.getImages',{'tag_id':typeId}))		
	elif(split[0] == 'cats') :
		try:
			typeId = split[1]
		except:
			populateDirectory(serverRequest('pwg.categories.getList')['categories'])
		else :
			recursiveCategoryImages(typeId)
	elif(split[0] == 'recent'):
		populateImages(serverRequest('pwg.categories.getImages',[{'order':'date_available DESC'}, allCategories()]))
	elif(split[0] == 'random'):
		populateImages(serverRequest('pwg.categories.getImages',[{'order':'random'}, allCategories()]))
	else :
		home()		
else:
	serverLogin()
	home()