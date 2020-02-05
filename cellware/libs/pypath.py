import os.path
import shutil
from glob import glob

class local(object):

    def __init__(self, path):
        if path is None:
            raise TypeError
        self.strpath = os.path.abspath(str(path))

    def __str__(self):
        return self.strpath

    def __repr__(self):
        return 'PyPath(%r)' % self.strpath

    def __cmp__(self, other):
        if isinstance(other, local):
            return cmp(self.strpath, other.strpath)
        else:
            return cmp(self.strpath, other)

    def __hash__(self):
        return hash(self.strpath)

    @property
    def basename(self):
        return os.path.basename(self.strpath)

    @property
    def purebasename(self):
        name, ext = os.path.splitext(self.basename)
        return name

    @property
    def ext(self):
        name, ext = os.path.splitext(self.basename)
        return ext[:1]

    def dirpath(self):
        return self.__class__(os.path.dirname(self.strpath))

    def listdir(self, pattern='*'):
        pattern = os.path.join(self.strpath, pattern)
        return map(self.__class__, glob(pattern))
            
    def join(self, *parts):
        parts = map(str, parts)
        return self.__class__(os.path.join(self.strpath, *parts))

    def open(self, mode='r', **kwargs):
        return open(self.strpath, mode, **kwargs)

    def write(self, s):
        with open(self.strpath, 'w') as f:
            f.write(s)

    def read(self, mode='r'):
        assert mode in ('r', 'rb')
        with open(self.strpath, mode) as f:
            return f.read()

    def remove(self):
        if self.isdir():
            shutil.rmtree(str(self))
        else:
            os.remove(str(self))

    def ensure(self, dir=False):
        assert dir, 'Only dir=True is supported for now'
        if not os.path.isdir(self.strpath):
            os.mkdir(self.strpath)
        return self

    def copy(self, dst):
        if self.isdir():
            shutil.copytree(self.strpath, str(dst))
        else:
            shutil.copy(self.strpath, str(dst))

    def new(self, ext=None):
        if ext is not None:
            if not ext.startswith('.'):
                ext = '.' + ext
            base, _ = os.path.splitext(self.strpath)
            return self.__class__(base + ext)
        return self.__class__(self.strpath)

    def exists(self):
        return os.path.exists(self.strpath)

    def chdir(self):
        oldcwd = local(os.getcwd())
        os.chdir(self.strpath)
        return oldcwd
    
    def relto(self, path):
        return os.path.relpath(self.strpath, str(path))

    def isdir(self):
        return os.path.isdir(self.strpath)

    def getmtime(self):
        """
        """
        mTime = os.path.getmtime(self.strpath)
        return mTime
