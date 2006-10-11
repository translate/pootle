from Pootle import potree
from jToolkit import prefs
from Pootle.filelocations import prefsfile
import os

serverprefs = prefs.PrefsParser()
serverprefs.parsefile(prefsfile)
instance = serverprefs

instancename = 'Pootle'

# find the instance prefs
try:
    instance = serverprefs
    if instancename:
        for part in instancename.split("."):
            instance = getattr(instance, part)
except AttributeError:
    errormessage = "Prefs file %r has no attribute %r\nprefs file is %r, attributes are %r" \
                   % (prefsfile, instancename, serverprefs, [top[0] for top in serverprefs.iteritems()])
    raise AttributeError(errormessage)

instance.potree = potree.POTree(instance)


users = prefs.PrefsParser()
users.parsefile(instance.userprefs)
