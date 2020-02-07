import numpy as np
from skyfield.api import Star, load
from skyfield.data import hipparcos

with load.open(hipparcos.URL) as f:
    df = hipparcos.load_dataframe(f)

# POLARIS is 11767
URSA_MINOR = [77055, 79822, 75097, 72607, 77055, 82080, 85822, 11767]
URSA_MAJOR = [53910, 54061, 59774, 58001, 62956, 65378, 67301]


## URSA_MAJOR = [67301, 65378, 62956, 59774, 58001, 57399, 55219, 55203,
##               57399, 54539, 50801, 50372,
##               59774, 54061, 53910, 58001,
##               54061, 46733, 41704, 48319, 53910,
##               48319, 46853, 44127, 44471]



## ORION = ([24436, 27366, 26727, 27989, 28614, 29426, 28716] +
##          [29426, 29038, 27913] +
##          [27989, 26207, 25336, 22449, 22509, 22845] +
##          [22449, 22549, 22797, 23123] +
##          [25336, 25930, 24674, 24436] + [26311])

ALL_STARS = URSA_MINOR + URSA_MAJOR # + ORION

def star(s, n):
    return 'Star(ra=%f, dec=%f, hipparcos=%d)' % (s.ra.radians,
                                                  s.dec.radians,
                                                  n)

print("""
from dataclasses import dataclass

@dataclass
class Star:
    ra: float
    dec: float
    hipparcos: int

@dataclass
class SkyPoint:
    ra: float
    dec: float
""")
print()
print('STARS = [')
for n in ALL_STARS:
    if df.loc[n].magnitude >= 5:
        # ignore faint stars
        continue
    s = Star.from_dataframe(df.loc[n])
    if np.isnan(s.ra.radians) or np.isnan(s.dec.radians):
        continue
    print('    %s,' % star(s, n))
print(']')
