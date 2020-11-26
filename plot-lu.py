import ast
from pprint import pprint
from datetime import date as dt_date
from datetime import timedelta as dt_timedelta

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

ALPHA = 0.10

def import_dbdict():
    with open('dbdict.txt') as f:
        fcontent = f.read()
    d = ast.literal_eval(fcontent)
    return d


def moving_exp_avg(data_date, data_val):
    prev_avg = None
    prev_dt = None
    data_avg = []
    for dt, val in zip(data_date, data_val):
        if (prev_avg, prev_dt) == (None, None):
            new_avg = val
        else:
            dt_delta = dt-prev_dt
            if isinstance(dt_delta, dt_timedelta):
                dt_delta = dt_delta.days
            new_avg = prev_avg + ALPHA*(val-prev_avg)
        data_avg.append((dt, new_avg))
        prev_avg = new_avg
        prev_dt = dt
    return data_avg



def graphics_luarocks(data):

    cum_dl = list(reversed(data[NB_DL_LUAROCKS_TOTAL]))
    cum_dl_date = [dates.datestr2num(v[0]) for v in cum_dl]
    cum_dl_val  = [v[1] for v in cum_dl]

    daily_dl = [(v2-v1)/(dt2-dt1) for v1,v2,dt1,dt2 in zip(cum_dl_val[:-1], cum_dl_val[1:], cum_dl_date[:-1], cum_dl_date[1:])]
    daily_dl_avg = moving_exp_avg(cum_dl_date, daily_dl)
    daily_dl_avg_date = [ v[0] for v in daily_dl_avg ]
    daily_dl_avg_nb   = [ v[1] for v in daily_dl_avg ]


    plot_cumulated_and_avg(
        'Cumulated download of LuaUnit package',
        cum_dl_date, cum_dl_val,

        'Average daily download of LuaUnit package',
        daily_dl_avg_date, daily_dl_avg_nb,
    )

def graphics_projects_using_lu(data):

    nb_ref_lu = list(reversed(data[GH_DATA_REF_LUAUNIT_CODE]))
    nb_ref_lu_date = [dt_date.fromisoformat(v[0]) for v in nb_ref_lu]
    nb_ref_lu_val  = [v[1] for v in nb_ref_lu]


    # fill dates for each quarter
    last_date = dt_date(2016,1,1)
    quart_dates = [last_date]
    while last_date < dt_date.today():
        if last_date.month < 9:
            new_date = dt_date(last_date.year, last_date.month+3, 1)
        else:
            new_date = dt_date(last_date.year+1, 1, 1)
        quart_dates.append(new_date)
        last_date = new_date

    # keep only quarter dates after the start of our date series
    quart_dates = [qdt for qdt in quart_dates if qdt >= nb_ref_lu_date[0]]

    quart_dt_val = []
    # find one date for each quarter immediatly after the start of the quarter
    for qdt in quart_dates:
        # find first date after this quarter
        # keep the date and the value for this quarter
        post_dt_nb_ref_lu = [(dt,val) for (dt,val) in zip(nb_ref_lu_date, nb_ref_lu_val) if dt >= qdt]
        if len(post_dt_nb_ref_lu) == 0:
            # end of our series
            break
        quart_dt_val.append((qdt, post_dt_nb_ref_lu[0][1]))

    # now we have dates for each quarter with a value
    quart_dt_val_delta = [ (v1[0], (v2[1]-v1[1])/(v2[0]-v1[0]).days*92) for v1, v2 in zip(quart_dt_val[:-1], quart_dt_val[1:]) ]
    quart_dt_dates = [v[0] for v in quart_dt_val_delta ]
    quart_dt_delta = [v[1] for v in quart_dt_val_delta ]

    quart_dt_avg_delta = moving_exp_avg(quart_dt_dates, quart_dt_delta)
    quart_dt_avg_dates = [v[0] for v in quart_dt_avg_delta ]
    quart_dt_avg_delta = [v[1] for v in quart_dt_avg_delta ]


    fig, (ax1, ax2) = pyplot.subplots(2,1)
    locator = dates.AutoDateLocator()
    formatter = dates.ConciseDateFormatter(locator)

    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    # ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '%dk' % (x//1000)))
    ax1.plot_date(nb_ref_lu_date, nb_ref_lu_val, '-')
    ax1.set_title('GitHub projects referencing LuaUnit')
    ax1.grid(True)

    ax2.xaxis.set_major_locator(ticker.FixedLocator([dates.date2num(v) for v in quart_dt_dates]))
    # ax2.xaxis.set_major_locator(ticker.IndexLocator(92, dates.date2num(quart_dates[0])))
    # ax2.xaxis.set_major_formatter(formatter)
    ax2.xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda x, pos: ( ('Q%d-%02d' % (dates.num2date(x).month//3+1, dates.num2date(x).year%100)) )))
    ax2.bar(quart_dt_dates, quart_dt_delta, 80)
    ax2.set_title('New projects referencing LuaUnit per quarter')
    ax2.grid(True)
    ax2.plot_date(quart_dt_avg_dates, quart_dt_avg_delta, 'r-',)


    pyplot.tight_layout()
    pyplot.show()


def plot_cumulated_and_avg(title_data_sum, x_data_sum, y_data_sum, 
                           title_data_avg, x_data_avg, y_data_avg):

    fig, (ax1, ax2) = pyplot.subplots(2,1)
    locator = dates.AutoDateLocator()
    formatter = dates.ConciseDateFormatter(locator)

    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(formatter)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '%dk' % (x//1000)))
    ax1.plot_date(x_data_sum, y_data_sum, '-')
    ax1.set_title(title_data_sum)
    ax1.grid(True)

    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(formatter)
    ax2.plot_date(x_data_avg, y_data_avg, '-')
    ax2.set_title(title_data_avg)
    ax2.grid(True)


    pyplot.tight_layout()
    pyplot.show()


def main():
    data = import_dbdict()
    # graphics_luarocks(data)
    graphics_projects_using_lu(data)

if __name__ == '__main__':
    main()

# TODO:
# - with the quarter graphics, the last quarter value should be trimmed off and is forced to null ?
