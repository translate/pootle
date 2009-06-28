#!/usr/bin/env python

from distutils.core import setup, Extension, Distribution, Command
import distutils.sysconfig
import sys
import os.path
from Pootle.pootle_app import __version__
from Pootle import __doc__
try:
  import py2exe
  build_exe = py2exe.build_exe.py2exe
  Distribution = py2exe.Distribution
except ImportError:
  py2exe = None
  build_exe = Command

# TODO: check out installing into a different path with --prefix/--home

join = os.path.join

pootleversion = __version__.sver

packagesdir = distutils.sysconfig.get_python_lib()
sitepackages = packagesdir.replace(sys.prefix + os.sep, '')

infofiles = [(join(sitepackages,'Pootle'),
             [join('Pootle',filename) for filename in 'ChangeLog', 'COPYING', 'LICENSE', 'README'])]
initfiles = [(join(sitepackages,'Pootle'),[join('Pootle','__init__.py')])]

packages = [
  "Pootle.tools", 
  "Pootle.auth", 
  "Pootle.i18n", 
  "Pootle.scripts", 
  "Pootle.middleware", 
  "Pootle.pootle_app",
]
pootlescripts = [join('Pootle', 'PootleServer'), join('Pootle', 'tools', 'updatetm')]

def addsubpackages(subpackages):
  for subpackage in subpackages:
    initfiles.append((join(sitepackages, 'Pootle', subpackage),
                      [join('Pootle', subpackage, '__init__.py')]))
    for infofile in ('README', 'TODO'):
      infopath = join('translate', subpackage, infofile)
      if os.path.exists(infopath):
        infofiles.append((join(sitepackages, 'Pootle', subpackage), [infopath]))
    packages.append("Pootle.%s" % subpackage)

#Enter the codes for all languages that must be packaged here
#approvedlanguages = ['af', 'ar', 'eu', 'ca', 'zh_CN', 'zh_HK', 'da', 'nl', 'fi', 'fr', 'gl', 'de', 'hu', 'it', 'ja', 'mt',  'pt', 'sl', 'es', 'sv', 'vi', 'templates']

class build_exe_map(build_exe):
    """distutils py2exe-based class that builds the exe file(s) but allows mapping data files"""
    def reinitialize_command(self, command, reinit_subcommands=0):
        if command == "install_data":
            install_data = build_exe.reinitialize_command(self, command, reinit_subcommands)
            install_data.data_files = self.remap_data_files(install_data.data_files)
            return install_data
        return build_exe.reinitialize_command(self, command, reinit_subcommands)

    def remap_data_files(self, data_files):
        """maps the given data files to different locations using external map_data_file function"""
        new_data_files = []
        for f in data_files:
            if type(f) in (str, unicode):
                f = map_data_file(f)
            else:
                datadir, files = f
                datadir = map_data_file(datadir)
                if datadir is None:
                  f = None
                else:
                  f = datadir, files
            if f is not None:
              new_data_files.append(f)
        return new_data_files

class InnoScript:
    """class that builds an InnoSetup script"""
    def __init__(self, name, lib_dir, dist_dir, exe_files = [], other_files = [], install_scripts = [], version = "1.0"):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir.endswith(os.sep):
            self.dist_dir += os.sep
        self.name = name
        self.version = version
        self.exe_files = [self.chop(p) for p in exe_files]
        self.other_files = [self.chop(p) for p in other_files]
        self.install_scripts = install_scripts

    def getcompilecommand(self):
        try:
            import _winreg
            compile_key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "innosetupscriptfile\\shell\\compile\\command")
            compilecommand = _winreg.QueryValue(compile_key, "")
            compile_key.Close()
        except:
            compilecommand = "compil32.exe"
        return compilecommand

    def chop(self, pathname):
        """returns the path relative to self.dist_dir"""
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]

    def create(self, pathname=None):
        """creates the InnoSetup script"""
        if pathname is None:
          self.pathname = os.path.join(self.dist_dir, self.name + os.extsep + "iss")
        else:
          self.pathname = pathname
        ofi = self.file = open(self.pathname, "w")
        print >> ofi, "; WARNING: This script has been created by py2exe. Changes to this script"
        print >> ofi, "; will be overwritten the next time py2exe is run!"
        print >> ofi, r"[Setup]"
        print >> ofi, r"AppName=%s" % self.name
        print >> ofi, r"AppVerName=%s %s" % (self.name, self.version)
        print >> ofi, r"DefaultDirName={pf}\%s" % self.name
        print >> ofi, r"DefaultGroupName=%s" % self.name
        print >> ofi, r"OutputBaseFilename=%s-%s-setup" % (self.name, self.version)
        print >> ofi
        print >> ofi, r"[Files]"
        for path in self.exe_files + self.other_files:
            print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (path, os.path.dirname(path))
        print >> ofi
        print >> ofi, r"[Icons]"
        for path in self.exe_files:
            if path in self.install_scripts:
                continue
            linkname = os.path.splitext(os.path.basename(path))[0]
            print >> ofi, r'Name: "{group}\%s"; Filename: "{app}\%s"; WorkingDir: "{app}"; Flags: dontcloseonexit' % \
                  (linkname, path)
        print >> ofi, 'Name: "{group}\Uninstall %s"; Filename: "{uninstallexe}"' % self.name
        if self.install_scripts:
            print >> ofi, r"[Run]"
            for path in self.install_scripts:
                print >> ofi, r'Filename: "{app}\%s"; WorkingDir: "{app}"; Parameters: "-install"' % path
            print >> ofi
            print >> ofi, r"[UninstallRun]"
            for path in self.install_scripts:
                print >> ofi, r'Filename: "{app}\%s"; WorkingDir: "{app}"; Parameters: "-remove"' % path
        print >> ofi
        ofi.close()

    def compile(self):
        """compiles the script using InnoSetup"""
        shellcompilecommand = self.getcompilecommand()
        compilecommand = shellcompilecommand.replace('"%1"', self.pathname)
        result = os.system(compilecommand)
        if result:
            print "Error compiling iss file"
            print "Opening iss file, use InnoSetup GUI to compile manually"
            os.startfile(self.pathname)

class build_installer(build_exe_map):
    """distutils class that first builds the exe file(s), then creates a Windows installer using InnoSetup"""
    description = "create an executable installer for MS Windows using InnoSetup and py2exe"
    user_options = getattr(build_exe, 'user_options', []) + \
        [('install-script=', None,
          "basename of installation script to be run after installation or before deinstallation")]

    def initialize_options(self):
        build_exe.initialize_options(self)
        self.install_script = None

    def run(self):
        # First, let py2exe do it's work.
        build_exe.run(self)
        lib_dir = self.lib_dir
        dist_dir = self.dist_dir
        # create the Installer, using the files py2exe has created.
        exe_files = self.windows_exe_files + self.console_exe_files
        install_scripts = self.install_script
        if isinstance(install_scripts, (str, unicode)):
            install_scripts = [install_scripts]
        script = InnoScript(self.distribution.metadata.name, lib_dir, dist_dir, exe_files, self.lib_files, version=self.distribution.metadata.version, install_scripts=install_scripts)
        print "*** creating the inno setup script***"
        script.create()
        print "*** compiling the inno setup script***"
        script.compile()
        # Note: By default the final setup.exe will be in an Output subdirectory.

def map_data_file (data_file):
  """remaps a data_file (could be a directory) to a different location
  This version gets rid of Lib\\site-packages, etc"""
  data_parts = data_file.split(os.sep)
  if data_parts[:2] == ["Lib", "site-packages"]:
    data_parts = data_parts[2:]
    if data_parts:
      data_file = os.path.join(*data_parts)
    else:
      data_file = ""
  if data_parts[:1] == ["Pootle"]:
    data_parts = data_parts[1:]
    if data_parts:
      data_file = os.path.join(*data_parts)
    else:
      data_file = ""
  return data_file

def getdatafiles():
  datafiles = initfiles + infofiles
  def listfiles(srcdir):
    return join(sitepackages, srcdir), [join(srcdir, f) for f in os.listdir(srcdir) if os.path.isfile(join(srcdir, f))]
  pootlefiles = [(join(sitepackages, 'Pootle'), [join('Pootle', 'pootle.prefs'), join('Pootle', 'users.prefs'), join('Pootle', 'pootle.ini')])]
  pootlefiles.append(listfiles(join('Pootle', 'html')))
  pootlefiles.append(listfiles(join('Pootle', 'html', 'images')))
  pootlefiles.append(listfiles(join('Pootle', 'html', 'js')))
  pootlefiles.append(listfiles(join('Pootle', 'html', 'js', 'jquery')))
  pootlefiles.append(listfiles(join('Pootle', 'html', 'doc')))
  pootlefiles.append(listfiles(join('Pootle', 'html', 'doc', 'en')))
  basedir, pootlelangs, files = os.walk(join('Pootle', 'po', 'pootle')).next()
  for dir in pootlelangs:
    pootlefiles.append(listfiles(join('Pootle', 'po', 'pootle', dir)))
  datafiles += pootlefiles
  return datafiles

def buildinfolinks():
  linkfile = getattr(os, 'symlink', None)
  import shutil
  if linkfile is None:
    linkfile = shutil.copy2
  basedir = os.path.abspath(os.curdir)
  os.chdir("Pootle")
  if os.path.exists("LICENSE") or os.path.islink("LICENSE"):
    os.remove("LICENSE")
  linkfile("COPYING", "LICENSE")
  os.chdir(basedir)
  for infofile in ["COPYING", "README", "LICENSE"]:
    if os.path.exists(infofile) or os.path.islink(infofile):
      os.remove(infofile)
    linkfile(os.path.join("Pootle", infofile), infofile)

def buildmanifest_in(file, scripts):
  """This writes the required files to a MANIFEST.in file"""
  print >>file, "# MANIFEST.in: the below autogenerated by pootlesetup.py from Pootle %s" % pootleversion
  print >>file, "# things needed by translate setup.py to rebuild"
  print >>file, "# informational files"
  for infofile in ("README", "TODO", "ChangeLog", "COPYING", "LICENSE", "*.txt"):
    print >>file, "global-include %s" % infofile
  print >> file, "# scripts which don't get included by default in sdist"
  for scriptname in scripts:
    print >>file, "include %s" % scriptname
  # wordlist, portal are in the source tree but unconnected to the python code
  print >>file, "prune wordlist"
  print >>file, "prune pootling"
  print >>file, "prune spelling"
  print >>file, "prune .svn"
  # translate toolkit is in the same source tree but distributed separately
  print >>file, "prune translate"
  print >>file, "prune virtaal"
  print >>file, "prune spelt"
  print >>file, "prune corpuscatcher"
  print >>file, "include Pootle/*.prefs"
  print >>file, "graft Pootle/html"
  print >>file, "graft Pootle/templates"
  print >>file, "graft Pootle/po/pootle"
  print >>file, "# MANIFEST.in: the above autogenerated by pootlesetup.py from Pootle %s" % pootleversion

def fix_bdist_rpm(setupfile):
    """Fixes bdist_rpm to use the given setup filename instead of setup.py"""
    try:
        from distutils.command import bdist_rpm
        build_rpm = bdist_rpm.bdist_rpm
    except ImportError:
        return
    if not hasattr(build_rpm, "_make_spec_file"):
        return
    orig_make_spec_file = build_rpm._make_spec_file
    def fixed_make_spec_file(self):
        """Generate the text of an RPM spec file and return it as a
        list of strings (one per line).
        """
        orig_spec_file = orig_make_spec_file(self)
        return [line.replace("setup.py", setupfile) for line in orig_spec_file]
    build_rpm._make_spec_file = fixed_make_spec_file

class PootleDistribution(Distribution):
  """a modified distribution class for translate"""
  def __init__(self, attrs):
    baseattrs = {}
    py2exeoptions = {}
    py2exeoptions["packages"] = ["Pootle", "encodings"]
    py2exeoptions["compressed"] = True
    jToolkitExcludes = ["PyLucene", "Image", "jToolkit.data.ADODB", "pgdb", "MySQLdb", "cx_Oracle", "pysqlite2"]
    py2exeoptions["excludes"] = ["Tkconstants", "Tkinter", "tcl", "translate.misc._csv"] + jToolkitExcludes
    version = attrs.get("version", pootleversion)
    py2exeoptions["dist_dir"] = "Pootle-%s" % version
    options = {"py2exe": py2exeoptions}
    baseattrs['options'] = options
    if py2exe:
      baseattrs['zipfile'] = "Pootle.zip"
      baseattrs['console'] = pootlescripts
      baseattrs['cmdclass'] = {"py2exe": build_exe_map, "innosetup": build_installer}
      options["innosetup"] = py2exeoptions.copy()
      options["innosetup"]["install_script"] = []
    baseattrs.update(attrs)
    fix_bdist_rpm(os.path.basename(__file__))
    Distribution.__init__(self, baseattrs)

def standardsetup(name, version, custompackages=[], customdatafiles=[]):
  buildinfolinks()
  # TODO: make these end with .py ending on Windows...
  try:
    manifest_in = open("MANIFEST.in", "w")
    buildmanifest_in(manifest_in, pootlescripts)
    manifest_in.close()
  except IOError, e:
    print >> sys.stderr, "warning: could not recreate MANIFEST.in, continuing anyway. Error was %s" % e
  #addsubpackages(subpackages)
  datafiles = getdatafiles()
  ext_modules = []
  dosetup(name, version, packages + custompackages, datafiles + customdatafiles, pootlescripts, ext_modules)

#http://cheeseshop.python.org/pypi?:action=list_classifiers
classifiers = [
  "Development Status :: 5 - Production/Stable",
  "Environment :: Web Environment",
  "Intended Audience :: End Users/Desktop",
  "License :: OSI Approved :: GNU General Public License (GPL)",
  "Programming Language :: Python",
  "Topic :: Software Development :: Localization",
  "Operating System :: OS Independent",
  "Operating System :: Microsoft :: Windows",
  "Operating System :: Unix"
  ]

def dosetup(name, version, packages, datafiles, scripts, ext_modules=[]):
  long_description = __doc__
  description = __doc__.split("\n", 1)[0]
  setup(name=name,
        version=version,
        license="GNU General Public License (GPL)",
        description=description,
        long_description=long_description,
        author="Translate.org.za",
        author_email="translate-devel@lists.sourceforge.net",
        url="http://translate.sourceforge.net/wiki/pootle/index",
        download_url="http://sourceforge.net/project/showfiles.php?group_id=91920&package_id=144807",
        platforms=["any"],
        classifiers=classifiers,
        packages=packages,
        data_files=datafiles,
        scripts=scripts,
        ext_modules=ext_modules,
        distclass=PootleDistribution
        )

if __name__ == "__main__":
  standardsetup("Pootle", pootleversion)

