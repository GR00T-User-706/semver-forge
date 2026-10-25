class ForgeError(Exception):
    exit_code = 1


class InputError(ForgeError):
    exit_code = 2


class ConfigError(ForgeError):
    exit_code = 3


class GitError(ForgeError):
    exit_code = 4


class TestFailure(ForgeError):
    exit_code = 5


class BuildFailure(ForgeError):
    exit_code = 6


class ReleaseFailure(ForgeError):
    exit_code = 7


class SafetyError(ForgeError):
    exit_code = 8
