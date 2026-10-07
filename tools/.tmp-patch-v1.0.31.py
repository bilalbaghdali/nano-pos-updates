import json,struct,hashlib,base64
from pathlib import Path
p=Path("payload/app.asar")
notes=base64.b64decode("KCgpPT57J3VzZSBzdHJpY3QnO2NvbnN0IFY9U3RyaW5nKHdpbmRvdy5OQU5PX0FQUF9WRVJTSU9OfHx3aW5kb3cuTkFOT19SVU5USU1FX1ZFUlNJT058fHdpbmRvdy5uYW5vTmF0aXZlPy5hcHBWZXJzaW9ufHwnMC4wLjAnKS5yZXBsYWNlKC9edi9pLCcnKTtjb25zdCBGPXthcjpbJ9ix2KjYtyDZhdmF2YrYstin2Kog2KfZhNil2LXYr9in2LEg2KjYsdmC2YUg2KfZhNmG2LPYrtipINin2YTZhdir2KjYqtipINio2K/ZhCDYp9mE2YbYtSDYp9mE2KvYp9io2KouJywn2YXYstin2YXZhtipINmF2YXZitiy2KfYqiDZg9mEINil2LXYr9in2LEg2YXYuSDYs9is2YQg2KfZhNil2LXYr9in2LHYp9iqINin2YTZhdmG2LTZiNixINi52YTZiSBHaXRIdWIuJywn2KXYuNmH2KfYsSDZhdmF2YrYstin2Kog2KfZhNmG2LPYrtipINin2YTZhdir2KjYqtipINit2KrZiSDYudmG2K8g2KrZiNmB2LEg2YbYs9iu2Kkg2KPYrdiv2KsuJywn2KrYrdiz2YrZhiDZhdmI2KvZiNmC2YrYqSDYudix2LYg2K3Yp9mE2Kkg2KfZhNil2LXYr9in2LEg2YjYp9mE2KrYrdiv2YrYq9in2KouJ10sZnI6WyJMaWFpc29uIGRlcyBub3V2ZWF1dMOpcyBhdSBudW3DqXJvIGRlIHZlcnNpb24gcsOpZWxsZW1lbnQgaW5zdGFsbMOpLiIsIlN5bmNocm9uaXNhdGlvbiBkZXMgbm91dmVhdXTDqXMgYXZlYyBs4oCZaGlzdG9yaXF1ZSBkZXMgdmVyc2lvbnMgcHVibGnDqSBzdXIgR2l0SHViLiIsIkFmZmljaGFnZSBkZXMgbm91dmVhdXTDqXMgZGUgbGEgdmVyc2lvbiBpbnN0YWxsw6llIG3Dqm1lIGxvcnNxdeKAmXVuZSB2ZXJzaW9uIHBsdXMgcsOpY2VudGUgZXhpc3RlLiIsIkFtw6lsaW9yYXRpb24gZGUgbGEgZmlhYmlsaXTDqSBkZSBs4oCZw6l0YXQgZGUgdmVyc2lvbiBldCBkZXMgbWlzZXMgw6Agam91ci4iXSxlbjpbJ1JlbGVhc2UgaGlnaGxpZ2h0cyBub3cgZm9sbG93IHRoZSBhY3R1YWxseSBpbnN0YWxsZWQgdmVyc2lvbi4nLCdSZWxlYXNlIGhpZ2hsaWdodHMgc3luY2hyb25pemUgd2l0aCB0aGUgdmVyc2lvbiBoaXN0b3J5IHB1Ymxpc2hlZCBvbiBHaXRIdWIuJywnSW5zdGFsbGVkLXZlcnNpb24gaGlnaGxpZ2h0cyByZW1haW4gY29ycmVjdCBldmVuIHdoZW4gYSBuZXdlciB1cGRhdGUgZXhpc3RzLicsJ0ltcHJvdmVkIHJlbGlhYmlsaXR5IG9mIHZlcnNpb24gYW5kIHVwZGF0ZSBzdGF0dXMgZGlzcGxheS4nXX07bGV0IFI9e3ZlcnNpb246VixmZWF0dXJlczpGfTt3aW5kb3cuTkFOT19SRUxFQVNFX05PVEVTPVI7Y29uc3QgTD0oKT0+e2xldCB4PVN0cmluZyh3aW5kb3cuY3VycmVudExhbmd1YWdlfHxkb2N1bWVudC5kb2N1bWVudEVsZW1lbnQubGFuZ3x8J2FyJykudG9Mb3dlckNhc2UoKTtyZXR1cm4geC5zdGFydHNXaXRoKCdmcicpPydmcic6eC5zdGFydHNXaXRoKCdlbicpPydlbic6J2FyJ30sVD1sPT5sPT09J2ZyJz9bJ05vdXZlYXV0w6lzIGRlIGxhIHZlcnNpb24gYWN0dWVsbGUnLCdWZXJzaW9uIGluc3RhbGzDqWUnXTpsPT09J2VuJz9bJ0N1cnJlbnQgcmVsZWFzZSBoaWdobGlnaHRzJywnSW5zdGFsbGVkIHZlcnNpb24nXTpbJ9mF2YXZitiy2KfYqiDYp9mE2KXYtdiv2KfYsSDYp9mE2K3Yp9mE2YonLCfYp9mE2KXYtdiv2KfYsSDYp9mE2YXYq9io2KonXSxFPXg9PlN0cmluZyh4KS5yZXBsYWNlKC9bJjw+IiddL2csYz0+KHsnJic6JyZhbXA7JywnPCc6JyZsdDsnLCc+JzonJmd0OycsJyInOicmcXVvdDsnLCInIjonJiMzOTsnfVtjXSkpLEQ9KCk9PntsZXQgYj1kb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnY3VycmVudFJlbGVhc2VGZWF0dXJlcycpO2lmKCFiKXJldHVybjtsZXQgbD1MKCksdD1UKGwpLGE9Ui5mZWF0dXJlcz8uW2xdfHxGW2xdO2xldCBoPWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdjdXJyZW50UmVsZWFzZVRpdGxlJyksdj1kb2N1bWVudC5nZXRFbGVtZW50QnlJZCgnY3VycmVudFJlbGVhc2VWZXJzaW9uJyk7aWYoaCloLnRleHRDb250ZW50PXRbMF07aWYodil2LnRleHRDb250ZW50PWAke3RbMV19OiB2JHtWfWA7Yi5pbm5lckhUTUw9YS5tYXAoeD0+YDxkaXYgY2xhc3M9ImZsZXggZ2FwLTIgaXRlbXMtc3RhcnQiPjxzcGFuIGNsYXNzPSJ0ZXh0LWVtZXJhbGQtNTAwIGZvbnQtYmxhY2siPuKckzwvc3Bhbj48c3Bhbj4ke0UoeCl9PC9zcGFuPjwvZGl2PmApLmpvaW4oJycpfSxTPWFzeW5jKCk9Pnt0cnl7bGV0IHg9YXdhaXQgd2luZG93Lm5hbm9OYXRpdmU/LmNoZWNrRm9yVXBkYXRlcz8uKCksbT14Py5tYW5pZmVzdDtpZighbSlyZXR1cm47bGV0IGY9bS52ZXJzaW9uPT09Vj9tLmZlYXR1cmVzOm0ucmVsZWFzZUhpc3Rvcnk/LltWXT8uZmVhdHVyZXM7aWYoZil7Uj17dmVyc2lvbjpWLGZlYXR1cmVzOnsuLi5GLC4uLmZ9fTt3aW5kb3cuTkFOT19SRUxFQVNFX05PVEVTPVI7RCgpfX1jYXRjaHt9fTtkb2N1bWVudC5hZGRFdmVudExpc3RlbmVyKCdET01Db250ZW50TG9hZGVkJywoKT0+e0QoKTtTKCl9LHtvbmNlOnRydWV9KTt3aW5kb3cuYWRkRXZlbnRMaXN0ZW5lcignbmFuby1sYW5ndWFnZS1zeW5jaHJvbml6ZWQnLEQpO3dpbmRvdy5hZGRFdmVudExpc3RlbmVyKCdsb2FkJyxELHtvbmNlOnRydWV9KX0pKCk7Cg==")
with p.open("rb") as f:
    f.read(4); hs=struct.unpack("<I",f.read(4))[0]; hb=f.read(hs); sl=struct.unpack("<I",hb[4:8])[0]; h=json.loads(hb[8:8+sl]); base=8+hs
nodes={}
def walk(n,pre=""):
    for k,v in n.get("files",{}).items():
        q=f"{pre}/{k}" if pre else k
        if "files" in v: walk(v,q)
        else: nodes[q]=v
walk(h)
targets={"app-config.js","browser-ui.css","browser-ui.js","index.html","package-lock.json","package.json","release-notes.js","updater-main.cjs"}
changed={}
with p.open("rb") as f:
    for path,m in nodes.items():
        if path not in targets: continue
        f.seek(base+int(m["offset"])); orig=f.read(m["size"]); data=orig
        if path in {"app-config.js","browser-ui.css","browser-ui.js","index.html","package-lock.json","package.json"}:
            data=data.replace(b"1.0.30",b"1.0.31")
        elif path=="release-notes.js":
            if len(notes)>len(orig): raise RuntimeError("release notes too large")
            data=notes+b" "*(len(orig)-len(notes))
        elif path=="updater-main.cjs":
            s=data.decode()
            old="notes: raw.notes || {},\n    download:"
            new="notes:raw.notes||{},releaseHistory:raw.releaseHistory||{},\n    download:"
            if old not in s: raise RuntimeError("manifest normalizer target missing")
            s=s.replace(old,new,1)
            s=s.replace("  // Fast path: per-user/writable installs can apply the patch without UAC.\n","")
            s=s.replace("const DEFAULT_MANIFEST_URL = ","const DEFAULT_MANIFEST_URL=")
            s=s.replace("const MAX_MANIFEST_BYTES = ","const MAX_MANIFEST_BYTES=")
            s=s.replace("const MAX_REDIRECTS = ","const MAX_REDIRECTS=")
            data=s.encode()
            if len(data)>len(orig): raise RuntimeError("updater too large")
            data+=b" "*(len(orig)-len(data))
        if data!=orig:
            changed[path]=data
            integ=m.get("integrity") or {}; bs=int(integ.get("blockSize") or 4194304)
            integ["algorithm"]="SHA256"; integ["hash"]=hashlib.sha256(data).hexdigest(); integ["blockSize"]=bs
            integ["blocks"]=[hashlib.sha256(data[i:i+bs]).hexdigest() for i in range(0,len(data),bs)]
            m["integrity"]=integ
newjson=json.dumps(h,separators=(",",":"),ensure_ascii=False).encode()
if len(newjson)!=sl: raise RuntimeError("header length changed")
newhb=struct.pack("<I",struct.unpack("<I",hb[:4])[0])+struct.pack("<I",sl)+newjson+hb[8+sl:]
with p.open("r+b") as f:
    f.seek(8); f.write(newhb)
    for path,data in changed.items():
        m=nodes[path]; f.seek(base+int(m["offset"])); f.write(data)
sha=hashlib.sha256(p.read_bytes()).hexdigest()
print(sha)
if sha!="cc406ee8429e16a472096b4d90d62cd19b316d0c05c620ce6a8c49883288ef31":
    raise RuntimeError("unexpected asar sha "+sha)
