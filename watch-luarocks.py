from bs4 import BeautifulSoup
import requests

import sys, os, ast, pprint, subprocess, functools, datetime

# Global config

DBDICT_FNAME='dbdict.txt'
# our minimalist db
dbdict = None
DBDICT_INIT_VAL = {}


def extract_digit( s ):
    '''Extract the digits from a complex string'''
    v_s = ''.join( c for c in s if c.isdigit() )
    v = int(v_s)
    return v

def sanitize_quotes( s ):
    if len(s) > 1 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s

def remove_duplicates( nb_val ):
    '''Data is formatted as (isodate, nb of something)
    In case of duplicates, keep only the latest value
    '''
    nb_val.sort()
    new_nb_val = functools.reduce( lambda li, e: li + [e] if len(li) == 0 or li[-1][0] != e[0] else li, nb_val, [] )
    if len(new_nb_val) != len(nb_val):
        print( 'Removed %d duplicates' % (len(nb_val) - len(new_nb_val)))
    return new_nb_val

def update_db_list( key, data ):
    '''Update our dbdict with a new entry, create the db column if needed'''
    if key in dbdict:
        list_val = dbdict[ key ]
    else:
        list_val = []
        dbdict[ key ] = list_val
    list_val.append( data )
    dbdict[ key ] = remove_duplicates( list_val )

################################################################################333
#
#               LuaRocks stuff

# LuaRocks config
LUAROCKS_PROJECT='http://luarocks.org/modules/bluebird75/luaunit'
NB_DL_LUAROCKS='NB_DL_LUAROCKS'

def luarocks_fetch_nb_dl():
    s = requests.get(LUAROCKS_PROJECT).text
    soup = BeautifulSoup( s, "html.parser" )
    e = soup.find_all(string='Downloads' )[0]
    # print( e )
    e = e.parent.next_sibling
    # print( e )
    s = e.string
    nb_dl = extract_digit( s )
    return nb_dl

def luarocks_fetch_nb_dl_and_archive():
    "Fetch nb of download and archive in dbdict"
    today = datetime.date.today().isoformat()
    nb_dl = luarocks_fetch_nb_dl()
    update_db_list( NB_DL_LUAROCKS, (today, nb_dl) )
    # print(dbdict)

def watch_luarocks():
    luarocks_fetch_nb_dl_and_archive()
    save_db_dict()

################################################################################333
#
#               GitHub stuff

try:
    from github import Githubx
    HAS_GH_API=True
except ImportError:
    HAS_GH_API=False

GH_USER=sanitize_quotes( os.getenv('GH_USER') )
GH_PWD=sanitize_quotes( os.getenv('GH_PWD') )

GH_DATA_HAVE_LUAUNIT_FILE='GH_DATA_HAVE_LUAUNIT_FILE'
GH_DATA_REF_LUAUNIT_CODE ='GH_DATA_REF_LUAUNIT_CODE'
GH_METADATA = 'GH_METADATA'

def gh_data_fetch_and_archive_have_luaunit_file(session):
    r = session.get('https://github.com/search?utf8=%E2%9C%93&q=filename%3Aluaunit.lua&type=Code&ref=searchresults')
    open('gh_login3.txt', 'wb').write( r.text.encode('utf8') )
    return r.text

def gh_data_fetch_and_archive_ref_luaunit_code(session):
    r = session.get('https://github.com/search?utf8=%E2%9C%93&q=luaunit.lua&type=Code&ref=searchresults')
    open('gh_login4.txt', 'wb').write( r.text.encode('utf8') )
    return r.text

def printtag( t ):
    print( t.encode('cp1252', 'replace') )

def gh_login():
    s = requests.Session()

    # open login page
    r = s.get( 'https://github.com/login' )
    open('gh_login1.txt', 'wb').write( r.text.encode('utf8' ) )

    # perform login
    soup = BeautifulSoup( r.text, "html.parser" )
    input_utf8 = soup.find_all('input')[0]['value']
    input_auth_token = soup.find_all('input')[1]['value']
    # printtag( input_utf8 )
    # printtag( input_auth_token )
    if not(GH_USER) or not(GH_PWD):
        raise ValueError("GH_USER and GH_PWD must be set for this action. Current values: %s, %s" % (GH_USER, GH_PWD) )
    payload = { 'authenticity_token': input_auth_token, 'utf8' : input_utf8, 'login': GH_USER, 'password' : GH_PWD,   }
    # print(str(payload).encode('cp1252', 'replace'))
    r = s.post( 'https://github.com/session', data=payload  )
    open('gh_login2.txt', 'wb').write( r.text.encode('utf8') )

    # validate login
    soup = BeautifulSoup( r.text, "html.parser" )
    if soup.get_text().find('Incorrect username or password') != -1:
        print('Login failed! user="%s" pwd="%s"' % (GH_USER, GH_PWD) )
        return s, False

    return s, True

def count_results( data ):
    soup = BeautifulSoup( data, "html.parser" )
    e = soup.find_all("div", "sort-bar")[0]
    s = e.h3.string
    nb = extract_digit( s )
    return nb

def watch_gh_data():
    session, success = gh_login()
    if not success:
        return
    nb_have_luaunit_file = count_results( gh_data_fetch_and_archive_have_luaunit_file(session) )
    nb_ref_luaunit_code = count_results( gh_data_fetch_and_archive_ref_luaunit_code(session) )
    today = datetime.date.today().isoformat()
    update_db_list( GH_DATA_HAVE_LUAUNIT_FILE, (today, nb_have_luaunit_file) )
    update_db_list( GH_DATA_REF_LUAUNIT_CODE , (today, nb_ref_luaunit_code ) )
    print(dbdict)

def watch_gh_metadata():
    if not HAS_GH_API:
        print("GitHub API not available...")
        sys.exit(1)
    g = Github(GH_USER, GH_PWD)
    lu_repo = g.get_repo('bluebird75/luaunit')
    lu_repo_metadata = {
        'forks_count'       : lu_repo.forks_count,
        'stargazers_count'  : lu_repo.stargazers_count,
        'watchers_count'    : lu_repo.watchers_count,
    }
    today = datetime.date.today().isoformat()
    update_db_list( GH_METADATA, (today, lu_repo_metadata ) )

################################################################################333
#
#               Local DB stuff

def init_db_dict():
    '''Load dbdict from disk'''
    global dbdict
    if os.path.exists(DBDICT_FNAME):
        s = open(DBDICT_FNAME, 'r').read()
        dbdict = ast.literal_eval( s )
    else:
        dbdict = DBDICT_INIT_VAL
    # print( 'dbdict read: ', dbdict )

def save_db_dict():
    '''Save dbdict into dbdict.txt'''
    f = open(DBDICT_FNAME, 'w')
    s = pprint.pformat(dbdict)
    # print( 'Writing dbdict: ', s)
    f.write(s)
    f.close()

def git_pull():
    subprocess.call(['git', 'pull', '--quiet'])

def git_commit_and_push():
    subprocess.call(['git', 'commit', '--quiet', '-m', 'DB update', 'dbdict.txt'])
    subprocess.call(['git', 'push', '--quiet'])

def github_db_commit_push():
    git_commit_and_push()



################################################################################333
#
#               Command Line Interface


ACTIONS = {
    'watch_luarocks': watch_luarocks,
    'watch_gh_data':  watch_gh_data,
    'watch_gh_metadata':  watch_gh_metadata,
    'gh_push': git_commit_and_push,
}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Possible ACTIONS: %s' % ', '.join(ACTIONS.keys()) )
        sys.exit(1)

    not_recognised = [ action for action in sys.argv[1:] if not( action in ACTIONS)  ]
    if len(not_recognised):
        print('Unrecognised action: ', ' '.join(not_recognised))
        sys.exit(1)

    git_pull()
    init_db_dict()

    for action in sys.argv[1:]:
        ACTIONS[action]()

    pprint.pprint( dbdict )
    save_db_dict()

