# scrape all player common info
#
# see:      github.com/seemethere/nba_py/wiki/stats.nba.com-Endpoint-Documentation for complete endpoint documention
# format:   stats.nba.com/stats/{endpoint}/?{params}
# example:  http://stats.nba.com/stats/commonallplayers/?LeagueID=00&Season=2015-16&IsOnlyCurrentSeason=0
#
# birth_date
# school
# country
# height
# weight
# roster_status
# current_team_id
# current_team_name
# from_year
# to_year
# draft_year
# draft_position (round and number)

import requests
import mongo_helper
import asyncio
import async_timeout
import aiohttp

# set proper headers to allow scraping from NBA website
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0'}

@asyncio.coroutine
def fetch_page(session, url):
    print('Fetching player: ' + url[-4:])
    # set timeout for longer in case of errors
    with aiohttp.Timeout(100):
        response = yield from session.get(url, headers=headers)
        try:
            return (yield from response.json())
        finally:
            yield from response.release()

# players currently refers to the 'players' collection
players = mongo_helper.db.players

# player_id_list referes to a cursor, which needs to be closed. save it into an array first
player_id_list = list(players.find({'draft_position.number':1},{'_id':0, 'player_id':1}))

loop = asyncio.get_event_loop()
returned_tasks = []
with aiohttp.ClientSession(loop=loop) as session:
    tasks = [fetch_page(session,'http://stats.nba.com/stats/commonplayerinfo/?PlayerID=' + str(element['player_id'])) for element in player_id_list]

    content = loop.run_until_complete(asyncio.wait(tasks))
    # content contains a tuple
    returned_tasks = list(content[0])

for element in returned_tasks:
    for item in element.result()['resultSets'][0]['rowSet']:
        
        # item[0] is NBA:PERSON_ID
        # item[6] is NBA:BIRTHDATE
        # item[7] is NBA:SCHOOL
        # item[8] is NBA:COUNTRY 
        # item[10] is NBA:HEIGHT 
        # item[11] is NBA:WEIGHT 
        # item[15] is NBA:ROSTERSTATUS 
        # item[16] is NBA:TEAM_ID 
        # item[17] is NBA:TEAM_NAME 
        # item[22] is NBA:FROM_YEAR 
        # item[23] is NBA:TO_YEAR
        # item[26] is NBA:DRAFT_YEAR
        # item[27] is NBA:DRAFT_ROUND
        # item[28] is NBA:DRAFT_NUMBER

        player_id = int(item[0])
        birth_date = item[6]
        school = item[7]
        country = item[8]
        height = item[10]
        if str(item[11]).isdigit():
            weight = int(item[11])
        else:
            weight = 0

        roster_status = item[15]

        if str(item[16]).isdigit():
            current_team_id = int(item[16])
        else:
            current_team_id = 0

        current_team_name = item[17]

        if str(item[22]).isdigit() and str(item[23]).isdigit():
            years_active = {'from':int(item[22]), 'to':int(item[23])}
        else:
            years_active = {'from':0, 'to':0}

        if str(item[26]).isdigit():
            draft_year = int(item[26])
        else:
            draft_year = 0

        if str(item[27]).isdigit() and str(item[28]).isdigit():
            draft_position = {'round':int(item[27]), 'number':int(item[28])}
        else:
            draft_position = {'round':0, 'number':0}
        print(years_active)
        players.update_one(
            # condition: on player id
            {'player_id':player_id}, 
            # insert the following document (using $set to add new fields without deleting existing fields)
            { "$set":
                {
                    'birth_date':birth_date,
                    'school':school,
                    'country':country,
                    'height':height,
                    'weight':weight,
                    'roster_status':roster_status,
                    'current_team_id':current_team_id,
                    'current_team_name':current_team_name,
                    'years_active':years_active,
                    'draft_year':draft_year,
                    'draft_position':draft_position
                }

            },
            # creates a new document if no document matches the criteria
            upsert=True)

mongo_helper.client.close()