from pathlib import Path
import os, tempfile, shutil
from .version_sources import read_version, render_version, _path
from .errors import ConfigError, SafetyError
from .semver import Version, SemVerError

def sync(root, cfg, version, dry_run=False):
    try:
        version = str(Version.parse(str(version)))
    except SemVerError as exc:
        raise ConfigError(f'invalid target version {version!r}: {exc}') from exc
    sources=[cfg['version']['source'], *cfg.get('sync',{}).get('targets',[])]
    changes=[]
    for src in sources:
        p=_path(root,src['file'])
        if not p.exists(): raise ConfigError(f'synchronization target missing: {p}')
        old=read_version(root,src)
        new=render_version(root,src,version)
        changes.append((p,old,new,src))
    if dry_run: return [{'file':str(p),'old_version':old,'new_version':version,'changed':old!=version} for p,old,new,src in changes]
    # Validate every file before any writes; backups are in memory and restored on failure.
    originals={p:p.read_bytes() for p,_,_,_ in changes}
    written=[]
    try:
        for p,old,new,src in changes:
            if old==version: continue
            fd,tmp=tempfile.mkstemp(prefix='.semver-forge-',dir=p.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8',newline='') as f: f.write(new); f.flush(); os.fsync(f.fileno())
                os.chmod(tmp,p.stat().st_mode)
                os.replace(tmp,p); written.append(p)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
        for p,_,_,src in changes:
            if read_version(root,src)!=version: raise ConfigError(f'post-write verification failed for {p}')
    except Exception:
        for p in reversed(written):
            fd,tmp=tempfile.mkstemp(prefix='.semver-forge-rollback-',dir=p.parent)
            try:
                with os.fdopen(fd,'wb') as f: f.write(originals[p]); f.flush(); os.fsync(f.fileno())
                os.replace(tmp,p)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
        raise
    return [{'file':str(p),'old_version':old,'new_version':version,'changed':old!=version} for p,old,new,src in changes]
