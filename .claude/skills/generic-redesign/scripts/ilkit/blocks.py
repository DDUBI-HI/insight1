from sv import *

def chevrons(mods, y=192):
    """mods: (label, name, icon, tag, core[2], method, out[2])"""
    ops=[0.7,0.8,0.9,1.0][-len(mods):] if len(mods)<=4 else [0.6,0.7,0.8,0.9,1.0]
    n=len(mods); w=(1088)//n
    b=''
    for i,(m,name,icon,tag,core,meth,out) in enumerate(mods):
        x0=96+i*w
        if i==0: pts=f"{x0},{y} {x0+w-4},{y} {x0+w+16},{y+32} {x0+w-4},{y+64} {x0},{y+64}"
        else: pts=f"{x0},{y} {x0+w-4},{y} {x0+w+16},{y+32} {x0+w-4},{y+64} {x0},{y+64} {x0+20},{y+32}"
        op='' if ops[i]==1.0 else f' fill-opacity="{ops[i]}"'
        b+=f'  <polygon points="{pts}" fill="#012281"{op}/>\n'
        tx=x0+(24 if i==0 else 36)
        b+=t(tx,y+25,m,12.8,600,"#FFFFFF",ls=0.26)
        b+=t(tx,y+50,name,17.6,700,"#FFFFFF")
        cx=x0+20
        b+=ic(icon,cx,y+88,32)
        b+=t(cx,y+152,tag,15.2,700)
        for j,c in enumerate(core): b+=t(cx,y+184+j*24,c,15.2,400,"#595959")
        b+=ln(cx,y+236,x0+w-12,y+236)
        b+=t(cx,y+266,"METHOD",12.8,600,"#595959",ls=0.26)
        b+=t(cx,y+292,meth,15.2,400)
        b+=t(cx,y+332,"OUTPUT",12.8,600,"#595959",ls=0.26)
        for j,c in enumerate(out): b+=t(cx,y+358+j*24,c,15.2,700)
    return b

def dot(x,y): return f'  <circle cx="{x}" cy="{y}" r="2.5" fill="#1A1A1A"/>\n'

def modgrid(mods, rows, hl=None, top=184):
    """mods: [{name,time,cells:{rowkey:[lines] or ('b',[bullets])}}]; rows: [(key,label,h)]"""
    cols=[240,712]; W=472
    b=r(96,top,144,56,"#012281")+t(168,top+33,"MODULE",15.2,700,"#FFFFFF",anchor="middle")
    b+=r(240,top,944,56,"#F8F8F8")
    y=top+56; ys={}
    for k,lab,h in rows:
        ys[k]=(y,h)
        b+=r(96,y,144,h,"#012281",op=0.7)+ln(96,y,240,y,"#FFFFFF")
        b+=t(168,y+h/2+5.5,lab,15.2,700,"#FFFFFF",anchor="middle")
        b+=ln(240,y,1184,y)
        y+=h
    b+=ln(240,y,1184,y)+ln(712,top,712,y)
    for ci,(x,m) in enumerate(zip(cols,mods)):
        b+=t(x+24,top+34,m["name"],17.6,700)
        if m.get("time"): b+=ic("clock",x+W-88,top+17,20,"#595959")+t(x+W-24,top+33,m["time"],15.2,700,"#595959",anchor="end")
        for k,lab,h in rows:
            y0,hh=ys[k]; cell=m["cells"].get(k,[])
            if hl==(ci,k): b+=r(x+1,y0+1,W-1,hh-1,"#E0EDF3")
            if isinstance(cell,tuple):
                for j,s in enumerate(cell[1]):
                    yy=y0+32+j*34
                    b+=dot(x+30,yy-5)+t(x+42,yy,s,15.2,400)
            else:
                n=len(cell); start=y0+hh/2+5.5-(n-1)*12
                for j,s in enumerate(cell):
                    fw,fs,fill=(700,15.2,"#1A1A1A") if (j==0 and k=="q") else (400,15.2 if k!="q" else 12.8,"#1A1A1A" if k!="q" else "#595959")
                    b+=t(x+24,start+j*24,s,fs,fw,fill)
    return b,y

def budget(total, stats, rows, formula, basis="기준: 시간, 원"):
    """stats: [(value,label)]x3; rows: [(구분, 세부내역, 금액, bold?, hl?)]; formula: [(value,label) or (op,None)]"""
    def wo(s, op): return s.replace('fill="#FFFFFF"', f'fill="#FFFFFF" fill-opacity="{op}"')
    b=r(96,184,400,288,"#012281")
    b+=wo(t(128,224,"TOTAL BUDGET | 교육비 합계",12.8,600,"#FFFFFF",ls=0.26),0.7)
    b+=t(128,280,total,40,800,"#FFFFFF",ls=-0.8)
    b+=wo(t(128,308,"VAT 10% 포함",15.2,400,"#FFFFFF"),0.8)
    b+=ln(128,332,464,332,"#FFFFFF").replace('/>',' stroke-opacity="0.3"/>')
    for i,(v,l) in enumerate(stats):
        y=368+i*40
        b+=t(128,y,v,17.6,700,"#FFFFFF")+wo(t(464,y,l,15.2,400,"#FFFFFF",anchor="end"),0.8)
    b+=t(544,196,f"BUDGET DETAIL | 산출 내역 ({basis})",12.8,600,"#595959",ls=0.26)
    b+=r(544,208,640,56,"#F8F8F8")
    for x,s,a in [(568,"구분",None),(728,"세부내역",None),(1040,"금액","end"),(1160,"비고","end")]:
        b+=t(x,241,s,15.2,700,anchor=a)
    rh=min(64,int(208/len(rows)))
    y=264
    for g,d,amt,bold,hl in rows:
        if hl: b+=r(544,y,640,rh,"#E0EDF3")
        b+=t(568,y+rh/2+5.5,g,15.2,700 if bold else 400)
        if d: b+=t(728,y+rh/2+5.5,d,15.2,400)
        b+=t(1040,y+rh/2+5.5,amt,17.6 if hl else 15.2,700 if hl else 400,anchor="end")
        y+=rh
        b+=ln(544,y,1184,y,"#C2C2C2" if hl else "#DFDFDF")
    b+=r(96,496,1088,112,"#F8F8F8",14)
    b+=t(128,530,"HOW IT ADDS UP | 산출식",12.8,600,"#595959",ls=0.26)
    n=len(formula); xs=[200+i*(880/(n-1)) for i in range(n)]
    for x,(v,l) in zip(xs,formula):
        x=round(x)
        if l is None: b+=t(x,572,v,17.6,400,"#595959",anchor="middle")
        else: b+=t(x,566,v,17.6,700,anchor="middle")+t(x,590,l,12.8,400,"#666666",anchor="middle")
    return b

def roster(rows, heads=("현직","강의 분야","대표 출강"), C=((248,300),(548,372),(920,264)), hlcol=None, rh=72, top=184):
    b=r(96,top,152,56,"#012281")+t(172,top+33,"강사",15.2,700,"#FFFFFF",anchor="middle")
    b+=r(248,top,936,56,"#F8F8F8")
    if hlcol is not None: b+=r(C[hlcol][0],top,C[hlcol][1],56,"#E0EDF3")
    for (x,w),h in zip(C,heads): b+=t(x+24,top+33,h,15.2,700)
    y=top+56
    for n,*cols in rows:
        b+=r(96,y,152,rh,"#012281",op=0.7)+t(172,y+rh/2+6,n,17.6,700,"#FFFFFF",anchor="middle")
        if hlcol is not None: b+=r(C[hlcol][0],y,C[hlcol][1],rh,"#E0EDF3")
        for (x,w),lines in zip(C,cols):
            if len(lines)==1: b+=t(x+24,y+rh/2+5,lines[0],15.2,400)
            else: b+=t(x+24,y+rh/2-7,lines[0],15.2,400)+t(x+24,y+rh/2+17,lines[1],15.2,400,"#595959")
        b+=ln(96,y,248,y,"#FFFFFF")+ln(248,y+rh,1184,y+rh)
        y+=rh
    return b,y

def timetable(rows, hl=None, top=184, rh=56):
    """rows: (time, dur, title, content, method)"""
    b=r(96,top,168,48,"#012281")+t(180,top+30,"시간",15.2,700,"#FFFFFF",anchor="middle")
    b+=r(264,top,920,48,"#F8F8F8")+t(288,top+30,"세션 · 주요 내용",15.2,700)+t(1160,top+30,"방식",15.2,700,anchor="end")
    y=top+48
    for i,(tm,du,ti,co,me) in enumerate(rows):
        b+=r(96,y,168,rh,"#012281",op=0.7)+ln(96,y,264,y,"#FFFFFF")
        b+=t(180,y+25,tm,15.2,700,"#FFFFFF",anchor="middle")+t(180,y+45,du,12.8,400,"#FFFFFF",anchor="middle").replace('fill="#FFFFFF"','fill="#FFFFFF" fill-opacity="0.8"',1)
        if hl==i: b+=r(264,y,920,rh,"#E0EDF3")
        b+=t(288,y+24,ti,15.2,700)+t(288,y+44,co,12.8,400,"#595959")
        b+=t(1160,y+34,me,12.8,600,"#1A1A1A",anchor="end")
        y+=rh
        b+=ln(264,y,1184,y)
    return b,y

def modrows(rows, top=184, lh=21, pad=14, hl=None):
    """rows: (label1,label2, [(tag,text)], method, time)"""
    b=r(96,top,176,40,"#012281")+t(184,top+26,"모듈",15.2,700,"#FFFFFF",anchor="middle")
    b+=r(272,top,912,40,"#F8F8F8")+t(296,top+26,"내용",15.2,700)+t(1010,top+26,"방법",15.2,700,anchor="middle")+t(1130,top+26,"시간",15.2,700,anchor="middle")
    y=top+40
    for i,(l1,l2,items,meth,tm) in enumerate(rows):
        h=pad*2+lh*len(items)
        b+=r(96,y,176,h,"#012281",op=0.7)+ln(96,y,272,y,"#FFFFFF")
        b+=t(184,y+h/2-4,l1,12.8,600,"#FFFFFF",anchor="middle").replace('fill="#FFFFFF"','fill="#FFFFFF" fill-opacity="0.8"',1)+t(184,y+h/2+18,l2,15.2,700,"#FFFFFF",anchor="middle")
        if hl==i: b+=r(272,y,912,h,"#E0EDF3")
        for j,(tag,tx) in enumerate(items):
            yy=y+pad+15+j*lh
            if tag=="h": b+=t(296,yy,tx,15.2,700)
            else:
                xx=312
                if tag: b+=t(xx,yy,f"[{tag}]",12.8,700,"#012281"); xx+=12*len(tag)+30
                b+=t(xx,yy,tx,12.8,400,"#1A1A1A" if tag else "#595959")
        b+=t(1010,y+h/2+5,meth,12.8,400,"#595959",anchor="middle")+t(1130,y+h/2+5,tm,15.2,700,anchor="middle")
        y+=h; b+=ln(272,y,1184,y)
    return b,y
