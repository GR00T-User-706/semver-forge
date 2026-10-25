# Version-control backends

The VCS boundary is defined by `VCSBackend` in `vcs.py`. Release policy should depend on
that interface rather than invoking a provider executable directly.

Git is the first supported backend. Mercurial, Subversion, Fossil, and Perforce are
possible future backends, but are not currently detected or supported. A backend must
provide repository discovery, dirty-state inspection, branch/current-revision identity,
tag enumeration and resolution, and commit history in the normalized record format
used by release planning.

Do not infer that a VCS is supported merely because its executable is installed.
