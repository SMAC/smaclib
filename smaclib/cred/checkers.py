
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

    def __init__(self, home_root):
        self.home_root = home_root

    def request_avatar_id(self, creds):
        try:
            childpath = self.home_root.child(creds.username)
        except filepath.InsecurePath:
            pass
        else:
            if childpath.parent() == self.home_root and childpath.isdir():
                return defer.succeed(creds.username)
        return defer.fail(error.UnauthorizedLogin())
    requestAvatarId = request_avatar_id # Twisted naming conventions