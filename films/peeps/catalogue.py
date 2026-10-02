import os
import re

import cv2
import numpy as np
import skia
from films import montage_ia as MI
D=os.path.join(os.path.dirname(os.path.abspath(__file__)), "")
eff=open(D+"effigy_offsets.js").read()
off={}
for fn in ("createHair","createBeard"):
    m=re.search(r"var %s = function.*?\n};"%fn, eff, re.S)
    for t,tr in re.findall(r'\.type === "(\w+)"\)\s*\{\s*return React\.createElement\("g", \{ transform: \'([^\']+)\'', m.group(0)):
        off[(fn,t)]=tr
def inner(path):
    return re.sub(r"^<svg[^>]*>|</svg>$","",open(path).read())
VB=(184.2, 210.8, 940.3, 1130.6)
def compose(body, head, face, beard=None):
    g=lambda fn,t: off.get((fn,t),"translate(0 0)")
    parts=[f'<g transform="translate(147, 639)">{inner(D+"svg/body/effigy/"+body+".svg")}</g>',
           f'<g transform="translate(342, 190)"><g transform="{g("createHair",head)}">{inner(D+"svg/head/"+head+".svg")}</g></g>',
           f'<g transform="translate(531, 366)">{inner(D+"svg/face/"+face+".svg")}</g>']
    if beard: parts.append(f'<g transform="translate(495, 518)"><g transform="{g("createBeard",beard)}">{inner(D+"svg/beard/"+beard+".svg")}</g></g>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB[0]} {VB[1]} {VB[2]} {VB[3]}" width="{VB[2]}" height="{VB[3]}">{"".join(parts)}</svg>'
def raster(svg, w, h, bg=(255,255,255)):
    m=re.search(r'viewBox="([^"]+)"',svg); vx,vy,vw,vh=[float(x) for x in m.group(1).split()]
    svg=re.sub(r'(<svg[^>]*?) width="[^"]*"', r'\1', svg, count=1); svg=re.sub(r'(<svg[^>]*?) height="[^"]*"', r'\1', svg, count=1)
    dom=skia.SVGDOM.MakeFromStream(skia.MemoryStream(svg.encode()))
    dom.setContainerSize(skia.Size(w,h))
    arr=np.zeros((h,w,4),np.uint8); arr[:,:,:3]=bg; arr[:,:,3]=255
    c=skia.Surface(arr,colorType=skia.kRGBA_8888_ColorType).getCanvas()
    dom.render(c); return arr[:,:,:3].copy()
def label(img, txt, size=22):
    arr=np.dstack([img,np.full(img.shape[:2],255,np.uint8)]).copy(); c=skia.Surface(arr,colorType=skia.kRGBA_8888_ColorType).getCanvas()
    f=skia.Font(MI.F_SUB,size); c.drawString(txt,(arr.shape[1]-f.measureText(txt))/2,arr.shape[0]-8,f,skia.Paint(AntiAlias=True,Color=skia.ColorBLACK)); return arr[:,:,:3]
def grid(tiles, cols):
    tiles=list(tiles)
    while len(tiles)%cols: tiles.append(np.full_like(tiles[0],255))
    return np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)])
def pad(img, h_extra=34):
    return np.vstack([img, np.full((h_extra,img.shape[1],3),255,np.uint8)])
if __name__=="__main__":
    OUT="output/open_peeps"; os.makedirs(OUT,exist_ok=True)
    save=lambda n,im,q=86: cv2.imwrite(OUT+n, cv2.cvtColor(im,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,q])
    chars=[("Explaining","ShortTwo","Smile","Chin"),("PointingUp","Bun","Awe",None),("Computer","Afro","Calm",None),("Coffee","Bangs","Cute",None),
    ("BlazerBlackTee","Bald","Concerned","Full"),("Paper","LongBangs","Driven",None),("Hoodie","Beanie","Cheeky",None),("Jacket","ShortThree","Suspicious","MustacheSeven"),
    ("Turtleneck","BunTwo","SmileTeeth",None),("TeeArmsCrossed","Mohawk","Serious",None),("Gaming","Hijab","Calm",None),("Whatever","GrayShort","Old","Full")]
    save("/1_personnages.jpg", grid([label(pad(raster(compose(*c),376,452)), c[0]) for c in chars],4))
    faces=sorted(os.listdir(D+"svg/face"))
    save("/2_expressions.jpg", grid([label(pad(raster(compose("Tee","ShortTwo",f[:-4]),376,452)[20:250,70:310]), f[:-4],18) for f in faces],7))
    heads=sorted(os.listdir(D+"svg/head"))
    save("/3_coiffures.jpg", grid([label(pad(raster(compose("Tee",h[:-4],"Calm"),376,452)[0:260,50:330]), h[:-4],16) for h in heads],9),82)
    tiles=[]
    for sub in ("standing","sitting"):
        for b in sorted(os.listdir(D+"svg/body/"+sub)):
            s=open(D+f"svg/body/{sub}/{b}").read(); vb=[float(x) for x in re.search(r'viewBox="([^"]+)"',s).group(1).split()]
            h=380; w=int(h*vb[2]/vb[3]); im=raster(s,w,h); t=np.full((h,300,3),255,np.uint8)
            x0=max(0,(w-300)//2); im=im[:,x0:x0+300]; t[:, (300-im.shape[1])//2:(300-im.shape[1])//2+im.shape[1]]=im
            tiles.append(label(pad(t),b[:-4],15))
    save("/4_corps_entiers.jpg", grid(tiles,9),82)
    print(os.listdir(OUT))
