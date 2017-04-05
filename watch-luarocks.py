from bs4 import BeautifulSoup
import requests
import six

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

################################################################################333
#
#               LuaRocks stuff

# LuaRocks config
LUAROCKS_PROJECT='http://luarocks.org/modules/bluebird75/luaunit'
NB_DL_LUAROCKS='NB_DL_LUAROCKS'

def luarocks_fetch_nb_dl():
    net_sleep()
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
    home = os.getenv('HOME')
    try:
        path = '%s/.ssh/GH_USER' % home
        user = open(path).read().strip()
        path = '%s/.ssh/GH_PWD' % home
        pwd  = open(path).read().strip()
    except IOError:
        print('Could not read file %s' % path)
        raise Exception("GH_USER and GH_PWD must be set for this action.")
    return user, pwd

def gh_data_fetch_and_archive_have_luaunit_file(session, page=None):
    if NONET:
        page = open('gh_have_luaunit_file.txt', 'rb').read().decode( 'utf8')
        return page

    pageref='&p=%d' % page if page else ''
    net_sleep()
    r = session.get('https://github.com/search?utf8=%E2%9C%93&q=filename%3Aluaunit.lua&type=Code&ref=searchresults' + pageref)
    open('gh_have_luaunit_file.txt', 'wb').write( r.text.encode('utf8') )
    return r.text

def gh_data_fetch_and_archive_ref_luaunit_code(session, page=None):
    if NONET:
        page = open('gh_ref_luaunit_code.txt', 'rb').read().decode( 'utf8')
        return page

    pageref='&p=%d' % page if page else ''
    net_sleep()
    r = session.get('https://github.com/search?utf8=%E2%9C%93&q=luaunit.lua&type=Code&ref=searchresults' + pageref)
    open('gh_ref_luaunit_code.txt', 'wb').write( r.text.encode('utf8') )
    return r.text

def enc_print( info, t ):
    for l in  ( '%s=%s' % (info,t) ).split('\n'):
        six.print_( l.encode('cp1252', 'replace') )

def gh_login():
    if NONET:
        return 'no network, no session', True
    if hasattr(gh_login, 'session'):
        print('Reusing login session')
        return gh_login.session        

    session = requests.Session()

    # open login page
    r = session.get( 'https://github.com/login' )
    open('gh_login1.txt', 'wb').write( r.text.encode('utf8' ) )

    # perform login
    soup = BeautifulSoup( r.text, "html.parser" )
    input_utf8 = soup.find_all('input')[0]['value']
    input_auth_token = soup.find_all('input')[1]['value']
    # enc_print( input_utf8 )
    # enc_print( input_auth_token )
    user, pwd = get_gh_user_pwd()
    payload = { 'authenticity_token': input_auth_token, 'utf8' : input_utf8, 'login': user, 'password' : pwd,   }
    # print(str(payload).encode('cp1252', 'replace'))
    r = session.post( 'https://github.com/session', data=payload  )
    open('gh_login2.txt', 'wb').write( r.text.encode('utf8') )

    # validate login
    soup = BeautifulSoup( r.text, "html.parser" )
    if soup.get_text().find('Incorrect username or password') != -1:
        print('Login failed! user="%s" pwd="%s"' % (GH_USER, GH_PWD) )
        return session, False

    # store session for later re-use
    gh_login.session = session

    return session, True

def count_results( data ):
    soup = BeautifulSoup( data, "html.parser" )
    e = soup.find_all("div", "d-flex flex-justify-between border-bottom pb-3")[0]
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
    # print(dbdict)

def fname_is_luaunit( fpath ):
    '''Return true if last part of the path is exactly luaunit.lua'''
    fname = fpath.split('/')[-1]
    return fname.lower() == 'luaunit.lua'

reVersion = re.compile('Version:\s+(\d+\.\d+)')
def get_luaunit_version( session, proj_luau_fullpath ):
    '''Fetch luaunit file and analyse version of the file.
    Return None if not a luaunit official file. Return version string else'''
    if NONET:
        raise ConnectionError('Can not analyse version of file without network') 
    raw_luaunit_url = proj_luau_fullpath.replace('blob', 'raw')
    net_sleep()
    r = session.get(proj_luau_fullpath)
    open('dl_luaunit.txt', 'wb').write( r.text.encode('utf8') )
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

def extend_project_info( session, projects, page, pnb ):
    soup = BeautifulSoup( page, "html.parser" )
    all_code = soup.find_all("div", "code-list-item")
    added_projects = {}
    for code_item in all_code:
        six.print_('.', end='', flush=True)
        # enc_print( 'code_item', str(code_item ) )
        proj_auth_name = code_item.div.div.a.string
        # enc_print( 'proj_auth_name',  proj_auth_name )
        proj_auth, proj_name = proj_auth_name.split('/')
        path_item = code_item.div.div.a.next_sibling.next_sibling
        # enc_print( 'path_item', path_item )
        proj_luau_relpath =  path_item['title']
        proj_luau_fullpath = 'https://github.com/' + path_item['href']
        # enc_print( 'proj_luau_fullpath', proj_luau_fullpath )
        # enc_print( 'proj_luau_relpath', proj_luau_relpath )

        if not fname_is_luaunit( proj_luau_relpath ): 
            continue

        if NONET:
            luau_version = NO_VERSION
        else:
            luau_version = get_luaunit_version( session, proj_luau_fullpath )
            if not luau_version:
                continue
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
        d['luau_file_search_page'].append( six.u('%s' % pnb) )

        # add extra github data about project
        repo = gh_api().get_repo( proj_auth_name )
        extra_data = {
            'forks' : repo.forks_count,
            'stars' : repo.stargazers_count,
            'watchers' : repo.watchers_count,
        }
        # enc_print( 'extra_data', extra_data )
        d.update( extra_data )

    return added_projects

def extract_endpage( page ):
    soup = BeautifulSoup( page, "html.parser" )
    next_page = soup.find("a", "next_page")
    maxp = next_page.previous_sibling.previous_sibling.string
    return int(maxp)

def analyse_projects_data( extra_request=[] ):
    session, success = gh_login()
    if not success:
        return
    projects = {}

    page = gh_data_fetch_and_archive_have_luaunit_file(session)
    startpage = 1
    endpage = extract_endpage( page )
    if START_PAGE:
        startpage = max(START_PAGE, startpage)
    if END_PAGE:
        endpage = min(END_PAGE, endpage)

    print('Scanning github...')
    for pnb in range(startpage, endpage+1):
        six.print_('P%d' % pnb, end='', flush=True)
        page = gh_data_fetch_and_archive_have_luaunit_file(session, pnb)

        page_projects = extend_project_info( session, projects, page, pnb )
        # print( page_projects )

    all_versions_and_proj = [ (p['luau_version'], p['proj_path']) for p in projects.values()]
    all_versions = set( v for (v,p) in all_versions_and_proj )
    nbproj_with_version = [ (targetv, len( list( filter( lambda vp: vp[0] == targetv, all_versions_and_proj) ) ) )  for targetv in all_versions ]
    nbproj_with_version.sort()

    today = datetime.date.today().isoformat()
    update_db_list( GH_LUAU_VERSIONS, (today, nbproj_with_version ) )
    save_db_dict()

    # step1 archive the already collected info
    f = open('projects.csv', 'wb')
    fields = ( 'name', 'author', 'proj_path', 'luau_file_search_page', 'luau_version', 'stars', 'watchers', 'forks', 'luau_rel_path', 'luau_full_path')
    f.write( b';'.join( s.encode('cp1252', 'replace') for s in fields ) )
    f.write(b'\n')
    try:
        for proj_info in sorted( projects.keys() ):
            for k in fields:
                v = projects[proj_info][k]
                if type(v) in six.integer_types:
                    f.write( b'%d' % v )
                elif type(v) == six.text_type:
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
        six.print_('Error when handling field %s' % (six.b(k)) )
        six.print_('from project %s' % (six.b(projects[proj_info]['proj_path']) ))
        six.print_('of page %s' % (six.b(projects[proj_info]['luau_file_search_page'] ) ) )
        raise
    finally:
        f.close()

def gh_api():
    if not HAS_GH_API:
        print("GitHub API not available...")
        sys.exit(1)

    # static var stored as function attribute
    if not hasattr(gh_api, 'session'):
        gh_api.session = Github( *get_gh_user_pwd() )
    return gh_api.session

def watch_gh_metadata():
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


################################################################################333
#
#               Command Line Interface


ACTIONS = {
    'watch_luarocks': watch_luarocks,
    'watch_gh_data':  watch_gh_data,
    'watch_gh_metadata':  watch_gh_metadata,
    'gh_push': git_commit_and_push,
    'analyse_projects_data': analyse_projects_data,
}
HELP_ACTIONS = 'Possible ACTIONS: %s' % ', '.join(ACTIONS.keys())


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument( '--net-sleep' )
    parser.add_argument( '--no-network', action='store_true' )
    parser.add_argument( '--start-page' )
    parser.add_argument( '--end-page' )
    parser.add_argument( '--print-db', action='store_true' )
    parser.add_argument( 'actions', nargs='*', help=HELP_ACTIONS )
    result = parser.parse_args()

    if len(result.actions) < 1:
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

        # git_pull()
    init_db_dict()

    for action in result.actions:
        ACTIONS[action]()

    if result.print_db:
        pprint.pprint( dbdict )
    save_db_dict()

