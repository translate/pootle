#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# glock.py:                 Global mutex
#
# See __doc__ string below.
#
# Requires:
#    - Python 1.5.2 or newer (www.python.org)
#    - On windows: win32 extensions installed
#           (http://www.python.org/windows/win32all/win32all.exe)
#    - OS: Unix, Windows.
#
# The original version of this file can be found at http://rgruet.free.fr/
# It is distributed under the LGPL license (http://www.gnu.org/copyleft/lesser.html)
#----------------------------------------------------------------------------
'''
This module defines the class GlobalLock that implements a global
(inter-process) mutex that works on Windows and Unix, using file-locking on
Unix (I also tried this approach on Windows but got some tricky problems so I
ended using a Win32 Mutex).

@see: class L{GlobalLock} for more details.
'''
__version__ = '0.2.' + '1.2 with jToolkit patches '
__author__ = 'Richard Gruet', 'rjgruet@yahoo.com'
__since__ = '2000-01-22'
__doc__ += '\n@author: %s (U{%s})\n@version: %s' % (__author__[0],
                                            __author__[1], __version__)
__all__ = ['GlobalLock', 'GlobalLockError', 'LockAlreadyAcquired', 'NotOwner']

# Imports:
import sys, string, os, errno, re

# System-dependent imports for locking implementation:
_windows = (sys.platform == 'win32')

if _windows:
    try:
        import win32event, win32api, pywintypes
    except ImportError:
        sys.stderr.write('The win32 extensions need to be installed!')
    try:
        import ctypes
    except ImportError:
        ctypes = None
else:   # assume Unix
    try:
        import fcntl
    except ImportError:
        sys.stderr.write("On what kind of OS am I ? (Mac?) I should be on "
                         "Unix but can't import fcntl.\n")
        raise
    import threading

# Exceptions :
# ----------
class GlobalLockError(Exception):
    ''' Error raised by the glock module.
    '''
    pass

class NotOwner(GlobalLockError):
    ''' Attempt to release somebody else's lock.
    '''
    pass

class LockAlreadyAcquired(GlobalLockError):
    ''' Non-blocking acquire but lock already seized.
    '''
    pass


# Constants
# ---------:
if sys.version[:3] < '2.2':
    True, False = 1, 0  # built-in in Python 2.2+

#----------------------------------------------------------------------------
class GlobalLock:
#----------------------------------------------------------------------------
    ''' A global mutex.

        B{Specification}
        
         - The lock must act as a global mutex, ie block between different
           candidate processus, but ALSO between different candidate
           threads of the same process.
         
         - It must NOT block in case of reentrant lock request issued by
           the SAME thread.
         - Extraneous unlocks should be ideally harmless.

        B{Implementation}

        In Python there is no portable global lock AFAIK. There is only a
        LOCAL/ in-process Lock mechanism (threading.RLock), so we have to
        implement our own solution:

         - Unix: use fcntl.flock(). Recursive calls OK. Different process OK.
           But <> threads, same process don't block so we have to use an extra
           threading.RLock to fix that point.
         - Windows: We use WIN32 mutex from Python Win32 extensions. Can't use
           std module msvcrt.locking(), because global lock is OK, but
           blocks also for 2 calls from the same thread!
    '''
    RE_ERROR_MSG = re.compile ("^\[Errno ([0-9]+)\]")
    
    def __init__(self, fpath, lockInitially=False):
        ''' Creates (or opens) a global lock.

            @param fpath: Path of the file used as lock target. This is also
                         the global id of the lock. The file will be created
                         if non existent.
            @param lockInitially: if True locks initially.
        '''
        if _windows:
            self.name = string.replace(fpath, '\\', '_')
            self.mutex = win32event.CreateMutex(None, lockInitially, self.name)
        else: # Unix
            self.name = fpath
            self.flock = open(fpath, 'w')
            self.fdlock = self.flock.fileno()
            self.threadLock = threading.RLock()
        if lockInitially:
            self.acquire()

    def __del__(self):
        #print '__del__ called' ##
        try: self.release()
        except: pass
        if _windows:
            win32api.CloseHandle(self.mutex)
        else:
            try: self.flock.close()
            except: pass

    def __repr__(self):
        return '<Global lock @ %s>' % self.name
        
    def acquire(self, blocking=True):
        """ Locks. Attemps to acquire a lock.

            @param blocking: If True, suspends caller until done. Otherwise,
            LockAlreadyAcquired is raised if the lock cannot be acquired immediately.

            On windows an IOError is always raised after ~10 sec if the lock
            can't be acquired.
            @exception GlobalLockError: if lock can't be acquired (timeout)
            @exception LockAlreadyAcquired: someone already has the lock and the caller decided not to block
        """
        if _windows:
            if blocking:
                timeout = win32event.INFINITE
            else:
                timeout = 0
            r = win32event.WaitForSingleObject(self.mutex, timeout)
            if r == win32event.WAIT_FAILED:
                raise GlobalLockError("Can't acquire mutex: error")
            if not blocking and r == win32event.WAIT_TIMEOUT:
                raise LockAlreadyAcquired('Lock %s already acquired by '
                                          'someone else' % self.name)
        else:
            # Acquire 1st the global (inter-process) lock:
            if blocking:
                options = fcntl.LOCK_EX
            else:
                options = fcntl.LOCK_EX|fcntl.LOCK_NB
            try:
                fcntl.flock(self.fdlock, options)
            except IOError, message: #(errno 13: perm. denied,
                            #       36: Resource deadlock avoided)
                if not blocking and self._errnoOf (message) == errno.EWOULDBLOCK:
                    raise LockAlreadyAcquired('Lock %s already acquired by '
                                              'someone else' % self.name)
                else:
                    raise GlobalLockError('Cannot acquire lock on "file" '
                                          '%s: %s\n' % (self.name, message))
            #print 'got file lock.' ##
            # Then acquire the local (inter-thread) lock:
            if not self.threadLock.acquire(blocking):
                fcntl.flock(self.fdlock, fcntl.LOCK_UN) # release global lock
                raise LockAlreadyAcquired('Lock %s already acquired by '
                                          'someone else' % self.name)
            #print 'got thread lock.' ##

    def tryacquire(self):
        '''tries to acquire in nonblocking mode, and returns whether successfull or not'''
        try:
            self.acquire(blocking=False)
            return True
        except LockAlreadyAcquired:
            return False

    def forcerelease(self):
	''' Releases the lock if aqcuired ... (by ignoring any exceptions) '''
	try:
		self.release()
	except:
		pass

    def release(self):
        ''' Unlocks. (caller must own the lock!)

            @return: The lock count.
            @exception IOError: if file lock can't be released
            @exception NotOwner: Attempt to release somebody else's lock.
        '''
        if _windows:
            if ctypes:
                result = ctypes.windll.kernel32.ReleaseMutex(self.mutex.handle)
                if not result:
                    raise NotOwner("Attempt to release somebody else's lock")
            else:
                try:
                    win32event.ReleaseMutex(self.mutex)
                    print "released mutex", self.name
                except pywintypes.error, e:
                    errCode, fctName, errMsg =  e.args
                    if errCode == 288:
                        raise NotOwner("Attempt to release somebody else's lock")
                    else:
                        raise GlobalLockError('%s: err#%d: %s' % (fctName, errCode,
                                                                  errMsg))
        else:
            # First, release the local (inter-thread) lock:
            try:
                self.threadLock.release()
            except AssertionError:
                raise NotOwner("Attempt to release somebody else's lock")

            # Then release the global (inter-process) lock:
            try:
                fcntl.flock(self.fdlock, fcntl.LOCK_UN)
            except IOError: # (errno 13: permission denied)
                raise GlobalLockError('Unlock of file "%s" failed\n' %
                                                            self.name)

    def _errnoOf (self, message):
        match = self.RE_ERROR_MSG.search(str(message))
        if match:
            return int(match.group(1))
        else:
            raise Exception ('Malformed error message "%s"' % message)

#----------------------------------------------------------------------------
def test():
#----------------------------------------------------------------------------
    ##TODO: a more serious test with distinct processes !
    
    print 'Testing glock.py...' 
    
    # unfortunately can't test inter-process lock here!
    lockName = 'myFirstLock'
    l = GlobalLock(lockName)
    if not _windows:
        assert os.path.exists(lockName)
    l.acquire()
    l.acquire() # reentrant lock, must not block
    l.release()
    l.release()
    
    try: l.release()
    except NotOwner: pass
    else: raise Exception('should have raised a NotOwner exception')

    # Check that <> threads of same process do block:
    import threading, time
    thread = threading.Thread(target=threadMain, args=(l,))
    print 'main: locking...',
    l.acquire()
    print ' done.'
    thread.start()
    time.sleep(3)
    print '\nmain: unlocking...',
    l.release()
    print ' done.'
    time.sleep(0.1)
    
    print '=> Test of glock.py passed.'
    return l

def threadMain(lock):
    print 'thread started(%s).' % lock
    try: lock.acquire(blocking=False)
    except LockAlreadyAcquired: pass
    else: raise Exception('should have raised LockAlreadyAcquired')
    print 'thread: locking (should stay blocked for ~ 3 sec)...',
    lock.acquire()
    print 'thread: locking done.'
    print 'thread: unlocking...',
    lock.release()
    print ' done.'
    print 'thread ended.'

#----------------------------------------------------------------------------
#       M A I N
#----------------------------------------------------------------------------
if __name__ == "__main__":
    l = test()
