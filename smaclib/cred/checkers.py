
from twisted.cred import error
from twisted.cred import checkers
from twisted.cred import credentials
from twisted.internet import defer
from twisted.python import filepath

from zope.interface import implements


class HomeDirectoryExistence(object):
    implements(checkers.ICredentialsChecker)

    credentialInterfaces = (credentials.IUsernamePassword,
                            credentials.IUsernameHashedPassword)

    def __init__(self, *home_roots):
        self.home_roots = home_roots

    def requestAvatarId(self, creds):
        for home in self.home_roots:
            try:
                childpath = home.child(creds.username)
            except filepath.InsecurePath:
                pass
            else:
                if childpath.parent() == home and childpath.isdir():
                    return defer.succeed(creds.username)
        else:
            return defer.fail(error.UnauthorizedLogin())
