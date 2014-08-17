#!/usr/bin/env python
import sys, urllib, urllib2, cookielib, xbmcgui, xbmcaddon, pickle, simplejson as json

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")

# __settings__ = xbmcaddon.Addon(id='script.image.lastfm.slideshow')
# __language__ = __settings__.getLocalizedString
# lib = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'lib')
# sys.path.append(lib)

# print sys.path
from xbmcapi import XBMCSourcePlugin

# API_KEY = 'x1XhpKkt9qCtqyXdDEGHp5TCDQ1TOWm2VTLiWUm0FHpdkHI5Rj'

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
		# thumbnail = 'http://api.tumblr.com/v2/blog/%s.tumblr.com/avatar/256' % cat
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
	url2 = '%s/ws.php?format=json' % (plugin.getSetting('server'))
	values = {
		'method' : method
	}


	try:
		for key in extraData.iteritems():
			values[key[0]] = key[1]
	except:
		pass

	print '---serverdata---%s' % (values)

	data2 = urllib.urlencode(values)
	req2 = urllib2.Request(url2, data2)
	conn2 = opener.open(req2)
	response2 = json.loads(conn2.read())
	conn2.close()
	if(response2['stat'] == 'ok') :
		return response2['result']
	else :
		xbmcgui.Dialog().ok(__addonname__, 'There was an error retrieving data', 'Method: '+method)

def browseTags():
	tags = serverRequest('pwg.tags.getList');
	for tag in tags['tags']:
		# thumbnail = 'http://api.tumblr.com/v2/blog/%s.tumblr.com/avatar/256' % cat
		listitem = xbmcgui.ListItem(tag['name'])
		plugin.addDirectoryItem(url='tags/%s' % (tag['id']), listitem=listitem, isFolder=True)
	plugin.endOfDirectory()

def browseCategories():
	cats = serverRequest('pwg.categories.getList');
	for cat in cats['categories']:
		listitem = xbmcgui.ListItem(cat['name'],iconImage=cat['tn_url'])
		plugin.addDirectoryItem(url='%s/%s/%s' % (plugin.root, plugin.path, cat['id']), listitem=listitem, isFolder=True)
	plugin.endOfDirectory()

def browseCategoriesImages(catId):
	imgs = serverRequest('pwg.categories.getImages',{'cat_id':catId});
	for img in imgs['images']:
		listitem = xbmcgui.ListItem(img['name'],iconImage=img['derivatives']['thumb']['url'])
		plugin.addDirectoryItem(url=img['element_url'], listitem=listitem)
	plugin.endOfDirectory()

# def catagories():
# 	cats = [c.strip() for c in plugin.getSetting('tumblrs').split()]
# 	for cat in cats:
# 		thumbnail = 'http://api.tumblr.com/v2/blog/%s.tumblr.com/avatar/256' % cat
# 		listitem = xbmcgui.ListItem(cat, iconImage=thumbnail)
# 		ok = plugin.addDirectoryItem(url='%s/%s' % (plugin.root, cat), listitem=listitem, isFolder=True)
# 	plugin.endOfDirectory()

# urls = []
# def listimages(tumblr):
# 	print tumblr
# 	start = int(plugin.query.get('start',0))
# 	url = 'http://api.tumblr.com/v2/blog/%s.tumblr.com/posts/photo?api_key=%s&offset=%d' % (tumblr, API_KEY, start)
# 	print 'URL:', url
# 	fd = urllib2.urlopen(url)
# 	dom = json.load(fd)
# 	fd.close()

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

if plugin.path:
	split = plugin.path.split('/')
	print '>>>>>>plugin.path: '+plugin.path
	print '>>>>>>>>plugin.path.split: %s' % (split)

	if(split[0] == 'tags') :
		browseTags()
	elif(split[0] == 'cats') :

		try:
			catIds = split[1]
			browseCategoriesImages(catIds)
		except:
			browseCategories()
	else :
		home()		

	# listimages(tumblr)
	# try:
	# serverLogin()

	# xbmcgui.Dialog().ok(__addonname__, 'plugin.path present')
	# except: 
	# 	xbmcgui.Dialog().ok(__addonname__, 'Username and/or password incorrect.', 'Please check the configuration')
 #  		pass


else:

	# try:
	serverLogin()
	# print '------------lgin fired'
	# except: 
	# xbmcgui.Dialog().ok(__addonname__, 'no plugin.path')

	# print plugin.root + plugin.path
 #  		pass

	
	home()