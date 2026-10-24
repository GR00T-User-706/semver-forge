"""Strict TOML configuration loading with explicit defaults."""
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from .errors import ConfigError

DEFAULTS = {
 'project': {'name': None, 'description': ''},
 'version': {'source': {'type':'text','file':'VERSION'}, 'initial':'0.1.0'},
 'git': {'tag_prefix':'v','require_clean':True,'baseline':None,'unknown_commit':'ignore','merge_commits':'ignore'},
 'commits': {'breaking_changes':True,'ignored_types':['docs','style','refactor','test','build','ci','chore'],'types':{'feat':'minor','fix':'patch','perf':'patch','revert':'patch'},'unknown':'ignore'},
 'sync': {'targets':[]}, 'release': {'commit_version':True,'annotated_tag':True,'notes_file':'CHANGELOG.md','require_confirmation':True,'test_commands':[],'build_commands':[],'artifact_paths':[],'release_when_no_changes':False},
}

def merge(a,b):
    out=dict(a)
    for k,v in b.items(): out[k]=merge(out[k],v) if isinstance(v,dict) and isinstance(out.get(k),dict) else v
    return out

def load(path):
    p=Path(path)
    if not p.exists(): raise ConfigError(f'configuration not found: {p}; run semver-forge init')
    try: raw=tomllib.loads(p.read_text(encoding='utf-8'))
    except (OSError, tomllib.TOMLDecodeError) as e: raise ConfigError(f'invalid TOML configuration: {e}') from e
    cfg=merge(DEFAULTS,raw)
    for section,key in [('version','initial')]:
        from .semver import Version, SemVerError
        try: Version.parse(str(cfg[section][key]))
        except SemVerError as e: raise ConfigError(f'config [{section}].{key}: {e}') from e
    source=cfg['version'].get('source')
    if not isinstance(source,dict) or source.get('type') not in ('text','json','toml','yaml','shell','debian'):
        raise ConfigError('version.source.type must be text, json, toml, yaml, shell, or debian')
    if not source.get('file'): raise ConfigError('version.source.file is required')
    known={x: set(v) for x,v in DEFAULTS.items()}
    unknown=[]
    for section, values in raw.items():
        if section not in known: unknown.append(section); continue
        if isinstance(values,dict): unknown.extend(f'{section}.{k}' for k in values if k not in known[section])
    return cfg, unknown

def find_config(root):
    for name in ('.semver-forge.toml','semver-forge.toml'):
        p=Path(root)/name
        if p.is_file(): return p
    return None
