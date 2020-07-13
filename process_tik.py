import csv
import os
import matplotlib.pyplot as plt
import numpy as np
import collections
from functools import reduce


field_description = {
    'total_voters': "Amount of potential voters",
    'given_ballots': "Amount of given ballot papers",
    'found_ballots': "Amount of ballots in the ballot boxes",
    'spoiled_ballots': "Amount of spoiled ballots",
    'yes_votes': "YES",
    'no_votes': "NO"
}

line_as_ui_info_field = {
    '1': "total_voters",
    '2': "given_ballots",
    '3': "found_ballots",
    '4': "spoiled_ballots",
    '5': "yes_votes",
    '6': "no_votes"
}


class IkInfo:
    dependent_iks = None
    total_voters = 0
    given_ballots = 0
    found_ballots = 0
    spoiled_ballots = 0
    yes_votes = 0
    no_votes = 0

    def __init__(self, name):
        self.name = name

    def to_string(self):
        result = "{name}: total={total:>4}, given={given:>4}, " \
                 "found={found:>4}, spoiled={spoiled:>3}, " \
                 "turnout={turnout:>7.2%}, " \
                 "YES={yes_votes:>4} ({yes_part:>6.2%}), " \
                 "NO={no_votes:>4} ({no_part:>6.2%})"
        return result.format(
            name=self.name,
            total=self.total_voters,
            given=self.given_ballots,
            found=self.found_ballots,
            spoiled=self.spoiled_ballots,
            turnout=float(self.given_ballots) / self.total_voters,
            yes_votes=self.yes_votes,
            yes_part=float(self.yes_votes) / self.found_ballots,
            no_votes=self.no_votes,
            no_part=float(self.no_votes) / self.found_ballots
        )

    def get_turnout_percent(self):
        return 100.0 * self.given_ballots / self.total_voters

    def get_yes_percent(self):
        return 100.0 * self.yes_votes / self.found_ballots

    def get_no_percent(self):
        return 100.0 * self.no_votes / self.found_ballots

    def get_spoiled_percent(self):
        return 100.0 * self.spoiled_ballots / self.found_ballots

    def get_number_of_iks(self):
        return 0 if not self.dependent_iks else len(self.dependent_iks)

    def get_iks(self, recursive=True):
        if not self.dependent_iks:
            yield self
        else:
            for ik in self.dependent_iks.values():
                if recursive:
                    yield from ik.get_iks()
                else:
                    yield ik

    def get_ik_by_name(self, ik_name):
        if self.name == ik_name:
            return self
        if ik_name in self.dependent_iks:
            return self.dependent_iks[ik_name]
        for ik in self.dependent_iks:
            t = ik.get_ik_by_name(ik_name)
            if t:
                return t
        return None

    def add_ik_info(self, ik_info):
        if not self.dependent_iks:
            self.dependent_iks = collections.OrderedDict()
        self.dependent_iks[ik_info.name] = ik_info
        self.total_voters += ik_info.total_voters
        self.given_ballots += ik_info.given_ballots
        self.found_ballots += ik_info.found_ballots
        self.spoiled_ballots += ik_info.spoiled_ballots
        self.yes_votes += ik_info.yes_votes
        self.no_votes += ik_info.no_votes

    @staticmethod
    def extract_ik_info(tik_name, data_file):
        this_tik = IkInfo(tik_name)
        with open(data_file, 'r', encoding='utf-8') as tik_data:
            reader = csv.DictReader(tik_data, delimiter=';')
            fields = reader.fieldnames
            uiks = fields[3:-1]     # the header of the table is kinda malformed
            this_tik.__init_dict(uiks)

            pos_line_number = fields[0]
            total_column = "Сумма"
            for line in reader:
                # to skip the line without any data and with a question
                # "Do you agree with constitutional amendments?"
                line_number = line[pos_line_number]
                if not line_number:
                    continue
                field_to_insert = line_as_ui_info_field[line_number]
                total = int(line[total_column])
                setattr(this_tik, field_to_insert, total)

                for ik_name, ik_info in this_tik.dependent_iks.items():
                    value = int(line[ik_name])
                    setattr(ik_info, field_to_insert, value)

        this_tik.validate(data_file)
        return this_tik

    def __init_dict(self, ik_names):
        self.dependent_iks = collections.OrderedDict()
        for uik in ik_names:
            self.dependent_iks[uik] = IkInfo(uik)

    def validate(self, data_file=None):
        self.__validate_found_ballots()
        self.__validate_given_ballots()
        self.__validate_total_voters()
        self.__validate_dependent_iks_numbers()

    def __validate_found_ballots(self):
        found_ballots = self.yes_votes + self.no_votes + self.spoiled_ballots
        if self.found_ballots != found_ballots:
            msg = "IK {ik_name}.\n Yes votes ({yes}) + No votes ({no}) + " \
                  "spoiled ballots ({spoiled}) != found_ballots {found}"
            args = {
                "ik_name": self.name,
                "yes": self.yes_votes,
                "no": self.no_votes,
                "spoiled": self.spoiled_ballots,
                "found": self.found_ballots
            }
            raise AssertionError(msg.format(**args))

    def __validate_given_ballots(self):
        if self.given_ballots < self.found_ballots:
            msg = "IK {ik_name}. Given ballots ({given}) is less " \
                  "than found ballots ({found})".format(
                ik_name=self.name,
                given=self.given_ballots,
                found=self.found_ballots)
            raise AssertionError(msg)

    def __validate_total_voters(self):
        if self.total_voters < self.given_ballots:
            msg = "IK {ik_name}. Total voters ({voters}) is less " \
                  "than given ballots ({given})".format(
                ik_name=self.name,
                voters=self.total_voters,
                given=self.given_ballots)
            raise AssertionError(msg)

    def __validate_dependent_iks_numbers(self):
        if not self.dependent_iks:
            return

        for ik in self.dependent_iks.values():
            ik.validate()

        for field in line_as_ui_info_field.values():
            total_calc = reduce((lambda acc, ik: acc + getattr(ik, field)),
                                self.dependent_iks.values(), 0)
            total = getattr(self, field)
            if total != total_calc:
                msg = "IK {ik_name}. '{meaning}': total={total}," \
                      " but sum={sum}".format(
                    ik_name=self.name,
                    total=total,
                    sum=total_calc,
                    meaning=field_description[field])
                raise AssertionError(msg)


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

    plt.title(ik_info.name)
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


data_folder = "data"
number_of_tiks = 30
RIK_info_map = {}
spb_ik_info = IkInfo("Saint-Petersburg")
for i in range(1, number_of_tiks + 1):
    tik = "TIK-%02d" % i

    filename = os.path.join(data_folder, tik + ".csv")
    tik_info = IkInfo.extract_ik_info(tik, filename)
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
