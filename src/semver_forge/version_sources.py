"""Version source adapters. TOML read/write supports a top-level dotted key via explicit path."""
from pathlib import Path
import json, re

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib
from .errors import ConfigError

def _path(root, file):
    p=(Path(root)/file).resolve()
    if not p.is_relative_to(Path(root).resolve()): raise ConfigError(f'path escapes project root: {file}')
    return p

def read_version(root, source):
    p=_path(root,source['file']); typ=source['type']
    if not p.is_file(): raise ConfigError(f'version source missing: {p}')
    text=p.read_text(encoding='utf-8')
    if typ=='text': return text.strip()
    key=source.get('key')
    if typ=='json':
        obj=json.loads(text)
        for part in (key or 'version').split('.'): obj=obj[part]
        return str(obj)
    if typ=='toml':
        obj=tomllib.loads(text)
        for part in (key or 'project.version').split('.'): obj=obj[part]
        return str(obj)
    if typ=='shell':
        key=key or 'VERSION'; matches=re.findall(rf'^\s*{re.escape(key)}\s*=\s*[\"\']?([^\"\'\n#]+)',text,re.M)
        if len(matches)!=1: raise ConfigError(f'{p}: expected exactly one {key}= assignment')
        return matches[0].strip()
    if typ=='debian':
        m=re.findall(r'^Version:\s*(\S+)\s*$',text,re.M)
        if len(m)!=1: raise ConfigError(f'{p}: expected exactly one Version field')
        return m[0]
    if typ=='yaml': raise ConfigError('YAML support requires an explicit adapter; no YAML parser is bundled')
    raise ConfigError(f'unsupported version source type: {typ}')

def render_version(root, source, version):
    p=_path(root,source['file']); typ=source['type']; text=p.read_text(encoding='utf-8')
    if typ=='text': return version+'\n'
    key=source.get('key')
    if typ=='json':
        obj=json.loads(text); parts=(key or 'version').split('.'); cur=obj
        for part in parts[:-1]: cur=cur[part]
        cur[parts[-1]]=version
        return json.dumps(obj,indent=2,ensure_ascii=False)+'\n'
    if typ=='toml':
        import re
        key_path=(key or 'project.version').split('.')
        section='.'.join(key_path[:-1])
        field=re.escape(key_path[-1])
        lines=text.splitlines(keepends=True)
        section_pattern=re.compile(r'^\\s*\\['+re.escape(section)+r'\\]\\s*(?:#.*)?
    if typ=='shell':
        key=key or 'VERSION'; pattern=rf'^(\s*{re.escape(key)}\s*=\s*)([\"\']?)[^\"\'\n#]+([\"\']?\s*(?:#.*)?)$'
        new,n=re.subn(pattern,lambda m:m.group(1)+m.group(2)+version+m.group(3),text,count=1,flags=re.M)
        if n!=1: raise ConfigError(f'{p}: expected exactly one {key}= assignment')
        return new
    if typ=='debian':
        new,n=re.subn(r'^(Version:\s*)\S+(\s*)$',lambda m:m.group(1)+version+m.group(2),text,count=1,flags=re.M)
        if n!=1: raise ConfigError(f'{p}: expected exactly one Version field')
        return new
    if typ=='yaml': raise ConfigError('YAML support requires an explicit adapter; no YAML parser is bundled')
    raise ConfigError(f'unsupported version source type: {typ}')
)
        field_pattern=re.compile(r'^(\\s*'+field+r'\\s*=\\s*)([^#\\r\\n]+?)(\\s*(?:#.*)?(?:\\r?\\n)?)
    if typ=='shell':
        key=key or 'VERSION'; pattern=rf'^(\s*{re.escape(key)}\s*=\s*)([\"\']?)[^\"\'\n#]+([\"\']?\s*(?:#.*)?)$'
        new,n=re.subn(pattern,lambda m:m.group(1)+m.group(2)+version+m.group(3),text,count=1,flags=re.M)
        if n!=1: raise ConfigError(f'{p}: expected exactly one {key}= assignment')
        return new
    if typ=='debian':
        new,n=re.subn(r'^(Version:\s*)\S+(\s*)$',lambda m:m.group(1)+version+m.group(2),text,count=1,flags=re.M)
        if n!=1: raise ConfigError(f'{p}: expected exactly one Version field')
        return new
    if typ=='yaml': raise ConfigError('YAML support requires an explicit adapter; no YAML parser is bundled')
    raise ConfigError(f'unsupported version source type: {typ}')
)
        in_section=False
        found=[]
        for index,line in enumerate(lines):
            stripped=line.strip()
            if stripped.startswith('[') and stripped.endswith(']'):
                in_section=bool(section_pattern.match(line.rstrip('\\r\\n')))
            elif in_section:
                match=field_pattern.match(line)
                if match:
                    found.append((index,match))
        if len(found)!=1:
            raise ConfigError(f'{p}: expected exactly one {key or "project.version"} TOML field in [{section}]')
        index,match=found[0]
        lines[index]=match.group(1)+json.dumps(version)+match.group(3)
        return ''.join(lines)
    if typ=='shell':
        key=key or 'VERSION'; pattern=rf'^(\s*{re.escape(key)}\s*=\s*)([\"\']?)[^\"\'\n#]+([\"\']?\s*(?:#.*)?)$'
        new,n=re.subn(pattern,lambda m:m.group(1)+m.group(2)+version+m.group(3),text,count=1,flags=re.M)
        if n!=1: raise ConfigError(f'{p}: expected exactly one {key}= assignment')
        return new
    if typ=='debian':
        new,n=re.subn(r'^(Version:\s*)\S+(\s*)$',lambda m:m.group(1)+version+m.group(2),text,count=1,flags=re.M)
        if n!=1: raise ConfigError(f'{p}: expected exactly one Version field')
        return new
    if typ=='yaml': raise ConfigError('YAML support requires an explicit adapter; no YAML parser is bundled')
    raise ConfigError(f'unsupported version source type: {typ}')
