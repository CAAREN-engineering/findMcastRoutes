#!/usr/bin/env python3

"""
Original by William Zhang
https://github.com/willzhang05/senior-research

Script to query I2 router proxy for active multicast routes

modified by akg
# TODO deduplication needs work
"""


from argparse import ArgumentParser, RawTextHelpFormatter
import datetime
import pandas as pd
import os
import requests
import re
import time
from prettytable import PrettyTable


parser = ArgumentParser(description="Query I2 router proxy for active multicast routes", formatter_class=RawTextHelpFormatter)

parser.add_argument("-c", "--cutoff", action='store', default=9, metavar="",
                    help="minimum number of pps to be included in report\n(default is 9)")

args = parser.parse_args()

cutoff = args.cutoff


class Source:
    def __init__(self, source, group, stats, router):
        self.source = source
        self.group = group
        st = stats.split(',')
        self.speed = int(re.sub(r'[^0-9]', '', st[0]))
        self.pps = int(re.sub(r'[^0-9]', '', st[1]))
        self.packets = int(re.sub(r'[^0-9]', '', st[2]))
        self.router = router

    def __repr__(self):
        return 'Group: {0:25s}\tSource: {1:25s}\tRouter: {2:18s}\tPackets/Second: {3:6d}'.format(self.group, self.source, self.router, self.pps)

    def __str__(self):
        return 'Group: {0:25s}\tSource: {1:25s}\tRouter: {2:18s}\tPackets/Second: {3:6d}'.format(self.group, self.source, self.router, self.pps)

    def __eq__(self, other):
        return self.source == other.source and self.group == other.group and self.router == self.router
    
    def __lt__(self, other):
        return self.group < other.group

    def __hash__(self):
        return hash(self.__repr__())


def getData():
    BASE_URL = 'https://routerproxy.grnoc.iu.edu/internet2/'
    routers = 'ips.txt'
    devices = set()
    with open(routers, 'r') as f:
        ip = f.readline()
        while ip != '':
            devices.add(ip.strip())
            ip = f.readline()
    devices = list(devices)      
    output = set()
    tdict = {}              # temp dict to be appended to tlist that will be used to create data frame
    tlist = []              # temp list to be used to create data frame
    for device in devices:
        r = requests.get(BASE_URL + '?method=submit&device=' + device + '&command=show multicast&menu=0&arguments=route detail')
        new_text = re.sub(r'&[^\s]{2,4};|[\r]', '', r.text)
        s_new_text = new_text.split('\n')
        fields = dict()
        for i in range(1, len(s_new_text) - 1):
            s_line = s_new_text[i].split(':', 1)
            if s_line[0] == '':
                if 'Group' in fields:
                    s = Source(fields['Source'], fields['Group'], fields['Statistics'], device)
                    tdict['group'] = s.group
                    tdict['packets'] = s.packets
                    tdict['pps'] = s.pps
                    tdict['router'] = s.router
                    tdict['source'] = s.source
                    tdict['speed'] = s.speed
                    tlist.append(tdict.copy())
                fields = dict()
            else:
                fields[s_line[0]] = ''.join(s_line[1:])
            if len(tdict) > 0:
                tlist.append(tdict.copy())
        time.sleep(5)
    # create the dataframe
    a = pd.DataFrame(tlist)
    # sort it by pps, packets, source, router
    b = a.sort_values(by=['pps', 'packets', 'source', 'router'], ascending=False)
    # deduplicate
    finalData = b.drop_duplicates()
    return finalData


def processData(inFrame, cutoff):
    """
    process the dataframe-
    sort it
    :param inFrame:
    :return:
    """
    directory = './output/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    timenow = time.strftime("%d%b%Y-%H%M") + '.csv'
    # write full dataframe to CSV
    dframefilename = directory + 'Dataframe-' + timenow + '.csv'
    inFrame.to_csv(dframefilename, index=False)
    # create pretty table and m3u
    playlistfilename = 'Playlist-' + timenow + '.m3u'
    outTable = PrettyTable(['group', 'source', 'pps', 'URI'])
    allURIs = []
    for index, row in inFrame.iterrows():
        group = row['group']
        source = row['source'][:-3]
        pps = row['pps']
        if pps > cutoff:
            amtURI = "amt://" + source + '@' + group
            outTable.add_row([group, source, pps, amtURI])
            allURIs.append(amtURI)
    print(outTable)
    with open(directory + playlistfilename, 'w') as f:
        f.write('\n'.join(allURIs))
    return


def main():
    mcastFrame = getData()
    processData(mcastFrame, cutoff)


if __name__ == '__main__':
  main()

