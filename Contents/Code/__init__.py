NAME = 'South Park'
BASE_URL = 'http://www.southparkstudios.com'
GUIDE_URL = 'http://www.southparkstudios.com/full-episodes'
SEASON_JSON_URL = 'http://www.southparkstudios.com/feeds/full-episode/carousel/%s/dc400305-d548-4c30-8f05-0f27dc7e0d5c' # season
RANDOM_URL = 'http://www.southparkstudios.com/full-episodes/random'

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:23.0) Gecko/20100101 Firefox/23.0'

###################################################################################################
@handler('/video/southpark', NAME)
def MainMenu():

	oc = ObjectContainer(no_cache=True)
	
	oc.add(InputDirectoryObject(key=Callback(EpisodeSearch),
               title='Search',
               summary='Search for South Park episodes by name.',
               prompt="Search by title"
        ))

	oc.add(VideoClipObject(
		url = RandomEpisode(),
		title = L('RANDOM_TITLE')
	))

	num_seasons = len(HTML.ElementFromURL(GUIDE_URL).xpath('//li/a[contains(@href, "full-episodes/season-")]'))

	for season in range(1, num_seasons+1):
		title = F("SEASON", str(season))
		oc.add(DirectoryObject(
			key = Callback(Episodes, title=title, season=str(season)),
			title = title
		))

	return oc

####################################################################################################
@route('/video/southpark/episodes')
def Episodes(title, season):

	oc = ObjectContainer(title2=title)

	for episode in JSON.ObjectFromURL(SEASON_JSON_URL % season)['season']['episode']:

		if episode['available'] != 'true':
			continue

		url = unicode(episode['url'])
		title = episode['title']
		summary = episode['description']
		originally_available_at = Datetime.ParseDate(episode['airdate'])
		index = episode['episodenumber'][-2:]
		thumb = episode['thumbnail'].split('?')[0]

		oc.add(EpisodeObject(
			url = url,
			show = NAME,
			title = title,
			summary = summary,
			originally_available_at = originally_available_at,
			season = int(season),
			index = int(index),
			thumb = Resource.ContentsOfURLWithFallback(thumb)
		))

	if len(oc) < 1:
		return ObjectContainer(header="Empty", message="This season doesn't contain any episodes.")
	else:
		oc.objects.sort(key = lambda obj: obj.index)
		return oc

###################################################################################################
@route('/video/southpark/episodes/random')
def RandomEpisode():

	try:
		page = HTTP.Request(RANDOM_URL, follow_redirects=False).content
	except Ex.RedirectError, e:
		if 'Location' in e.headers:
			url = e.headers['Location']

			if url[0:4] != 'http':
				url = '%s%s' % (BASE_URL, url)

			return unicode(url)

################## SEARCH ##########################################################################
""" This seems HEAVY, but I can't think of another way to easily do this.
    Pull down ALL the episodes listings and look in title for the query we entered. If the query has a partial match,
    add it to the oc.
    Problem is our client has to do the heavy lifing and do 17 different JSON requests.
    I wonder if there's a way to tap into the search functionality on the http://www.southparkstudios.com/full-episodes
    search page? Maybe submit the GET reuqest and parse the page from there?
    It would be AWESOME to have access to the South Park API docs...or just a RESTful url to access...
"""
def EpisodeSearch(query):
	oc = ObjectContainer()
	for season in range(1,17):
		for episode in JSON.ObjectFromURL(SEASON_JSON_URL % season)['season']['episode']:

			if episode['available'] != 'true':
				continue

			title = episode['title']
			
			if title.find(query) == -1:
				continue
			
			url = unicode(episode['url'])
			summary = episode['description']
			originally_available_at = Datetime.ParseDate(episode['airdate'])
			index = episode['episodenumber'][-2:]
			thumb = episode['thumbnail'].split('?')[0]

			oc.add(EpisodeObject(
				url = url,
				show = NAME,
				title = title,
				summary = summary,
				originally_available_at = originally_available_at,
				season = int(season),
				index = int(index),
				thumb = Resource.ContentsOfURLWithFallback(thumb)
			))

	if len(oc) < 1:
		no_results_message = "No results were found for " + str(query)
		return ObjectContainer(header="Empty", message=no_results_message)
	else:
		oc.objects.sort(key = lambda obj: obj.index)
		return oc
