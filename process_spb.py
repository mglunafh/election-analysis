import csv
import os
import matplotlib.pyplot as plt
import numpy as np
from ik_info import IkInfo


line_as_ik_info_field = {
    '1': "total_voters",
    '2': "given_ballots",
    '3': "found_ballots",
    '4': "spoiled_ballots",
    '5': "yes_votes",
    '6': "no_votes"
}


def extract_ik_info(tik_name, data_file):
    this_tik = IkInfo(tik_name, has_dependent=True)
    with open(data_file, 'r', encoding='utf-8') as tik_data:
        reader = csv.DictReader(tik_data, delimiter=';')
        fields = reader.fieldnames
        uiks = fields[3:-1]     # the header of the table is kinda malformed

        for uik in uiks:
            this_tik.dependent_iks[uik] = IkInfo(uik)

        pos_line_number = fields[0]
        total_column = "Сумма"
        for line in reader:
            # to skip the line without any data and with a question
            # "Do you agree with constitutional amendments?"
            line_number = line[pos_line_number]
            if not line_number:
                continue

            field_to_insert = line_as_ik_info_field[line_number]
            total = int(line[total_column])
            setattr(this_tik, field_to_insert, total)

            for ik_name, ik_info in this_tik.dependent_iks.items():
                value = int(line[ik_name])
                setattr(ik_info, field_to_insert, value)

    this_tik.validate()
    return this_tik


def plot_results(ik_info, recursive=True):

    all_iks = ik_info.get_iks(recursive)
    turnout = []
    yes_votes = []
    no_votes = []
    spoiled_ballots = []
    number_of_iks = 0

    for ik in all_iks:
        turnout.append(ik.get_turnout_percent())
        yes_votes.append(ik.get_yes_percent())
        no_votes.append(ik.get_no_percent())
        spoiled_ballots.append(ik.get_spoiled_percent())
        number_of_iks += 1

    kwargs_yes = {'c': 'r', 'marker': 'o', 's': 2}
    kwargs_no = {'c': 'b', 'marker': 'o', 's': 2}
    kwargs_spoiled = {'c': 'm', 'marker': 'o', 's': 2}
    plt.scatter(turnout, yes_votes, **kwargs_yes)
    plt.scatter(turnout, no_votes, **kwargs_no)
    plt.scatter(turnout, spoiled_ballots, **kwargs_spoiled)
    plt.legend(('percent of YES', 'percent of NO', 'percent of spoiled'))

    plt.title("%s, %d IKs" % (ik_info.name, number_of_iks))
    plt.axis([0, 105, 0, 105])
    plt.xlabel('Turnout')
    plt.ylabel('Percent of votes')
    plt.xticks(np.arange(0, 105, 5))
    plt.yticks(np.arange(0, 105, 5))
    plt.grid()


def plot_distribution(ik_info):
    # Roughly speaking, 'k' is a number on bins in one percent of turnout,
    # k = 1 corresponds to data visualized by Sergey Shpilkin.
    # Higher values of 'k' make artificial peaks around integer values
    # more visible.
    k = 3
    ticks = k * 100 + 1
    t = np.linspace(0, 100, ticks)
    yes_voters = np.zeros(ticks)
    no_voters = np.zeros(ticks)
    spoiled = np.zeros(ticks)

    for uik_info in ik_info.get_iks():
        turnout_rounded = uik_info.get_turnout_percent()
        turnout_ind = int(k * turnout_rounded)
        yes_voters[turnout_ind] += uik_info.yes_votes
        no_voters[turnout_ind] += uik_info.no_votes
        spoiled[turnout_ind] += uik_info.spoiled_ballots

    plt.plot(t, yes_voters, 'r', lw=1)
    plt.plot(t, no_voters, 'b', lw=1)
    plt.plot(t, spoiled, 'm', lw=1)

    plt.title("%s, %d voters" % (ik_info.name, ik_info.total_voters))
    plt.xlim(0, 105)
    plt.xlabel('Turnout')
    plt.ylabel('Number of votes')
    plt.xticks(np.arange(0, 105, 5))
    plt.grid()
    plt.show()


def plot_mean(ik_info):
    turnout = ik_info.get_turnout_percent()
    percent_yes = ik_info.get_yes_percent()
    percent_no = ik_info.get_no_percent()
    kwargs = {'ls': '-.', 'lw': 1}
    plt.axvline(x=turnout, c='g', **kwargs)
    plt.axhline(y=percent_yes, c='r', **kwargs)
    plt.axhline(y=percent_no, c='b', **kwargs)


def plot_histogram(ik_info):
    turnout_threshold = 50
    range = [[turnout_threshold, 105], [50, 105]]
    turnout = []
    yes_percent = []

    for ik in ik_info.get_iks():
        turnout.append(ik.get_turnout_percent())
        yes_percent.append(ik.get_yes_percent())

    plt.hist2d(turnout, yes_percent, bins=400, range=range, cmap='plasma')
    plt.xticks(np.arange(turnout_threshold, 105, 2))
    plt.show()


data_folder = "spb_data"
number_of_tiks = 30
RIK_info_map = {}
spb_ik_info = IkInfo("Saint-Petersburg")
for i in range(1, number_of_tiks + 1):
    tik = "TIK-%02d" % i

    filename = os.path.join(data_folder, tik + ".csv")
    tik_info = extract_ik_info(tik, filename)
    spb_ik_info.add_ik_info(tik_info)

spb_ik_info.validate()
print(spb_ik_info.to_string())

for tik in spb_ik_info.get_iks(recursive=False):
    print(tik.to_string())
    plot_results(tik)
    plot_mean(tik)
    plt.show()
    plot_distribution(tik)

plot_results(spb_ik_info)
plot_mean(spb_ik_info)
plt.show()
plot_distribution(spb_ik_info)

# plot_histogram(spb_ik_info)
