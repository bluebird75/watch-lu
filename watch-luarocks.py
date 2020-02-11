from bs4 import BeautifulSoup
import requests

import sys, os, ast, pprint, subprocess, functools, datetime, collections, re, time, argparse

# Global config

DBDICT_FNAME='dbdict.txt'
# our minimalist db
dbdict = None
DBDICT_INIT_VAL = {}
NET_SLEEP=None
END_PAGE=None
START_PAGE=None
NONET=False
updated_data = []
DEBUG=False

class ParseError(Exception):
    '''Raised when the format of the page has changed and is no longer parseable asis by watch-lu'''
    pass


def init_net_sleep(v):
    global NET_SLEEP
    NET_SLEEP=v

def set_start_page( v ):
    global START_PAGE
    START_PAGE=v

def set_end_page( v ):
    global END_PAGE
    END_PAGE=v

def set_nonet( v ):
    global NONET
    NONET=v

def net_sleep():
    if NET_SLEEP:
        # sleep to release the bandwidth pressure
        time.sleep( NET_SLEEP )

def extract_digit( s ):
    '''Extract the digits from a complex string'''
    v_s = ''.join( c for c in s if c.isdigit() )
    v = int(v_s)
    return v

def sanitize_quotes( s ):
    if s and len(s) > 1 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s

def remove_duplicates( nb_val ):
    '''Data is formatted as list of (isodate, nb of something)
    In case of duplicates, keep only the latest value
    '''
    nb_val.sort(reverse=True)
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
    updated_data.append( (key, data) )

################################################################################333
#
#               LuaRocks stuff

# LuaRocks config
LUAROCKS_PROJECT='http://luarocks.org/modules/bluebird75/luaunit'
NB_DL_LUAROCKS_TOTAL='NB_DL_LUAROCKS_TOTAL'
NB_DL_LUAROCKS_V33='NB_DL_LUAROCKS_V33'

def luarocks_fetch_nb_dl():
    '''Connect to luarocks and retrieve the number of download of luaunit.
    Return: (nb of dowloand of luaunit, nb of download of v3.3)
    '''
    net_sleep()
    s = requests.get(LUAROCKS_PROJECT, headers=HEADERS).text
    soup = BeautifulSoup( s, "html.parser" )
    e = soup.find_all(string='Downloads' )[0]
    # print( e )
    e = e.parent.next_sibling
    # print( e )
    s = e.string
    nb_dl = extract_digit( s )

    e = soup.find_all(string='Versions' )[0]
    e = e.parent.next_sibling
    version_33_1 = e.a.text
    if version_33_1 != '3.3-1':
        raise ValueError('Could not find version 3.3 download info on luarocks')

    nb_dl_v33 = extract_digit( e.span.next_sibling.text )

    return nb_dl, nb_dl_v33

def luarocks_fetch_nb_dl_and_archive():
    "Fetch nb of download and archive in dbdict"
    today = datetime.date.today().isoformat()
    nb_dl, nb_dl_v33 = luarocks_fetch_nb_dl()
    update_db_list( NB_DL_LUAROCKS_TOTAL, (today, nb_dl) )
    update_db_list( NB_DL_LUAROCKS_V33, (today, nb_dl_v33) )
    # print(dbdict)

def watch_luarocks():
    '''Perform the full action on luarocks: retrieve the number of download and archive it'''
    if NONET:
        raise ConnectionError('can not watch luarocks without network')
    luarocks_fetch_nb_dl_and_archive()
    save_db_dict()

################################################################################333
#
#               GitHub stuff

try:
    from github import Github
    HAS_GH_API=True
except ImportError:
    HAS_GH_API=False

GH_DATA_HAVE_LUAUNIT_FILE='GH_DATA_HAVE_LUAUNIT_FILE'
GH_DATA_REF_LUAUNIT_CODE ='GH_DATA_REF_LUAUNIT_CODE'
GH_METADATA              = 'GH_METADATA'
GH_LUAU_VERSIONS         = 'GH_LUAU_VERSIONS'
NO_VERSION               = 'No version'

def get_gh_user_pwd():
    '''Return the locally stored user and password values'''
    home = os.getenv('HOME')
    try:
        path = '%s/.ssh/GH_USER' % home
        user = open(path).read().strip()
        path = '%s/.ssh/GH_PAT_TOKEN' % home
        token = open(path).read().strip()
    except IOError:
        print('Could not read file %s' % path)
        raise Exception("GH_USER and GH_PWD must be set for this action.")
    return user, token

def gh_data_fetch_and_archive_have_luaunit_file(session, page=None):
    '''Search for projects containing a file named luaunit.lua'''
    resp = session.get('https://api.github.com/search/code', params={'q':'filename:luaunit.lua'})
    resp_json = resp.json()
    if 'errors' in resp_json:
        pprint.pprint(resp_json)
        sys.exit(-1)
    dbg('json_resp', pprint.pformat(resp_json))
    return resp_json

def gh_data_fetch_and_archive_ref_luaunit_code(session, page=None):
    '''Search for projects containing a string "luaunit.lua" in their code'''
    resp = session.get('https://api.github.com/search/code', params={'q':'luaunit.lua'})
    resp_json = resp.json()
    if 'errors' in resp_json:
        pprint.pprint(resp_json)
        sys.exit(-1)
    dbg('json_resp', pprint.pformat(resp_json))
    return resp_json

def dbg( info, t ):
    '''Print debug infromation if DEBUG is set to True'''
    if DEBUG == False:
        return
    first = True
    multiline = ( '%s=%s\n' % (info,t) ).split('\n')
    print(multiline[0])
    for l in multiline[1:]:
        print('\t' + l )

def gh_login():
    '''Create a requests session with user credentials'''
    if NONET:
        return 'no network, no session', True

    if hasattr(gh_login, 'session'):
        print('Reusing login session')
        return gh_login.session, True

    session = requests.Session()
    session.auth = get_gh_user_pwd()
    gh_login.session = session
    return session, True

def watch_gh_data():
    '''Retrieve data from github about number of use of luaunit.lua and store into db'''
    session, success = gh_login()
    if not success:
        return
    nb_have_luaunit_file = gh_data_fetch_and_archive_have_luaunit_file(session)['total_count']
    nb_ref_luaunit_code = gh_data_fetch_and_archive_ref_luaunit_code(session)['total_count']
    today = datetime.date.today().isoformat()
    update_db_list( GH_DATA_HAVE_LUAUNIT_FILE, (today, nb_have_luaunit_file) )
    update_db_list( GH_DATA_REF_LUAUNIT_CODE , (today, nb_ref_luaunit_code ) )
    # print(dbdict)

def fname_is_luaunit( fpath ):
    '''Return true if last part of the path is exactly luaunit.lua'''
    fname = fpath.split('/')[-1]
    return fname.lower() == 'luaunit.lua'

reVersion = re.compile(r'Version:\s+(\d+\.\d+)')
def get_luaunit_version( session, proj_luau_fullpath ):
    '''Fetch luaunit file and analyse version of the file.
    Return None if not a luaunit official file. Return version string else'''
    if NONET:
        raise ConnectionError('Can not analyse version of file without network') 
    raw_luaunit_url = proj_luau_fullpath.replace('blob', 'raw')
    net_sleep()
    r = session.get(proj_luau_fullpath, headers=HEADERS)
    open('dl_luaunit.html', 'wb').write( r.text.encode('utf8') )
    if r.text.find('Philippe') == -1:
        # print('No philippe in %s' % raw_luaunit_url )
        return None
    if r.text.find('Fremy') == -1:
        # print('No fremy in %s' % raw_luaunit_url )
        return None
    if r.text.find('Version: ') == -1:
        # print('No version in %s' % raw_luaunit_url )
        return NO_VERSION
    mo = reVersion.search( r.text )
    if not mo:
        # print('No parsable version in %s' % raw_luaunit_url )
        return NO_VERSION
    # print( mo )
    version = mo.group(1)
    # print( version )
    return version

def select_high_version( v1, v2):
    if NO_VERSION in (v1, v2):
        # one or two items are 'no version'
        return (v2 if v2 != NO_VERSION else v1)
    else:
        return max(v2, v1)

def extend_project_info( session, projects, page, pnb, have_luaunit ):
    soup = BeautifulSoup( page, "html.parser" )
    all_code = soup.find_all("div", "code-list-item")
    added_projects = {}
    for code_item in all_code:
        print('.', end='', flush=True)
        dbg( 'code_item', str(code_item ) )
        proj_auth_name = code_item.div.div.a.string.strip()
        dbg( 'proj_auth_name',  proj_auth_name )
        proj_auth, proj_name = proj_auth_name.split('/')
        path_item = code_item.div.div.next_sibling.next_sibling.a
        dbg( 'path_item', path_item )

        if have_luaunit:
            # we have a reference to luaunit file
            proj_luau_relpath =  path_item['title']
            proj_luau_fullpath = 'https://github.com/' + path_item['href']
            dbg( 'proj_luau_relpath', proj_luau_relpath )
            dbg( 'proj_luau_fullpath', proj_luau_fullpath )
            proj_ref_luau_relpath =  ''
            proj_ref_luau_fullpath = ''

            if not fname_is_luaunit( proj_luau_relpath ): 
                continue

            if NONET:
                luau_version = NO_VERSION
            else:
                luau_version = get_luaunit_version( session, proj_luau_fullpath )
                if not luau_version:
                    continue
        else:
            # we have a reference to a file which requires luaunit
            proj_ref_luau_relpath =  path_item['title']
            proj_ref_luau_fullpath = 'https://github.com/' + path_item['href']
            proj_luau_relpath =  ''
            proj_luau_fullpath = ''
            luau_version = NO_VERSION

        if proj_auth_name in projects:
            d = projects[ proj_auth_name ]
            assert( d['name'] == proj_name )
            assert( d['author'] == proj_auth )
        else:
            d = collections.defaultdict(list)
            projects[ proj_auth_name ] = d
            d['name'] = proj_name
            d['author'] = proj_auth
            d['proj_path'] = 'https://github.com/' + proj_auth_name

        added_projects[proj_auth_name] = d

        d['luau_version'] = select_high_version( luau_version, d.get('luau_version', 'No version') )
        d['luau_full_path'].append( proj_luau_fullpath )
        d['luau_rel_path'] .append( proj_luau_relpath )
        d['luau_ref_full_path'].append( proj_ref_luau_fullpath )
        d['luau_ref_rel_path'] .append( proj_ref_luau_relpath )
        d['luau_file_search_page'].append( '%s' % pnb)

        # add extra github data about project
        repo = gh_api().get_repo( proj_auth_name )
        extra_data = {
            'forks' : repo.forks_count,
            'stars' : repo.stargazers_count,
            'watchers' : repo.watchers_count,
        }
        dbg( 'extra_data', extra_data )
        d.update( extra_data )

    return added_projects

def extract_endpage( page ):
    soup = BeautifulSoup( page, "html.parser" )
    next_page = soup.find("a", "next_page")
    maxp = next_page.previous_sibling.previous_sibling.string
    return int(maxp)


def analyse_projects_data_without_luaunit():
    return analyse_projects_data( False )

def analyse_projects_data( have_luaunit=True ):
    '''Analyse content of all project using a lusunit.lua file or referencing such a file.
    have_luaunit: default to True, for projects who actually contain the luaunit.lua file
                  False: project is only referencing luaunit.lua , no version analysis possible.

    Archive the results in the DB file
    '''
    raise ImplementationError("Need to be reworked with REST API")
    session, success = gh_login()
    if not success:
        return
    projects = {}

    if have_luaunit:
        page = gh_data_fetch_and_archive_have_luaunit_file(session)
    else:
        page = gh_data_fetch_and_archive_ref_luaunit_code(session)
    startpage = 1
    endpage = extract_endpage( page )
    if START_PAGE:
        startpage = max(START_PAGE, startpage)
    if END_PAGE:
        endpage = min(END_PAGE, endpage)

    print('Scanning github...')
    for pnb in range(startpage, endpage+1):
        print('P%d' % pnb, end='', flush=True)
        if have_luaunit:
            page = gh_data_fetch_and_archive_have_luaunit_file(session, pnb)
        else:
            page = gh_data_fetch_and_archive_ref_luaunit_code(session, pnb)

        page_projects = extend_project_info( session, projects, page, pnb, have_luaunit )
        # print( page_projects )

    all_versions_and_proj = [ (p['luau_version'], p['proj_path']) for p in projects.values()]
    all_versions = set( v for (v,p) in all_versions_and_proj )
    nbproj_with_version = [ (targetv, len( list( filter( lambda vp: vp[0] == targetv, all_versions_and_proj) ) ) )  for targetv in all_versions ]
    nbproj_with_version.sort()

    today = datetime.date.today().isoformat()
    update_db_list( GH_LUAU_VERSIONS, (today, nbproj_with_version ) )
    save_db_dict()

    # archive the already collected info into a CSV
    if have_luaunit:
        fname = 'projects-have-luaunit.csv'
    else:
        fname = 'projects-ref-luaunit.csv'

    f = open( fname, 'wb')
    fields = ( 'name', 'author', 'proj_path', 'luau_file_search_page', 
               'luau_version', 'stars', 'watchers', 'forks', 'luau_rel_path', 'luau_ref_rel_path', 
               'luau_full_path', 'luau_ref_full_path')
    f.write( b';'.join( s.encode('cp1252', 'replace') for s in fields ) )
    f.write(b'\n')
    try:
        for proj_info in sorted( projects.keys() ):
            for k in fields:
                v = projects[proj_info][k]
                if type(v) == type(22):
                    f.write( bytes(v) )
                elif type(v) == type('33'):
                    f.write( v.encode('cp1252', 'replace') )
                elif type(v) == type([]):
                    f.write( b'"' )
                    for vv in v:
                        f.write( vv.encode('cp1252', 'replace') )
                        f.write( b' ' )
                    f.write( b'"' )
                else:
                    print( 'Unknown type: %s' % type(v) )
                f.write(b';')
            f.write(b'\n')
    except:
        print('Error when handling field %s' % k )
        print('from project %s' % (projects[proj_info]['proj_path']))
        print('of page %s' % (projects[proj_info]['luau_file_search_page'] ) )
        raise
    finally:
        f.close()

def gh_api():
    '''Create a github session and return it'''
    if not HAS_GH_API:
        print("Python package for GitHub API not available...")
        sys.exit(1)

    # static var stored as function attribute
    if not hasattr(gh_api, 'session'):
        gh_api.session = Github( *get_gh_user_pwd() )
    return gh_api.session

def watch_gh_metadata():
    '''Collect information about GitHub luaunit project and update DB'''
    if NONET:
        raise ConnectionError('Can not watch gh metadata without network') 
    lu_repo = gh_api().get_repo('bluebird75/luaunit')
    lu_repo_metadata = {
        'forks_count'       : lu_repo.forks_count,
        'stargazers_count'  : lu_repo.stargazers_count,
        'watchers_count'    : lu_repo.watchers_count,
    }
    today = datetime.date.today().isoformat()
    print( lu_repo_metadata )
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
    if NONET:
        raise ConnectionError("Can not process git pull in no-network mode")
    subprocess.call(['git', 'pull', '--quiet'])

def git_commit_and_push():
    if NONET:
        raise ConnectionError("Can not process git push in no-network mode")
    subprocess.call(['git', 'commit', '--quiet', '-m', 'DB update', 'dbdict.txt'])
    subprocess.call(['git', 'push', '--quiet'])

def dl_to_csv():
    '''Read the dbdict and transform the download data into a CSV file'''
    global dbdict
    init_db_dict()

    import csv, statistics
    f = open('dl_analysis.csv','w', newline='')
    csv_writer = csv.writer(f, delimiter=';')
    data = dbdict[NB_DL_LUAROCKS_TOTAL][:]
    data.sort()

    csv_writer.writerow( ['Date', 'Nb of downloads', 'Average daily downloads over 7 days'] )
    for i,d in enumerate(data):
        v = list(d)
        if i > 7:
            nb_days = (datetime.date.fromisoformat(data[i][0])-datetime.date.fromisoformat(data[i-7][0])).days
            v.append( ('%.1f' % ((data[i][1]-data[i-7][1])/nb_days)).replace('.',','))
        csv_writer.writerow( v )
    f.close()



################################################################################333
#
#               Command Line Interface


ACTIONS = {
    'watch_luarocks': (watch_luarocks, 'Retrieve information from luarocks about luaunit'),
    'watch_gh_data':  (watch_gh_data, 'Retrieve of projects using luaunit in Github (quick)'),
    'watch_gh_metadata':  (watch_gh_metadata, 'Retrieve information about luaunit project in GitHub (quick)'),
    'gh_push': (git_commit_and_push, 'Push update of the DB to Git'),
    'analyse_projects_data': (analyse_projects_data, 'Analyse all projects using a luaunit.lua file to check if some popular projects are using luaunit'),
    'analyse_projects_data_without_luaunit': (analyse_projects_data_without_luaunit, 'Analyse all projects referencing a luaunit.lua file'),
    'dl_to_csv': (dl_to_csv, 'Extract download data into CSV'),
}
HELP_ACTIONS = 'Possible ACTIONS:\n\t' + '\n\t'.join( '%s: %s' % (k, v[1]) for (k,v) in ACTIONS.items() )


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument( '--net-sleep' )
    parser.add_argument( '--no-network', action='store_true' )
    parser.add_argument( '--start-page' )
    parser.add_argument( '--end-page' )
    parser.add_argument( '--print-db', action='store_true' )
    parser.add_argument( 'actions', nargs='*', help='see below')
    result = parser.parse_args()

    if len(result.actions) < 1:
        parser.print_help()
        print()
        print( HELP_ACTIONS )
        sys.exit(1)

    not_recognised = [ action for action in result.actions if not( action in ACTIONS)  ]
    if len(not_recognised):
        print('Unrecognised action: ', ' '.join(not_recognised))
        sys.exit(1)

    if result.no_network:
        print('Work locally on last downloaded files')
        set_nonet( True )
        set_start_page( 1 )
        set_end_page( 1 )

    else:

        if result.net_sleep:
            print('Network sleep: %d' % int(result.net_sleep) )
            init_net_sleep( int(result.net_sleep) )

        if result.start_page:
            print('Start page: %d' % int(result.start_page) )
            set_start_page( int( result.start_page ) )

        if result.end_page:
            print('End page: %d' % int(result.end_page) )
            set_end_page( int( result.end_page ) )

        git_pull()
    init_db_dict()

    for action in result.actions:
        ACTIONS[action][0]()

    if result.print_db:
        pprint.pprint( updated_data )
        # pprint.pprint( dbdict )
    save_db_dict()


