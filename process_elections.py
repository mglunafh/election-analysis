from ik_info import IkInfo
import os
import csv


POS_REGION = 1
POS_TIK = 2
POS_UIK = 3
POS_TOTAL_VOTERS = 4
POS_GIVEN_BALLOTS = 5
POS_FOUND_BALLOTS = 6
POS_SPOILED_BALLOTS = 7
POS_YES_VOTES = 8
POS_NO_VOTES = 9

count = 0
election_data = os.path.join("full_data", "results.txt")

with open(election_data, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter='\t')
    for line in reader:
        count += 1

print("Number of UIKs: %d" % count)
