from __future__ import annotations
import argparse, json, sys, shutil, os, tempfile
from pathlib import Path
from importlib.resources import files as resource_files
from . import __version__, git
from .semver import Version, SemVerError
from .config import load, find_config
from .discovery import discover
from .errors import ForgeError, ConfigError, ReleaseFailure
from .version_sources import read_version
from .synchronization import sync
from .release import plan, release, latest_release
from .changelog import release_notes
from .installation import install, uninstall
from .operation_log import record

def parser():
    """Build the public CLI parser with useful command-specific help."""
    p = argparse.ArgumentParser(
        prog="semver-forge",
        description=(
            "Calculate Semantic Versioning releases from Git history, synchronize configured "
            "version metadata, and create auditable local Git releases."
        ),
        epilog=(
            "Typical workflow:\n"
            "  semver-forge init                         Create project configuration\n"
            "  semver-forge doctor                       Validate the environment\n"
            "  semver-forge next --explain               Explain the proposed version\n"
            "  semver-forge release --dry-run            Preview a release without changes\n"
            "  semver-forge release --yes                Execute an authorized local release\n\n"
            "Use 'semver-forge COMMAND --help' for command-specific help. "
            "See semver-forge(1), README.md, and docs/ for the full reference."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--project", help="project path (default: discover from the current directory)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON where supported")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    def command(name, description, epilog=None):
        return sub.add_parser(
            name, description=description, help=description,
            epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    init_cmd = command("init", "Create project version configuration and initialize version control metadata when available.",
            "Generated files are staged and committed only when Git is available and the index is clean.\nExample: semver-forge init")
    init_cmd.add_argument("--yes", action="store_true", help="authorize overwriting an existing SemVer Forge configuration")
    command("doctor", "Inspect Git, Python, project configuration, and version-source health.",
            "Example: semver-forge doctor --json")
    command("current", "Print the configured canonical project version and its source.")
    command("status", "Summarize repository state, latest release tag, and proposed next version.")
    command("history", "List commits since the latest recognized release boundary.")
    command("check", "Verify that the canonical version and configured synchronization targets agree.")
    command("verify-tag", "Verify the latest recognized release tag and its target commit.")
    command("verify-release", "Verify the latest recognized local release and whether its tag points at HEAD.")

    v = command("validate", "Validate one strict Semantic Versioning 2.0.0 version string.")
    v.add_argument("version", metavar="VERSION", help="version to validate, e.g. 1.2.3-rc.1+build.7")
    c = command("compare", "Compare two versions using SemVer precedence, not lexical string sorting.")
    c.add_argument("version_a", metavar="VERSION_A", help="first version")
    c.add_argument("version_b", metavar="VERSION_B", help="second version")

    b = command("bump", "Calculate a major, minor, or patch increment; write only with --write.",
                "Examples:\n  semver-forge bump patch\n  semver-forge bump minor --write --dry-run")
    b.add_argument("part", choices=["patch", "minor", "major"], help="SemVer component to increment")
    b.add_argument("--write", action="store_true", help="synchronize configured version files")
    b.add_argument("--dry-run", action="store_true", help="show proposed synchronization without writing")

    n = command("next", "Calculate the next version from commits since the previous release boundary.",
                "Examples:\n  semver-forge next\n  semver-forge next --explain --json")
    n.add_argument("--explain", action="store_true", help="include the release-impact explanation")

    sy = command("sync", "Synchronize configured version targets to the selected version.",
                 "This changes project files unless --dry-run is supplied. All targets are validated before writes.")
    sy.add_argument("--dry-run", action="store_true", help="show proposed changes without writing")
    sy.add_argument("--version", metavar="VERSION", help="target version (default: current canonical version)")

    r = command("release", "Prepare and create a local release with notes, configured checks, version metadata, and a Git tag.",
                "Examples:\n  semver-forge release --dry-run\n  semver-forge release patch --dry-run\n  semver-forge release --version 2.0.0 --yes\n  semver-forge release --prerelease rc --yes\n\n"
                "Dry runs and notes-only mode do not write project files, create commits/tags, run checks, or publish. "
                "Actual releases require a clean working tree and never push to a remote.")
    r.add_argument("part", nargs="?", choices=["patch", "minor", "major"], help="explicit release increment")
    r.add_argument("--version", dest="explicit", metavar="VERSION", help="explicit target SemVer version")
    r.add_argument("--dry-run", action="store_true", help="print the release plan without changing repository state")
    r.add_argument("--notes-only", action="store_true", help="generate and display notes without releasing")
    r.add_argument("--prerelease", choices=["alpha", "beta", "rc"], help="calculate or create a prerelease")
    r.add_argument("--yes", action="store_true", help="authorize execution without an interactive confirmation")
    r.add_argument("--build", action="store_true", help="run configured build commands before synchronization")

    ch = command("changelog", "Generate release notes from the commits in the proposed release range.")
    ch.add_argument("--dry-run", action="store_true", help="preview notes without writing a changelog")
    ins = command("install", "Install the current Semver Forge source tree into a user-local prefix.")
    ins.add_argument("--prefix", metavar="DIR", help="installation prefix (default: ~/.local)")
    un = command("uninstall", "Remove Semver Forge files owned by an installation under a prefix.")
    un.add_argument("--prefix", metavar="DIR", help="installation prefix (default: ~/.local)")
    return p

def output(data, as_json=False):
 print(json.dumps(data,indent=2,sort_keys=True,default=str) if as_json else (data if isinstance(data,str) else '\n'.join(f'{k}: {v}' for k,v in data.items())))

def main(argv=None):
 argv=list(sys.argv[1:] if argv is None else argv)
 if not argv:
  parser().print_help()
  return 0
 # Accept global project/JSON options both before and after subcommands.
 moved=[]; rest=[]; i=0
 while i < len(argv):
  if argv[i] == '--json': moved.append(argv[i]); i += 1
  elif argv[i] == '--project' and i + 1 < len(argv): moved.extend(argv[i:i+2]); i += 2
  else: rest.append(argv[i]); i += 1
 args=parser().parse_args(moved+rest)
 try:
  if args.cmd=='install': output(install(args.prefix),args.json); return 0
  if args.cmd=='uninstall': output(uninstall(args.prefix),args.json); return 0
  if args.cmd=='validate':
   Version.parse(args.version); output({'valid':True,'version':args.version},args.json); return 0
  if args.cmd=='compare':
   a=Version.parse(args.version_a); b=Version.parse(args.version_b); result=a.compare(b); output({'comparison':result,'relation':'less' if result<0 else 'greater' if result>0 else 'equal'},args.json); return 0
  if args.cmd=='init':
   project=Path(args.project or '.').expanduser().resolve()
   if not project.is_dir(): raise ConfigError(f'project directory does not exist: {project}')
   root=git.root(project) if git.available(project) else project
   path=root/'.semver-forge.toml'; version=root/'VERSION'
   if path.exists() and not args.yes:
    try: answer=input(f"Overwrite existing configuration {path}? [y/N] ").strip().lower()
    except EOFError: answer=''
    if answer not in ('y','yes'): raise ConfigError(f'initialization cancelled; existing configuration preserved: {path}')
   template=resource_files('semver_forge').joinpath('data/project-config.toml')
   generated={path:template.read_text(encoding='utf-8')}
   if not version.exists(): generated[version]='0.1.0\n'
   written=[]
   try:
    for target,contents in generated.items():
     fd,tmp=tempfile.mkstemp(prefix='.semver-forge-init-',dir=target.parent)
     try:
      with os.fdopen(fd,'w',encoding='utf-8',newline='') as stream:
       stream.write(contents); stream.flush(); os.fsync(stream.fileno())
      os.replace(tmp,target); written.append(target)
     finally:
      if os.path.exists(tmp): os.unlink(tmp)
   except Exception as exc:
    record('ERROR','init.generate','failed',error=exc)
    print(f"Initialization failed. No automatic cleanup was attempted. Inspect generated files: {', '.join(map(str,written))}",file=sys.stderr)
    raise
   committed=False; pushed=False
   vcs_note='no supported VCS detected; files created without a VCS commit'
   if git.available(root):
    try:
     rel=[str(p.relative_to(root)) for p in generated]
     git.run(['add','--',*rel],cwd=root)
     # --only commits exactly these paths and leaves unrelated staged changes untouched.
     git.run(['commit','--only','-m','chore(init): initialize SemVer Forge project configuration','--',*rel],cwd=root)
     committed=True; vcs_note='generated files committed; unrelated staged changes were left untouched'
     if git.run(['remote'],cwd=root,check=False).stdout.split():
      push=git.run(['push'],cwd=root,check=False); pushed=push.returncode==0
      vcs_note += '; remote push '+('succeeded' if pushed else 'failed; local commit preserved')
     else: vcs_note += '; no Git remote configured'
    except ForgeError as exc:
     record('ERROR','init.commit','failed',error=exc)
     vcs_note=f'commit failed: {exc}. Generated files remain; choose whether to retry the commit or keep them uncommitted'
   record('INFO','init','completed')
   output({'initialized':str(path),'version_file':str(version),'generated_files':[str(p) for p in generated],
           'committed':committed,'pushed':pushed,'vcs':vcs_note},args.json); return 0
  root=git.root(args.project)
  config_path=find_config(root)
  if args.cmd=='doctor':
   data={'root':str(root),'git_version':git.run(['--version'],cwd=root).stdout.strip(),'config':str(config_path) if config_path else None,'python':sys.version.split()[0],'git_dirty':git.is_dirty(root),'branch':git.branch(root),'config_valid':False}
   if config_path:
    cfg,unknown=load(config_path); data.update({'config_valid':True,'unknown_keys':unknown,'version':read_version(root,cfg['version']['source']),'defaults_and_config':'defaults merged with project configuration'})
   output(data,args.json); return 0
  if not config_path: raise ConfigError('no .semver-forge.toml found; run semver-forge init')
  cfg,unknown=load(config_path)
  if unknown: print('warning: unknown configuration keys: '+', '.join(unknown),file=sys.stderr)
  current=Version.parse(read_version(root,cfg['version']['source']))
  if args.cmd=='current': output({'version':str(current),'source':cfg['version']['source']['file'],'root':str(root)},args.json)
  elif args.cmd=='bump':
   nxt=current.bump(args.part); data={'current':str(current),'next':str(nxt),'written':False}
   if args.write:
    if not args.dry_run: sync(root,cfg,str(nxt)); data['written']=True
    else: data['dry_run']=True
   output(data,args.json)
  elif args.cmd=='next':
   p=plan(root,cfg); data={'current':str(p['current']),'next':str(p['next']),'impact':p['impact'],'previous_tag':p['tag'],'commit_count':len(p['commits'])}
   if args.explain: data['reason']='highest classified impact since previous release boundary; no impact means current version is retained'
   output(data,args.json)
  elif args.cmd=='sync':
   version=args.version or str(current); result=sync(root,cfg,version,args.dry_run); record('INFO','sync','dry-run' if args.dry_run else 'completed'); output(result,args.json)
  elif args.cmd=='release':
   override=args.explicit or args.part
   result=release(root,cfg,override,args.prerelease,args.dry_run,args.notes_only,args.yes,args.build)
   record('INFO','release','dry-run' if args.dry_run else 'notes-only' if args.notes_only else 'completed')
   output(result,args.json)
  elif args.cmd=='check':
   values=[cfg['version']['source'],*cfg.get('sync',{}).get('targets',[])]; checks=[]
   for src in values: checks.append({'file':src['file'],'version':read_version(root,src)})
   versions={x['version'] for x in checks}
   if len(versions)>1: raise ConfigError('version targets conflict: '+repr(checks))
   output({'consistent':True,'targets':checks},args.json)
  elif args.cmd=='status':
   prev,tag=latest_release(root,cfg); p=plan(root,cfg); output({'root':str(root),'branch':git.branch(root),'dirty':git.is_dirty(root),'current':str(current),'latest_release_tag':tag,'next':str(p['next']),'impact':p['impact'],'commit_count':len(p['commits'])},args.json)
  elif args.cmd=='history':
   prev,tag=latest_release(root,cfg); output({'latest_tag':tag,'commits':git.commits(root,tag)},args.json)
  elif args.cmd=='changelog':
   p=plan(root,cfg); notes=release_notes(p['commits'],p['rules']); output({'version':str(p['next']),'notes':notes,'dry_run':args.dry_run},args.json)
  elif args.cmd in ('verify-tag','verify-release'):
   prev,tag=latest_release(root,cfg)
   if not tag: raise ReleaseFailure('no valid SemVer release tag found')
   target=git.tag_commit(root,tag); data={'tag':tag,'version':str(prev),'tag_commit':target,'head':git.head(root),'tag_exists':True,'points_to_head':target==git.head(root)}
   output(data,args.json)
  else: raise ConfigError(f'command not implemented: {args.cmd}')
  return 0
 except ForgeError as e:
  record('ERROR',getattr(args,'cmd','cli'),'failed',error=e)
  print(f'error: {e}',file=sys.stderr); return e.exit_code
 except (ValueError, OSError, KeyError, TypeError) as e:
  record('ERROR',getattr(args,'cmd','cli'),'failed',error=e)
  print(f'error: {e}',file=sys.stderr); return 2
