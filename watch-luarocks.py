from bs4 import BeautifulSoup
import datetime
import requests
import os, ast, pprint

LUAROCKS_PROJECT='http://luarocks.org/modules/bluebird75/luaunit'
FNAME_LUAROCKS_RESULTS = 'luarocks_results.txt'
NB_DL_LUAROCKS='NB_DL_LUAROCKS'
DBDICT_FNAME='dbdict.txt'


# our minimalist db
dbdict = None

DBDICT_INIT_VAL = {
    NB_DL_LUAROCKS: [
       ( '2016-08-18', 6252 ),
       ( '2016-08-22', 7045 ),
    ]
}


def get_nb_dl_on_luarocks( luarocks_url, fname ):
    r = requests.get(luarocks_url)
    f = open(fname, 'w')
    f.write(r.text)
    f.close()

    return r.text

def get_nb_dl():
    if os.path.exists(FNAME_LUAROCKS_RESULTS):
        s = open(FNAME_LUAROCKS_RESULTS).read()
    else:
        s = get_nb_dl_on_luarocks( LUAROCKS_PROJECT, FNAME_LUAROCKS_RESULTS )

    soup = BeautifulSoup( s, "html.parser" )
    e = soup.find_all(string='Downloads' )[0]
    # print( e )
    e = e.parent.next_sibling
    # print( e )
    s = e.string
    nb_dl_s = ''.join( c for c in s if c.isdigit() )
    nb_dl = int(nb_dl_s)
    return nb_dl

def get_nb_dl_and_archive():
    "Fetch nb of download and archive in dbdict"
    today = datetime.date.today().isoformat()
    nb_dl = get_nb_dl()

    if NB_DL_LUAROCKS in dbdict:
        nb_dl_luarocks = dbdict[ NB_DL_LUAROCKS ]
    else:
        nb_dl_luarocks = []
        dbdict[ NB_DL_LUAROCKS ] = nb_dl_luarocks
    nb_dl_luarocks.append( ( today, nb_dl ) )
    print(dbdict)

def init_db_dict():
    '''Load dbdict from disk'''
    global dbdict
    if os.path.exists(DBDICT_FNAME):
        s = open(DBDICT_FNAME, 'r').read()
        dbdict = ast.literal_eval( s )
    else:
        dbdict = DBDICT_INIT_VAL
    print( 'dbdict read: ', dbdict )

def save_db_dict():
    '''Save dbdict into dbdict.txt'''
    f = open(DBDICT_FNAME, 'w')
    s = pprint.pformat(dbdict)
    print( 'Writing dbdict: ', s)
    f.write(s)
    f.close()

if __name__ == '__main__':
    init_db_dict()
    get_nb_dl_and_archive()
    save_db_dict()
