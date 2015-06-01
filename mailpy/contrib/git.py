from subprocess import Popen, PIPE, STDOUT


def execute(cmd, stderr_to_stdout=False, stdin=None, cwd=None):
    """Execute a command in the shell and return a tuple (rc, stdout, stderr)"""
    if stderr_to_stdout:
        stderr = STDOUT
    else:
        stderr = PIPE

    p = Popen(cmd, shell=False, bufsize=0, close_fds=True, stdin=stdin, stdout=PIPE, stderr=stderr, cwd=cwd)
    stdout, stderr = p.communicate()

    return p.returncode, stdout, stderr


class GitError(Exception):
    """
    Base exception for all git errors.
    """
    pass


class GitCmdError(GitError):
    """
    Exception for all git command errors.
    """
    def __init__(self, cmd, rc, msg):
        if isinstance(cmd, (list, tuple)):
            cmd = ' '.join(cmd)

        self.cmd = cmd
        self.rc = rc
        self.msg = msg

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.cmd)

    def __str__(self):
        return '%s: error %s: %s' % (self.cmd, self.rc, self.msg)


class Git(object):
    """
    Simple git API.
    """
    _git_cmd = 'git'

    def __init__(self, repo):
        self.repo = repo
        self._added = set()
        self._removed = set()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.repo)

    def _git(self, *args):
        """Run the git command"""
        cmd = (self._git_cmd,) + args
        rc, stdout, _ = execute(cmd, stderr_to_stdout=True, cwd=self.repo)

        if rc != 0:
            raise GitCmdError(cmd, rc, stdout)

        return stdout

    def add(self, *files):
        """git add <files>"""
        res = self._git('add', *files)
        self._added.update(files)

        return res

    def rm(self, *files):
        """git rm <files>"""
        res = self._git('rm', *files)
        self._removed.update(files)

        return res

    def reset(self):
        """git reset staged files"""
        staged_files = self._added | self._removed

        if not staged_files:
            raise GitError('Nothing to reset')

        res = self._git('reset', '--', *staged_files)
        self._added.clear()

        if self._removed:
            self._git('checkout', self._removed)
            self._removed.clear()

        return res

    def commit(self, msg):
        """git commit -m <msg>"""
        if not self._removed and not self._added:
            raise GitError('Nothing to commit')

        return self._git('commit', '-m', msg)
