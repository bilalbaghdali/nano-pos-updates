#!/usr/bin/env python3
"""Build complete Electron app.asar from verified 1.0.37 plus 1.0.38 delta and pinned megajs dependencies."""
import base64, hashlib, json, pathlib, struct, subprocess, tempfile, urllib.request, zipfile
ROOT = pathlib.Path(__file__).resolve().parent
BASE_URL = 'https://github.com/bilalbaghdali/nano-pos-updates/releases/download/v1.0.37/NANO-POS-Patch-1.0.36-to-1.0.37-MEGA-LOGIN.zip'
BASE_ZIP_SHA = 'a47e2584b948b34f232dc5c2931a393cf68e522637d087d382fa41ff5259b81a'
BASE_ASAR_SHA = '174187656df21a5cffd3d4bd8a977d1e551bbbd1b1f9a3ab56b26d84587026e7'
DELTA_SHA = 'f453d4ca32a81666d3b4440fba31393cff600cbbab626ae87e22fb9caf9893c8'
CORE_SHA = 'e94985f3f12205b7238dafd6e1ad1d19e22af23d00e9404bde05ff748540f626'
ASSET = 'NANO-POS-Patch-1.0.37-to-1.0.38-DIRECT-MEGA.zip'
def sha(data): return hashlib.sha256(data).hexdigest()
def file_map(data):
    length = struct.unpack('<I', data[12:16])[0]
    header = json.loads(data[16:16+length])
    start = 8 + struct.unpack('<I', data[4:8])[0]
    found = {}
    def walk(n, prefix=''):
        for name, node in n['files'].items():
            key = prefix + name
            if 'files' in node: walk(node, key + '/')
            else:
                position = start + int(node['offset'])
                found[key] = (node, data[position:position+node['size']])
    walk(header)
    return found
def make_asar(mapping, integrity_defaults=False):
    header = {'files': {}}
    chunks = []
    offset = 0
    for name, (oldmeta, data) in mapping.items():
        node = header
        parts = name.split('/')
        for part in parts[:-1]: node = node['files'].setdefault(part, {'files': {}})
        metadata = {'size': len(data), 'offset': str(offset)}
        if 'integrity' in oldmeta or integrity_defaults:
            block = oldmeta.get('integrity', {}).get('blockSize', 4194304)
            metadata['integrity'] = {
                'algorithm': 'SHA256', 'hash': sha(data), 'blockSize': block,
                'blocks': [sha(data[i:i+block]) for i in range(0,len(data),block)]
            }
        node['files'][parts[-1]] = metadata
        offset += len(data)
        chunks.append(data)
    raw = json.dumps(header,ensure_ascii=False,separators=(',',':')).encode()
    padded = (len(raw)+3) & ~3
    return struct.pack('<IIII',4,padded+8,padded+4,len(raw)) + raw + b'\0'*(padded-len(raw)) + b''.join(chunks)
def main():
    base_path = pathlib.Path('base-v1.0.37.zip')
    if not base_path.exists():
        request = urllib.request.Request(BASE_URL,headers={'User-Agent':'NANO-POS-verified-release-builder'})
        with urllib.request.urlopen(request,timeout=180) as response: base_path.write_bytes(response.read())
    assert sha(base_path.read_bytes()) == BASE_ZIP_SHA,'Base archive digest mismatch'
    with zipfile.ZipFile(base_path) as z: old_asar = z.read('payload/app.asar')
    assert sha(old_asar) == BASE_ASAR_SHA,'Base app.asar checksum mismatch'
    old = file_map(old_asar)
    parts = sorted(ROOT.glob('delta-part-*.b64'))
    assert len(parts)==1,'Missing source delta'
    data = base64.b64decode(''.join(p.read_text().strip() for p in parts),validate=True)
    assert sha(data) == DELTA_SHA,'Source delta digest mismatch'
    dz = pathlib.Path('delta.zip'); dz.write_bytes(data)
    with zipfile.ZipFile(dz) as z:
        replacements = {name[len('changed/'):]:z.read(name) for name in z.namelist() if name.startswith('changed/') and not name.endswith('/')}
    assert set(replacements) == {'electron-main.cjs','electron-native-preload.cjs','package.json','mega-cloud-backup.cjs','mega-backup-ui.js'}
    core = {key:(meta,replacements.get(key,content)) for key,(meta,content) in old.items()}
    core_bytes = make_asar(core)
    assert sha(core_bytes) == CORE_SHA,'Core build differs from tested source'
    # GitHub Actions installs megajs@1.3.10 into this isolated directory.
    node_modules = ROOT/'deps/node_modules'
    assert (node_modules/'megajs/package.json').is_file(), 'megajs dependencies missing'
    mega_pkg = json.loads((node_modules/'megajs/package.json').read_text())
    assert mega_pkg['version']=='1.3.10', 'Unpinned MEGAJS version'
    all_files = dict(core)
    deps_count = 0
    for file in sorted(node_modules.rglob('*')):
        if not file.is_file() or file.is_symlink(): continue
        rel = file.relative_to(node_modules).as_posix()
        if rel.startswith('.bin/'): continue
        name = 'node_modules/' + rel
        if name in all_files: raise RuntimeError('Duplicate archive path: ' + name)
        all_files[name] = ({},file.read_bytes())
        deps_count += 1
    assert deps_count>4,'Missing dependency files'
    app_asar = make_asar(all_files,integrity_defaults=True)
    assert 'node_modules/megajs/package.json' in file_map(app_asar)
    with tempfile.TemporaryDirectory() as td:
        test_root = pathlib.Path(td)
        # Offline module-resolution smoke test of everything actually packed.
        for rel, (_,payload) in file_map(app_asar).items():
            if rel.startswith('node_modules/'):
                out = test_root/rel
                out.parent.mkdir(parents=True,exist_ok=True)
                out.write_bytes(payload)
        subprocess.run(['node','-e',"const m=require('megajs');if(typeof m.Storage!=='function'||typeof m.Storage.fromJSON!=='function')process.exit(1);console.log('MEGAJS module smoke test passed')"],cwd=td,check=True,timeout=20)
    with zipfile.ZipFile(ASSET,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:z.writestr('payload/app.asar',app_asar)
    with zipfile.ZipFile(ASSET) as z:
        assert z.testzip() is None and z.namelist()==['payload/app.asar']
        assert sha(z.read('payload/app.asar'))==sha(app_asar)
    info = {'fileName':ASSET,'sha256':sha(pathlib.Path(ASSET).read_bytes()),
        'appAsarSha256':sha(app_asar),'sizeBytes':pathlib.Path(ASSET).stat().st_size,
        'megajsVersion':'1.3.10','bundledDependencyFiles':deps_count}
    pathlib.Path('build-result.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))
if __name__=='__main__':main()
