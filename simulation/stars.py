
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


POLARIS = Star(ra=0.662285, dec=1.557953, hipparcos=11767, name='polaris')
STARS = [
    Star(ra=4.119229, dec=1.357770, hipparcos=77055, name=''),
    Star(ra=4.265185, dec=1.322169, hipparcos=79822, name=''),
    Star(ra=4.017439, dec=1.253739, hipparcos=75097, name=''),
    Star(ra=3.886441, dec=1.294257, hipparcos=72607, name=''),
    Star(ra=4.119229, dec=1.357770, hipparcos=77055, name=''),
    Star(ra=4.389369, dec=1.431820, hipparcos=82080, name=''),
    Star(ra=4.591154, dec=1.511217, hipparcos=85822, name=''),
    Star(ra=0.662285, dec=1.557953, hipparcos=11767, name=''),
]
