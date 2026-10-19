import os,sys,re,json,hashlib,zipfile,datetime,pathlib
p=pathlib.Path(sys.argv[1])
m=re.fullmatch(r"NANO-POS-Patch-(\d+\.\d+\.\d+)-to-(\d+\.\d+\.\d+)(?:-[A-Za-z0-9-]+)?\.zip",p.name)
if not m or p.parent.as_posix()!="incoming": sys.exit("Invalid incoming patch filename")
old,new=m.groups()
f=pathlib.Path("nano-pos-update.json"); d=json.loads(f.read_text())
if old!=d["version"] or tuple(map(int,new.split(".")))<=tuple(map(int,old.split("."))): sys.exit("Invalid version transition")
with zipfile.ZipFile(p) as z:
 if "payload/app.asar" not in z.namelist(): sys.exit("Missing app.asar")
 if any(x.startswith("/") or ".." in pathlib.PurePosixPath(x).parts for x in z.namelist()): sys.exit("Unsafe ZIP")
 apphash=hashlib.sha256(z.read("payload/app.asar")).hexdigest()
sha=hashlib.sha256(p.read_bytes()).hexdigest();tag="v"+new
repo=os.environ["GITHUB_REPOSITORY"];url=f"https://github.com/{repo}/releases/download/{tag}/{p.name}"
features={"ar":["إصلاح ظهور نافذة الآية أو الحديث بعد تسجيل الدخول الناجح."],"fr":["Correction de la fenêtre de rappel après connexion."],"en":["Fixed reminder dialog after successful login."]}
date=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
prev=d.get("patches",[{}])[0].get("fromVersions",[old])
prev=sorted(set([v for v in prev if tuple(map(int,v.split(".")))<=tuple(map(int,old.split(".")))]+[old]),key=lambda v:tuple(map(int,v.split("."))))
d.update(version=new,published=True,releaseDate=date,features=features)
d.setdefault("releaseHistory",{})[new]={"releaseDate":date,"features":features}
d["patches"]=[{"id":f"nano-pos-v{new}-automatic","fromVersions":prev,"directUrl":url,"pageUrl":f"https://github.com/{repo}/releases/tag/{tag}","sha256":sha,"appAsarSha256":apphash,"fileName":p.name,"sizeBytes":p.stat().st_size,"payloadType":"app-asar"}]
f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
with open(os.environ["GITHUB_OUTPUT"],"a") as out:out.write(f"tag={tag}\nasset={p}\nversion={new}\n")
