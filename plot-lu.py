import ast
from pprint import pprint

import matplotlib
import matplotlib.pyplot as pyplot
import matplotlib.dates as dates
import matplotlib.ticker as ticker

GH_DATA_HAVE_LUAUNIT_FILE = 'GH_DATA_HAVE_LUAUNIT_FILE'
GH_DATA_REF_LUAUNIT_CODE = 'GH_DATA_REF_LUAUNIT_CODE'
GH_LUAU_VERSIONS = 'GH_LUAU_VERSIONS'
GH_METADATA = 'GH_METADATA'
NB_DL_LUAROCKS_TOTAL = 'NB_DL_LUAROCKS_TOTAL'
NB_DL_LUAROCKS_V33 = 'NB_DL_LUAROCKS_V33'

def import_dbdict():
    with open('dbdict.txt') as f:
        fcontent = f.read()
    d = ast.literal_eval(fcontent)
    return d


def graphics_luarocks(data):

    nb_dl_tot = list(reversed(data[NB_DL_LUAROCKS_TOTAL]))
    nb_dl_tot_date = [dates.datestr2num(v[0]) for v in nb_dl_tot]
    nb_dl_tot_val  = [v[1] for v in nb_dl_tot]


    daily_dl_7d = [ (day_nb1[0], 
                     (day_nb2[1]-day_nb1[1]), 
                     (dates.datestr2num(day_nb2[0]) - dates.datestr2num(day_nb1[0]))
                    )
        for (day_nb1, day_nb2) in zip(nb_dl_tot[:-7], nb_dl_tot[7:]) ]
    daily_dl_7d_date = [ dates.datestr2num(dt) + delta/2 for dt, nb, delta in daily_dl_7d ]
    daily_dl_7d_nb   = [ nb/delta for dt, nb, delta in daily_dl_7d ]

    pprint([(nb, dates.num2date(dt)) for nb, dt in zip(daily_dl_7d_nb, daily_dl_7d_date) if nb > 5000 ])


    # pyplot.xkcd()
    fig, (ax1, ax2) = pyplot.subplots(2,1)
    locator = dates.AutoDateLocator()
    formatter = dates.ConciseDateFormatter(locator)

    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '%dk' % (x//1000)))
    ax1.plot_date(nb_dl_tot_date, nb_dl_tot_val, '-')
    ax1.set_title('Cumulated download of LuaUnit package')
    ax1.grid(True)

    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(formatter)
    ax2.plot_date(daily_dl_7d_date, daily_dl_7d_nb, '-')
    ax2.set_title('Daily download of LuaUnit package (average on 7 days)')
    ax2.grid(True)


    pyplot.tight_layout()
    pyplot.show()


def graphics_projects_using_lu(data):

    nb_ref_lu = list(reversed(data[GH_DATA_REF_LUAUNIT_CODE]))
    nb_ref_lu_date = [dates.datestr2num(v[0]) for v in nb_ref_lu]
    nb_ref_lu_val  = [v[1] for v in nb_ref_lu]


    delta_days = 30
    daily_new_ref_lu = [ (day_nb1[0], 
                     (day_nb2[1]-day_nb1[1]), 
                     (dates.datestr2num(day_nb2[0]) - dates.datestr2num(day_nb1[0]))
                    )
        for (day_nb1, day_nb2) in zip(nb_ref_lu[:-delta_days], nb_ref_lu[delta_days:]) ]
    daily_new_ref_lu_date = [ dates.datestr2num(dt) + delta/2 for dt, nb, delta in daily_new_ref_lu ]
    daily_new_ref_lu_nb   = [ nb/delta*delta_days for dt, nb, delta in daily_new_ref_lu ]

    matplotlib.use('qt5agg')

    # pyplot.xkcd()
    fig, (ax1, ax2) = pyplot.subplots(2,1)
    locator = dates.AutoDateLocator()
    formatter = dates.ConciseDateFormatter(locator)

    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    # ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '%dk' % (x//1000)))
    ax1.plot_date(nb_ref_lu_date, nb_ref_lu_val, '-')
    ax1.set_title('GitHub projects referencing LuaUnit')
    ax1.grid(True)

    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(formatter)
    ax2.plot_date(daily_new_ref_lu_date, daily_new_ref_lu_nb, '-')
    ax2.set_title('New projects referencing LuaUnit per day')
    ax2.grid(True)


    pyplot.tight_layout()
    pyplot.show()



def main():
    data = import_dbdict()
    # graphics_luarocks(data)
    graphics_projects_using_lu(data)

if __name__ == '__main__':
    main()

