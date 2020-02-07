
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


STARS = [
    Star(ra=4.119229, dec=1.357770, hipparcos=77055),
    Star(ra=4.265185, dec=1.322169, hipparcos=79822),
    Star(ra=4.017439, dec=1.253739, hipparcos=75097),
    Star(ra=3.886441, dec=1.294257, hipparcos=72607),
    Star(ra=4.119229, dec=1.357770, hipparcos=77055),
    Star(ra=4.389369, dec=1.431820, hipparcos=82080),
    Star(ra=4.591154, dec=1.511217, hipparcos=85822),
    Star(ra=0.662285, dec=1.557953, hipparcos=11767),
    Star(ra=2.887821, dec=0.984058, hipparcos=53910),
    Star(ra=2.896071, dec=1.077760, hipparcos=54061),
    Star(ra=3.208893, dec=0.995407, hipparcos=59774),
    Star(ra=3.114667, dec=0.937150, hipparcos=58001),
    Star(ra=3.377331, dec=0.976684, hipparcos=62956),
    Star(ra=3.507779, dec=0.958629, hipparcos=65378),
    Star(ra=3.610835, dec=0.860680, hipparcos=67301),
]
