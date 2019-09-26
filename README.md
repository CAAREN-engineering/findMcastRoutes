## Python script to query Internet2 router proxy for active multicast routes.

Usage:
```
usage: find_src_i2.py [-h] [-c]

Query I2 router proxy for active multicast routes

optional arguments:
  -h, --help      show this help message and exit
  -c , --cutoff   minimum number of pps to be included in report
                  (default is 9)
```

Outputs two files- a CSV of all the data gathered, and an m3u playlist of AMT URIs

## Notes
Needs work to deduplicate entries
Would be nice to get information about source addr (hostname / whois)