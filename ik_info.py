from collections import OrderedDict
from functools import reduce


field_description = {
    'total_voters': "Amount of potential voters",
    'given_ballots': "Amount of given ballot papers",
    'found_ballots': "Amount of ballots in the ballot boxes",
    'spoiled_ballots': "Amount of spoiled ballots",
    'yes_votes': "YES",
    'no_votes': "NO"
}


class IkInfo:
    dependent_iks = None
    total_voters = 0
    given_ballots = 0
    found_ballots = 0
    spoiled_ballots = 0
    yes_votes = 0
    no_votes = 0

    def __init__(self, name, has_dependent=False):
        self.name = name
        if has_dependent:
            self.dependent_iks = OrderedDict()

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
            self.dependent_iks = OrderedDict()
        self.dependent_iks[ik_info.name] = ik_info
        self.total_voters += ik_info.total_voters
        self.given_ballots += ik_info.given_ballots
        self.found_ballots += ik_info.found_ballots
        self.spoiled_ballots += ik_info.spoiled_ballots
        self.yes_votes += ik_info.yes_votes
        self.no_votes += ik_info.no_votes

    def validate(self):
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

        for field in field_description.keys():
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
