from skyfield.api import Star, load
from skyfield.data import hipparcos

with load.open(hipparcos.URL) as f:
    df = hipparcos.load_dataframe(f)

URSA_MINOR = [77055, 79822, 75097, 72607, 77055, 82080, 85822, 11767]
## ORION = ([24436, 27366, 26727, 27989, 28614, 29426, 28716] +
##          [29426, 29038, 27913] +
##          [27989, 26207, 25336, 22449, 22509, 22845] +
##          [22449, 22549, 22797, 23123] +
##          [25336, 25930, 24674, 24436] + [26311])

ALL_STARS = URSA_MINOR # + ORION

def star(n, name=''):
    star = Star.from_dataframe(df.loc[n])
    return 'Star(ra=%f, dec=%f, hipparcos=%d, name=%r)' % (star.ra.radians,
                                                           star.dec.radians,
                                                           n,
                                                           name)

print("""
from dataclasses import dataclass

@dataclass
class Star:
    ra: float
    dec: float
    hipparcos: int
    name: str = ''

@dataclass
class SkyPoint:
    ra: float
    dec: float
""")
print()
print('POLARIS = %s' % star(11767, 'polaris'))
print('STARS = [')
for n in ALL_STARS:
    print('    %s,' % star(n))
print(']')
