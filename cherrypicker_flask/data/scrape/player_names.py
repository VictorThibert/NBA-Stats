# scrape all player names and ids into mongo (step 1)
#
# see:      github.com/seemethere/nba_py/wiki/stats.nba.com-Endpoint-Documentation for complete endpoint documention
# format:   stats.nba.com/stats/{endpoint}/?{params}
# example:  http://stats.nba.com/stats/commonallplayers/?LeagueID=00&Season=2015-16&IsOnlyCurrentSeason=0
#
# player_id
# player_name

import requests
import mongo_helper

# set proper headers to allow scraping from NBA website
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0'}

# parameters for endpoints
league_id = '00'
season = '1900-17' #every single player
is_only_current_season = '0'

# url endpoint
url = 'http://stats.nba.com/stats/' \
            'commonallplayers/?' \
            'LeagueID=' + league_id + \
            '&Season=' + season + \
            '&IsOnlyCurrentSeason=' + is_only_current_season

print('Scraping all player names and ids from:')
print(url)

response = requests.get(url, headers=headers)
response.raise_for_status()
data = response.json()

# players currently refers to the 'players' collection
players = mongo_helper.db.players

# each item is a player
for item in data['resultSets'][0]['rowSet']:
    
    # item[0] is NBA:PERSON_ID
    # item[3] is NBA:DISPLAY_FIRST_LAST (e.g. name of player)
    player_id = int(item[0])
    player_name = item[2]

    players.update(
        # condition: on player id
        {'player_id':player_id}, 
        # insert the following document (using $set to add new fields without deleting existing fields)
        { '$set':
            {
                'player_id':player_id,
                'player_name':player_name
            }
        },
        upsert=True)

mongo_helper.client.close()