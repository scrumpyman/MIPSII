import re,os
mdom="RDRAM"
bend="false"
console=0
def main():
    global mdom,bend,console
    ccode=[
        "moved1",
        "moved2",
        "0320D825",
        "03E0C825",
        "insert",#2
        "AFF90004",
        "0360C825",
        "AFFD0000",
        "AFE10008",
        "backuploop",#11
        "tojumper",
        "27BD0800",
        "insert",#2
        "restoreloop",#10
        "8FE10008",
        "8FFD0000",
        "8FFF0004",
        "return",
        "341B0AAA",
        "jumper",#x
        "ret"
        ]
    backuploop1=[
        "27FD0070",
        "24010018",
        "10010007",
        "242100A1",
        "backupsw",
        "2421FF5F",
        "27BDFFFC",
        "AFB90000",
        "1000FFF9",
        "2421FFFF",
        "8FFD0000"
        ]
    restoreloop1=[
        "27FD0070",
        "24010018",
        "10010007",
        "242100A1",
        "restoresw",
        "2421FF5F",
        "27BDFFFC",
        "8FB90000",
        "1000FFF9",
        "2421FFFF"
        ]
    outputn="output"
    inputf=open("input.txt","r")
    jumpfrom=""
    jumpto=[]
    jumpinsert=""
    jumpregisters=[]
    FP=0
    RA=0
    JJ=0
    jri=0
    jrif=0
    MO=0
    BT=0
    MC=0
    pspu=3
    for i,v in enumerate(inputf):
        vv=""
        if(v[-1:]=="\n"):
            v=v[:-1]
        vs=v.replace("#"," #").split(" ")
        for vn in vs:
            if(vn):
                vv=vn
                break
        if(vv!="#"):
            if(i==0 and vv):
                outputn2=""
                for n in vs:
                    if(n[0:1]=="#"):
                        break
                    else:
                        oo=re.sub(r'\W+','',n)
                        if(oo):
                            if(outputn2):
                                outputn2+=" "
                            outputn2+=oo
                if(outputn2):
                    outputn=outputn2
            elif(i==1 and vv):
                if(vv=="1"):
                    mdom="MainRAM"
                    bend="true"
                    console=1
                elif(vv=="2"):
                    mdom="EERAM"
                    bend="true"
                    console=2
            elif(i==2 and vv):
                ca=checkaddress(vv)
                if(ca):
                    jumpfrom=ca
                    print("jump-from: "+ca)
                else:
                    print("error: jump-from address invalid")
                    break
            elif(i==3 and vv):
                ca=checkaddress(vv)
                if(ca):
                    jumpinsert=ca
                    print("jump-insert: "+ca)
                else:
                    print("error: jump-insert address invalid")
            elif(i==4 and int(vv)>0 and int(vv)<=32):
                FP=int(vv)
            elif(i==5 and vv=="1"):
                BT=1
            elif(i==5 and vv=="2"):
                BT=2
            elif(i==6 and vv=="1"):
                MC=1
            elif(i==7 and vv=="1"):
                JJ=1
            elif(i==8 and vv=="1"):
                MO=1
            elif(i>8):
                quote=0
                qr=""
                for r in vs:
                    qc=r.count('"')
                    if(quote==0 and qc%2==1 or quote==1 and qc%2==0):
                        quote=1
                        qr+=r+" "
                    else:
                        r=(qr+r).replace('"','')
                        quote=0
                        qr=""
                        if(r.find(":")>-1):
                            ca=checkregister(r,RA,JJ,FP)
                            if(len(ca)==1):
                                ca=checkaddress(r[0:-1])
                                if(ca):
                                    if(jumpto):
                                        jri+=1
                                        jumpto=growlist(jumpto,jri,"")
                                        jumpto[jri]=ca
                                    else:
                                        jumpto.append(ca)
                                        print("jump-to: "+ca)
                            elif(len(ca)==5 and not isinstance(ca[0],list) and ca[0]!=-1):
                                jumpregisters=growlist(jumpregisters,jri,[])
                                jumpregisters[jri].append(ca)
                            elif(len(ca)>=2 and isinstance(ca[0],list)):
                                for ca2 in ca:
                                    if(isinstance(ca2,list) and len(ca2)==5 and ca2[0]!=-1):
                                        jumpregisters=growlist(jumpregisters,jri,[])
                                        jumpregisters[jri].append(ca2)
    inputf.close()
    if(jumpfrom and (jumpto or jumpinsert)):
        MOi=0
        if(MO and len(jumpto)>1):
            cjumpto=jumpto.copy()
            cjumpregisters=jumpregisters.copy()
            jumpto=[cjumpto[0]]
            jumpregisters=[cjumpregisters[0]]
        else:
            MO=0
        while(MOi<999):
            out=""
            branches=[]
            todobranches=[]
            if(jumpinsert):
                rrn=28
                if(BT==0):
                    rrn=4
                inserta=int(jumpinsert,16)+rrn*4
                reta=0
                jumper=jal(inserta+4,1)
                out+=writeunit(int(jumpfrom,16),jumper,"jump to custom code",0)
                if(MC):
                    out+=',\n    '
                    out+=writeunit(int(jumpfrom,16)+4,"00000000","jump delay slot",0)
                ita=""
                ita2=""
                if(jumpregisters):
                    if(jumpto):
                        print("outputting complete jump with backup, load and restore")
                    else:
                        print("outputting register load only")
                else:
                    if(jumpto):
                        print("outputting jump with registers backup and restore")
                    else:
                        print("outputting backup only? (probably does nothing)")
                for v in ccode:
                    out+=',\n    '
                    inserta+=4
                    if(v=="moved1"):
                        if(MC):
                            out+=writeunit(inserta,"","instruction transfer",1,int(jumpfrom,16))
                        else:
                            out+=writeunit(inserta,"00000000")
                    elif(v=="moved2"):
                        if(MC):
                            out+=writeunit(inserta,"","instruction transfer",1,int(jumpfrom,16)+4)
                        else:
                            out+=writeunit(inserta,"00000000")
                    elif(v=="tojumper"):
                        reta=inserta+4
                        out+=writeunit(inserta,ubranch(inserta,"jumper",branches,todobranches),"branch to instruction section between backup and restore")
                    elif(v=="backuploop"):
                        if(BT==1):
                            if(console==1 and pspu>=1):
                                jumpinsert2=checkaddress(hex8(inserta+16))
                                out+=writeunit(inserta,"3C01A0"+jumpinsert2[-8:-4].rjust(2,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"3421"+jumpinsert2[-4:].rjust(4,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"00200008")
                                out+=',\n    '
                                inserta+=4
                            for v2 in backuploop1[:-1]:
                                if(v2=="backupsw"):
                                    swoff=inserta-int(jumpinsert,16)+13
                                    if(bend=="true"):
                                        swoff+=1
                                    out+=writeunit(inserta,"A3E1"+hex4(swoff))
                                else:
                                    out+=writeunit(inserta,v2)
                                out+=',\n    '
                                inserta+=4
                            out+=writeunit(inserta,backuploop1[-1])
                            if(console==1 and pspu>=3):
                                jumpinsert2=checkaddress(hex8(inserta+16))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"3C0180"+jumpinsert2[-8:-4].rjust(2,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"3421"+jumpinsert2[-4:].rjust(4,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"00200008")
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"00000000")
                        elif(BT==2):
                            ri=0
                            while(ri<=23):
                                rn=226+ri
                                out+=writeunit(inserta,"AF"+hex2(rn)+hex4((ri+4)*4))
                                ri+=1
                                out+=',\n    '
                                inserta+=4
                            out+=writeunit(inserta,"00000000")
                        else:
                            out+=writeunit(inserta,"00000000")
                    elif(v=="restoreloop"):
                        if(BT==1):
                            if(console==1 and pspu>=3):
                                jumpinsert2=checkaddress(hex8(inserta+16))
                                out+=writeunit(inserta,"3C01A0"+jumpinsert2[-8:-4].rjust(2,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"3421"+jumpinsert2[-4:].rjust(4,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"00200008")
                                out+=',\n    '
                                inserta+=4
                            for v2 in restoreloop1[:-1]:
                                if(v2=="restoresw"):
                                    swoff=inserta-int(jumpinsert,16)+13
                                    if(bend=="true"):
                                        swoff+=1
                                    out+=writeunit(inserta,"A3E1"+hex4(swoff))
                                else:
                                    out+=writeunit(inserta,v2)
                                out+=',\n    '
                                inserta+=4
                            out+=writeunit(inserta,restoreloop1[-1])
                            if(console==1 and pspu>=2):
                                jumpinsert2=checkaddress(hex8(inserta+16))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"3C0180"+jumpinsert2[-8:-4].rjust(2,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"3421"+jumpinsert2[-4:].rjust(4,"0"))
                                out+=',\n    '
                                inserta+=4
                                out+=writeunit(inserta,"00200008")
                        elif(BT==2):
                            ri=0
                            while(ri<=23):
                                rn=226+ri
                                out+=writeunit(inserta,"8F"+hex2(rn)+hex4((ri+4)*4))
                                ri+=1
                                out+=',\n    '
                                inserta+=4
                            out+=writeunit(inserta,"00000000")
                        else:
                            out+=writeunit(inserta,"00000000")
                    elif(v=="ret" and reta>-1):
                        out+=writeunit(inserta,ubranch(inserta,reta),"end of instruction section, return to backup/restore")
                    elif(v=="return"):
                        out+=writeunit(inserta,jal(int(jumpfrom,16)+8,1),"end of backup/restore, return to "+hex8(int(jumpfrom,16)+8))
                    elif(v=="insert"):
                        if(ita==""):
                            ita="3C1FA0"+jumpinsert[-8:-4].rjust(2,"0")
                            ita2="37FF"+jumpinsert[-4:].rjust(4,"0")
                        out+=writeunit(inserta,ita)
                        out+=',\n    '
                        inserta+=4
                        out+=writeunit(inserta,ita2)
                    elif(v=="jumper"):
                        branches.append(["jumper",inserta-4])
                        for jri,jrv in enumerate(jumpregisters):
                            RAV=""
                            after=0
                            if(jrv):
                                for r in jrv:
                                    if(r[0]==-100):
                                        branches.append([r[1],inserta-4])
                                    elif(r[0]==31 and r[2]==0):
                                        if(RA or JJ):
                                            RAV=r[1]
                                    elif(r[2]%2==1 or r[0]<=31+FP and (r[0]>-99 or r[0]<=-1000)):
                                        t=writeregister(inserta,r[0],r[1],r[2],r[3],r[4],reta,branches,todobranches)
                                        out+=t[0]
                                        inserta=t[1]
                                    elif(r[0]==-99 and len(jumpto)>jri and jumpto[jri]):
                                        after+=1
                                        t=writejumper(inserta,jumpto[jri],RAV,JJ,RA)
                                        out+=t[0]
                                        inserta=t[1]
                            if(after==0 and len(jumpto)>jri and jumpto[jri]):
                                jrend=0
                                if(jri+1>=len(jumpregisters)):
                                    jrend=1
                                t=writejumper(inserta,jumpto[jri],RAV,JJ,RA,jrend)
                                out+=t[0]
                                inserta=t[1]
                            else:
                                out+=writeunit(inserta,"00000000")
                    else:
                        out+=writeunit(inserta,v)
            else:
                print("outputting direct jump only")
                jumper=jal(jumpto[0],JJ)
                out+=writeunit(int(jumpfrom,16),jumper,"direct jump to "+str(jumpto[0]),0)
            for todo in todobranches:
                bret=branchlocation(todo[1],todo[2],branches)
                if(bret=="?#missing-branch#?"):
                    print("error, cannot find branch "+todo[2])
                else:
                    out=out.replace(todo[0],bret)
                    
            if(MO):
                MOi+=1
                if(out):
                    output(writelayer(out),outputn+"-"+str(MOi)+"-"+jumpto[0]+".bl")
                if(len(cjumpto)>MOi):
                    jumpto=[cjumpto[MOi]]
                    jumpregisters=[cjumpregisters[MOi]]
                else:
                    break
            else:
                if(out):
                    output(writelayer(out),outputn+".bl")
                break
    else:
        print("error: not enough valid data in input.txt to output meaningful code")

def checkaddress(a):
    ret=""
    while(a[0:1]=="0"):
        a=a[1:]
    if(len(a)==8):
        if(a[0:2]=="80" or a[0:2]=="A0"):
            ret=a[2:]
    elif(len(a)<=6):
        ret=a
    return ret
def checkregister(r,RA,JJ,FP):
    ret=[]
    ro=r
    r=r.replace("_","")
    print("check register: "+r)
    rr=r.lower().split(":")
    note=""
    if(len(rr)>2):
        note=rr[2]
        print("note: "+note)
    if(len(rr)>=2 and rr[1] or r.find("exit")==0):
        if(rr[0][0:7]=="corrupt"):
            cfn=ro.split(":")[1]
            if(cfn[-3:]!=".bl"):
                print("invalid corrupt file ("+cfn+"), must be a .bl file")
            elif(os.path.isfile(cfn)):
                print("converting corrupt file: "+cfn)
                global bend
                cf=open(cfn,"r")
                state=0
                address=0
                value=""
                rev=0
                note=""
                for v in cf:
                    if(v.find(":")!=-1):
                        p=0
                        if(state==0 and v.find('"IsEnabled":')!=-1):
                            if(v.replace(" ","").find(":true")!=-1):
                                state=1
                        elif(state==1 and v.find('"BigEndian":')!=-1):
                            if(v.replace(" ","").find(":"+bend)==-1):
                                rev=1
                        elif(state>0 and v.find('"Note":')!=-1):
                            state=2
                            p=3
                        elif(state==1 and v.find('"Address":')!=-1):
                            p=1
                        elif(state==1 and v.find('"ValueString":')!=-1):
                            p=2
                        if(p>0):
                            v2=v.replace(" ","").replace(",","").replace('"','').replace("\r","").replace("\n","")
                            vv=v2.split(":")
                            if(p==1):
                                address=int(vv[1])
                            elif(p==2):
                                value=vv[1]
                            elif(p==3):
                                note=vv[1]
                        if(state==2):
                            state=0
                            if(address and value):
                                prec=0
                                if(len(value)==2):
                                    prec=5
                                elif(len(value)==8):
                                    prec=1
                                if(prec>0):
                                    if(rev):
                                        value=revbytes(value)
                                    ret.append([29,hex8(address+int("80000000",16)),0,0,""])
                                    ret.append([0,value,prec,0,note])
                                else:
                                    print("corrupt unit error: value must be precision 1 or 4")
                            address=0
                            value=""
                            rev=0
                            note=""
            else:
                print("corrupt file not found: "+cfn)
        elif(FP and rr[0][0:1]=="f" and len(rr[0])>1):
            fpn=int(rr[0][1:])
            if(fpn<FP):
                rr2=re.sub(r'\W+','',rr[1])
                ret=[fpn+32,rr2[-16:],0,0,note]
                print("register id: f"+str(fpn))
                print("register val: "+rr2)
        else:
            regs=["at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7","s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","s8"]
            branch=-1
            rad=0
            if(rr[0][0:6]=="branch"):
                branch=rr[1]
                rr[0]=rr[0][6:]
            elif(rr[0][0:4]=="exit"):
                branch=-2
                rr[0]=rr[0][4:]
            if(RA or JJ or branch!=-1):
                regs.append("ra")
                rad=1
            if(branch!=-1):
                if(rr[0][0:2]=="if"):
                    rr[0]=rr[0][2:]
                    if(len(rr[0])>=4):
                        if(rr[0][0:2] in regs):
                            ifr=regs.index(rr[0][0:2])+1
                            rr[0]=rr[0][2:]
                            ifop=-1
                            if(rr[0][0:1]==">"):
                                ifop=6
                            elif(rr[0][0:1]=="<"):
                                ifop=4
                            elif(rr[0][0:1]=="="):
                                ifop=2
                            elif(rr[0][0:1]=="!"):
                                ifop=0
                            if(ifop!=-1):
                                if(rr[0][1:3] in regs):
                                    ifn=regs.index(rr[0][1:3])+1
                                    ifop+=8
                                else:
                                    ifn=int(rr[0][1:],0)
                                if(branch==-2):
                                    ret=[-5-ifop,0,ifr,ifn,note]
                                    print("conditional exit if "+str(ifr)+" "+str(ifop)+" "+str(ifn))
                                else:
                                    ret=[-6-ifop,branch,ifr,ifn,note]
                                    print("conditional branch to "+branch+" if "+str(ifr)+" "+str(ifop)+" "+str(ifn))
                            else:
                                print("invalid if condition sign")
                        else:
                            print("invalid if condition, register not found")
                    else:
                        print("invalid if condition")
                else:
                    if(branch==-2):
                        ret=[-3,0,0,0,note]
                        print("unconditional exit")
                    else:
                        ret=[-4,branch,0,0,note]
                        print("unconditional branch to "+branch)
            elif(rr[0][0:2] in regs):
                add=0
                if(rad==0):
                    regs.append("ra")
                if(rr[1][2:3]=="+"):
                    add=int(rr[1][3:])
                elif(rr[1][2:3]=="-" and rr[1][0:2]!="sp"):
                    add=-int(rr[1][3:])
                dec=0
                if(rr[1][0:1]=="+"):
                    dec=1
                elif(rr[1][0:1]=="-"):
                    dec=2
                rr2=re.sub(r'\W+','',rr[1])
                special=0
                rr3=rr2[-8:]
                rr4=-1
                if(dec==1):
                    rr3=hexn(int(rr3))
                elif(dec==2):
                    rr3=hexn(-int(rr3))
                elif(rr3[0:2] in regs):
                    if(len(rr3)>2 and rr3[0:2]=="sp"):
                        if(rr3[2:3]=="b"):
                            if(len(rr3)>3):
                                special+=24
                                rr3=rr[1][3:]
                                print("val = sp byte "+str(rr3))
                        elif(rr3[2:3]=="h"):
                            if(len(rr3)>3):
                                special+=40
                                rr3=rr[1][3:]
                                print("val = sp half "+str(rr3))
                        else:
                            special+=8
                            rr3=rr[1][2:]
                            print("val = sp word "+str(rr3))
                        plus=rr3.find("+")
                        if(plus>0):
                            add=int(rr3[plus+1:])
                            rr3=rr3[:plus]
                        else:
                            minus=rr3.find("-")
                            if(minus>0):
                                add=-int(rr3[minus+1:])
                                rr3=rr3[:minus]
                        rr3=int(rr3)
                    else:
                        special+=2
                        rr3=regs.index(rr3[0:2])+1
                        print("val = reg id "+str(rr3)+" add: "+str(add))
                if(len(rr[0])>2 and rr[0][0:2]=="sp"):
                    if(rr[0][2:3]=="b"):
                        if(len(rr[0])>3):
                            rr4=int(rr[0][3:])
                            special+=5
                            print("write byte to sp"+str(rr4)+" val: "+str(rr3))
                    elif(rr[0][2:3]=="h"):
                        if(len(rr[0])>3):
                            rr4=int(rr[0][3:])
                            special+=65
                            print("write half to sp"+str(rr4)+" val: "+str(rr3))
                    else:
                        rr4=int(rr[0][2:])
                        special+=1
                        print("write to sp"+str(rr4)+" val: "+str(rr3))
                    if(rr4<0):
                        rr4-=1000
                else:
                    rr4=regs.index(rr[0][0:2])+1
                    print("register id: "+str(rr4)+" val: "+str(rr3))
                ret=[rr4,rr3,special,add,note]
            elif(rr[0]=="code"):
                ret=[-2,rr[1][-8:],0,0,note]
                print("code: "+rr[1][-8:])
    elif(r[-1:]==":"):
        ret=["a"]
        if(r.lower().find("after")==0):
            ret=[-99,0,0,0,""]
            print("after")
        elif(r.lower().find("branch")==0):
            bn=r[6:-1]
            ret=[-100,bn,0,0,""]
            print("branch "+bn)
    return ret
def writejumper(inserta,jumpto,RAV,JJ,RA,end=0):
    out=""
    if(RAV):
        print("RAV: "+RAV)
        t=writeregister(inserta,1,RAV)
        out+=t[0]
        inserta=t[1]
        if(JJ):
            out+=writeunit(inserta,"0001F825")
            out+=',\n    '
            inserta+=4
        if(RA):
            out+=writeunit(int(jumpto,16),"0001F825")
            out+=',\n    '
    jumper=jal(jumpto,JJ)
    out+=writeunit(inserta,jumper,"jump to "+str(jumpto))
    out+=',\n    '
    inserta+=4
    out+=writeunit(inserta,"00000000")
    if(end==0):
        out+=',\n    '
        inserta+=4
    return [out,inserta]
def writeregister(inserta,id,val,special=0,add=0,note="",reta=0,branches=None,todobranches=None):
    out=""
    minusid=0
    if(id<-1000):
        minusid=1
        id+=1000
    if(id<-1 and not minusid): #branching
        if(id==-2):
            out+=writeunit(inserta,val,note)
            out+=',\n    '
            inserta+=4
        elif(id>=-20):
            brl=-1
            if(id%2==0):
                brl=val
            else:
                brl=reta
            bif=-1-int((id+1)/2+1)
            brr=0
            if(bif>=4):
                brr=1
                bif-=4
            print("branch location: "+str(brl)+"  branch type: "+str(bif)+" branch double register: "+str(brr)+" add: "+str(add)+" special: "+str(special))
            if(bif==-1):
                out+=writeunit(inserta,ubranch(inserta,brl,branches,todobranches),note)
            else:
                ifr1=special
                ifr2=1
                if(brr==0):
                    if(add==0):
                        ifr2=0
                    else:
                        t=writeregister(inserta,ifr2,hexn(add),0,0,note)
                        out+=t[0]
                        inserta=t[1]
                else:
                    ifr2=add
                ift=0
                if(bif==1):
                    ift=1
                elif(bif==2 or bif==3):
                    if(bif==2):
                        out+=writeunit(inserta,slt(ifr2,ifr1,ifr2),note)
                    else:
                        out+=writeunit(inserta,slt(ifr2,ifr2,ifr1),note)
                    out+=',\n    '
                    inserta+=4
                    ifr1=0
                out+=writeunit(inserta,cbranch(inserta,brl,ift,ifr1,ifr2,branches,todobranches),note)
            out+=',\n    '
            inserta+=4
            out+=writeunit(inserta,"00000000",note)
            out+=',\n    '
            inserta+=4
    elif(special%16>=8): #from memory
        global console
        if(special%2==1):  #memory->memory
            if(special%32>=16):
                out+=writeunit(inserta,"83A1"+hex4(val),note)
            elif(special%64>=32):
                out+=writeunit(inserta,"87A1"+hex4(val),note)
            else:
                out+=writeunit(inserta,"8FA1"+hex4(val),note)
            out+=',\n    '
            inserta+=4
            if(console==1):
                out+=writeunit(inserta,"00000000",note)
                out+=',\n    '
                inserta+=4
            if(add!=0):
                out+=writeunit(inserta,"2421"+hex4(add),note)
                out+=',\n    '
                inserta+=4
            if(special%8>=4):
                out+=writeunit(inserta,"A3A1"+hex4(id),note)
            elif(special%128>=64):
                out+=writeunit(inserta,"A7A1"+hex4(id),note)
            else:
                out+=writeunit(inserta,"AFA1"+hex4(id),note)
        else:                #memory->register
            if(special%32>=16):
                out+=writeunit(inserta,"83"+hex2(160+id)+hex4(val),note)
            elif(special%64>=32):
                out+=writeunit(inserta,"87"+hex2(160+id)+hex4(val),note)
            else:
                out+=writeunit(inserta,"8F"+hex2(160+id)+hex4(val),note)
            if(console==1):
                out+=writeunit(inserta,"00000000",note)
                out+=',\n    '
                inserta+=4
            if(add!=0):
                out+=',\n    '
                inserta+=4
                out+=writeunit(inserta,hex4(9216+33*id)+hex4(add),note)
        out+=',\n    '
        inserta+=4
    elif(special%4>=2): #from register
        out+=writeunit(inserta,"00"+hex2(val)+"0825",note)
        out+=',\n    '
        inserta+=4
        if(add!=0):
            out+=writeunit(inserta,"2421"+hex4(add),note)
            out+=',\n    '
            inserta+=4
        if(special%2==1): #register->memory
            if(special%8>=4):
                out+=writeunit(inserta,"A3A1"+hex4(id),note)
            elif(special%128>=64):
                out+=writeunit(inserta,"A7A1"+hex4(id),note)
            else:
                out+=writeunit(inserta,"AFA1"+hex4(id),note)
        else:               #register->register
            out+=writeunit(inserta,"0001"+hex2(id*8)+"25",note)
        out+=',\n    '
        inserta+=4
    elif(special%2==1): #immediate->memory
        t=writeregister(inserta,1,val,0,0,note)
        out+=t[0]
        inserta=t[1]
        if(special%8>=4):
            out+=writeunit(inserta,"A3A1"+hex4(id),note)
        elif(special%128>=64):
            out+=writeunit(inserta,"A7A1"+hex4(id),note)
        else:
            out+=writeunit(inserta,"AFA1"+hex4(id),note)
        out+=',\n    '
        inserta+=4
    else:           #immediate->register
        if(id>31):
            print("fp unimplemented")
        else:
            if(len(val)>4):
                out+=writeunit(inserta,"3C"+hex2(id)+val[-8:-4].rjust(4,"0"),note)
                out+=',\n    '
                inserta+=4
                op=13312+id*33
                out+=writeunit(inserta,hex4(op)+val[-4:].rjust(4,"0"),note)
            else:
                out+=writeunit(inserta,"24"+hex2(id)+val[-4:].rjust(4,"0"),note)
            out+=',\n    '
            inserta+=4
    return [out,inserta]
def jal(v,JJ):
    jop="C"
    if(JJ):
        jop="8"
    if(isinstance(v,str)):
        v=int(v,16)
    return "0"+jop+hex6(int(v/4))
def slt(rd,rs,rt):
    return hex6(int(rd*8+rt*256+rs*8192))+"2A"
def ubranch(fr,to,branches=None,todobranches=None):
    return "1000"+branchlocation(fr,to,branches,todobranches)
def cbranch(fr,to,ift,ifr1,ifr2,branches=None,todobranches=None):
    opn=4096
    if(ift==0):
        opn=5120
    return hex4(int(opn+ifr1*32+ifr2))+""+branchlocation(fr,to,branches,todobranches)
def branchlocation(fr,to,branches=None,todobranches=None):
    if(isinstance(to,str)):
        sr=searchdl(branches,to)
        if(sr):
            return hex4(int((sr-fr)/4))
        else:
            if(todobranches!=None):
                todo="?#"+str(len(todobranches))+"#?"
                todobranches.append([todo,fr,to])
                return todo
            else:
                return "?#missing-branch#?"
    else:
        return hex4(int((to-fr)/4))
def searchdl(l,s):
    ret=0
    for v in l:
        if(v[0]==s):
            ret=v[1]
            break
    return ret
def revbytes(v):
    ret=""
    i=0
    while(i<len(v)):
        if(i==0):
            ret+=v[-2:]
        else:
            ret+=v[-i-2:-i]
        i+=2
    return ret
def writelayer(v):
    ret='{\n  "Layer": [\n    '+v+'\n  ]\n}'
    return ret
def writeunit(a,v,note="",l=1,s=0):
    global mdom,bend
    ret='{\n      "IsEnabled": true,\n      "IsLocked": false,\n      "BigEndian": '
    ret+=bend
    ret+=',\n      "Domain": "'
    ret+=mdom
    ret+='",\n      "Address": '
    ret+=str(a)
    ret+=',\n      "Precision": 4,\n      "Source": "'
    x='VALUE'
    if(s):
        x='STORE'
    ret+=x
    ret+='",\n      "StoreTime": "IMMEDIATE",\n      "StoreType": "ONCE",\n      "ValueString": "'
    ret+=str(v)
    ret+='",\n      "SourceDomain": '
    x='null'
    if(s):
        x='"'+mdom+'"'
    ret+=x
    ret+=',\n      "SourceAddress": '
    ret+=str(s)
    ret+=',\n      "TiltValue": 0,\n      "ExecuteFrame": 0,\n      "Lifetime": '
    ret+=str(l)
    ret+=',\n      "Loop": false,\n      "LoopTiming": 50,\n      "StoreLimiterSource": "ADDRESS",\n      "LimiterTime": "NONE",\n      "LimiterListHash": null'
    ret+=',\n      "InvertLimiter": false,\n      "GeneratedUsingValueList": false,\n      "Note": "'
    ret+=note
    ret+='"\n    }'
    return ret
def output(out,fn):
    print("writing to "+fn)
    outputf=open(fn,"w")
    outputf.write(out)
    outputf.close()
def hexn(n):
    if(abs(n)>=8**5):
        return hex8(n)
    else:
        return hex4(n)
def hex2(n):
    return "%s"%("00%x"%(n&0xff))[-2:]
def hex4(n):
    return "%s"%("0000%x"%(n&0xffff))[-4:]
def hex6(n):
    return "%s"%("000000%x"%(n&0xffffff))[-6:]
def hex8(n):
    return "%s"%("00000000%x"%(n&0xffffffff))[-8:]
def growlist(list,ti,gv):
    while(len(list)<=ti):
        list.append(gv)
    return list
main()