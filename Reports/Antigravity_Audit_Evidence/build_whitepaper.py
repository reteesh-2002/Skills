from pathlib import Path
import subprocess, json, re, html, textwrap, math
from reportlab.pdfgen import canvas
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, PageBreak, CondPageBreak, Table, TableStyle, Preformatted, Flowable, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/audit'
MD=OUT/'Antigravity_Architecture_Whitepaper.md'
PDF=OUT/'Antigravity_Architecture_Whitepaper.pdf'
for name, file in [('Sans','DejaVuSans.ttf'),('SansBold','DejaVuSans-Bold.ttf'),
                   ('Mono','DejaVuSansMono.ttf'),('Serif','DejaVuSerif.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('Sans',normal='Sans',bold='SansBold',italic='Sans',boldItalic='SansBold')
NAVY=colors.HexColor('#142D40'); TEAL=colors.HexColor('#087F8C'); GRAY=colors.HexColor('#546574')
W,H=A4; M=46; CW=W-2*M
styles={
 'body':ParagraphStyle('body',fontName='Sans',fontSize=9.1,leading=13.3,spaceAfter=7,textColor=NAVY),
 'h2':ParagraphStyle('h2',fontName='SansBold',fontSize=18,leading=22,spaceAfter=14,textColor=NAVY,keepWithNext=True),
 'h3':ParagraphStyle('h3',fontName='SansBold',fontSize=12,leading=16,spaceBefore=13,spaceAfter=7,textColor=TEAL,keepWithNext=True),
 'h4':ParagraphStyle('h4',fontName='SansBold',fontSize=10,leading=14,spaceBefore=10,spaceAfter=6,keepWithNext=True),
 'small':ParagraphStyle('small',fontName='Sans',fontSize=7.7,leading=10.7,spaceAfter=4,textColor=NAVY),
 'cell':ParagraphStyle('cell',fontName='Sans',fontSize=7.7,leading=10.7,textColor=NAVY),
 'headcell':ParagraphStyle('headcell',fontName='SansBold',fontSize=7.8,leading=10.6,textColor=colors.white),
 'code':ParagraphStyle('code',fontName='Mono',fontSize=7.35,leading=10.1,spaceBefore=5,spaceAfter=9,backColor=colors.HexColor('#F1F5F7'),borderPadding=7),
 'bullet':ParagraphStyle('bullet',fontName='Sans',fontSize=9.1,leading=13.3,spaceAfter=6,leftIndent=13,firstLineIndent=-10,textColor=NAVY),
}

def esc(s):return html.escape(s,quote=True)
def inline(xs):
    out=''
    for x in xs:
        t=x['t']; c=x.get('c')
        if t=='Str':out+=esc(c)
        elif t in ('Space','SoftBreak','LineBreak'):out+=' '
        elif t=='Strong':out+='<b>'+inline(c)+'</b>'
        elif t=='Emph':out+='<i>'+inline(c)+'</i>'
        elif t=='Code':out+='<font name="Mono" size="8">'+esc(c[1])+'</font>'
        elif t=='Link':out+='<link href="'+esc(c[2][0])+'" color="#087F8C">'+inline(c[1])+'</link>'
        elif t=='Quoted':out+='“'+inline(c[1])+'”'
        elif t=='Math':out+=esc(c[1])
        elif t=='Span':out+=inline(c[1])
    return out
def plain(xs):return re.sub('<[^>]+>','',inline(xs))
def blocks_text(bs):
    return '<br/>'.join(inline(b['c']) for b in bs if b['t'] in ('Plain','Para'))

class Diagram(Flowable):
    def __init__(self, kind):
        super().__init__();self.kind=kind;self.width=CW
        self.height={0:420,1:355,2:400,3:330}[kind]
    def wrap(self,a,b):return self.width,self.height
    def draw(self):
        c=self.canv; w=self.width; h=self.height
        c.setFillColor(colors.HexColor('#F4F8FA'));c.roundRect(0,0,w,h,7,fill=1,stroke=0)
        if self.kind in (0,3):self.sequence(c,w,h)
        else:self.graph(c,w,h)
    def label(self,c,txt,x,y,width=84,size=7.1):
        p=Paragraph(esc(txt),ParagraphStyle('d',fontName='Sans',fontSize=size,leading=size+2,alignment=1,textColor=NAVY))
        _,ph=p.wrap(width,80);p.drawOn(c,x-width/2,y-ph/2)
    def arrow(self,c,x1,y1,x2,y2,dashed=False):
        c.setStrokeColor(TEAL);c.setLineWidth(.85)
        c.setDash(3,2) if dashed else c.setDash()
        c.line(x1,y1,x2,y2);c.setDash()
        a=math.atan2(y2-y1,x2-x1);size=4
        for d in (-.5,.5):c.line(x2,y2,x2-size*math.cos(a+d),y2-size*math.sin(a+d))
    def sequence(self,c,w,h):
        if self.kind==0:
            names=['Debugger','Evidence','QA','Shipping','User']
            events=[(0,1,'Patch + snapshot'),(1,0,'Durable receipt'),(0,4,'Milestone'),
            (2,1,'Read contract'),(2,1,'Run verification'),(1,2,'Results + warnings'),
            (2,1,'Publish assessment'),(2,4,'State milestone'),(3,1,'Validate final gate'),
            (1,3,'Eligible: scoped capability'),(3,1,'Release receipt'),(3,4,'Final evidence card'),
            (1,3,'Otherwise: block + reasons'),(3,4,'Blocked card + next action')]
        else:
            names=['Coordinator','Lease service','Worker A','Worker B','Integrator']
            events=[(0,1,'Claim T'),(1,2,'Generation 7'),(2,1,'Renew'),
             (0,1,'Reconcile expired lease'),(1,3,'Generation 8; fence A'),
             (3,1,'Candidate at generation 8'),(1,4,'Accept candidate'),
             (2,1,'Late generation 7'),(1,2,'Reject stale generation'),
             (4,1,'Integrated snapshot'),(1,0,'Reverify affected checks')]
        xs=[38+i*(w-76)/4 for i in range(5)]
        top=h-30; bottom=20
        for x,name in zip(xs,names):
            c.setFillColor(colors.white);c.setStrokeColor(colors.HexColor('#BCD0DB'))
            c.roundRect(x-35,top-13,70,26,4,fill=1,stroke=1)
            self.label(c,name,x,top,66)
            c.setDash(2,3);c.line(x,top-14,x,bottom);c.setDash()
        gap=(h-69)/len(events)
        for i,(a,b,txt) in enumerate(events):
            y=top-34-i*gap
            self.arrow(c,xs[a],y,xs[b],y, i in [1,5,9,12])
            tw=max(75,abs(xs[a]-xs[b])-5)
            self.label(c,txt,(xs[a]+xs[b])/2,y+8,tw,6.6)
    def graph(self,c,w,h):
        if self.kind==1:
            nodes={'u':(95,320,'User intent / authorization'),'c':(95,260,'Coordinator / specialists'),
             'p':(265,260,'Policy / state service'),'x':(265,190,'Execution proxy'),
             'w':(420,190,'Task sandboxes'),'e':(265,120,'Evidence store'),
             'v':(420,60,'Adapters / verifier'),'r':(420,320,'Release gateway'),
             'h':(95,190,'Card renderer'),'m':(95,60,'Memory / search')}
            edges=[('u','c'),('c','p'),('p','x'),('x','w'),('x','e'),('e','v'),('v','p'),('p','r'),('p','h'),('h','u'),('e','m'),('m','c')]
        else:
            nodes={'p':(90,365,'Planned'),'l':(250,365,'Leased'),'r':(410,365,'Running'),
             'i':(410,265,'Interrupted'),'c':(250,265,'Candidate'),
             'v':(90,185,'Verifying'),'b':(410,155,'Blocked'),
             'e':(90,85,'Eligible'),'s':(250,85,'Stale'),'z':(90,25,'Released')}
            edges=[('p','l'),('l','r'),('r','c'),('r','i'),('i','p'),('c','v'),('c','b'),('v','e'),('v','b'),('e','s'),('s','v'),('e','z'),('b','p')]
        for a,b in edges:
            xa,ya,_=nodes[a];xb,yb,_=nodes[b]
            d=math.hypot(xb-xa,yb-ya);dx=(xb-xa)/d;dy=(yb-ya)/d
            self.arrow(c,xa+dx*32,ya+dy*16,xb-dx*42,yb-dy*19)
        for x,y,t in nodes.values():
            c.setFillColor(colors.white);c.setStrokeColor(colors.HexColor('#B5C9D4'))
            c.roundRect(x-62,y-19,124,38,5,fill=1,stroke=1);self.label(c,t,x,y,116,7.1)

class Doc(BaseDocTemplate):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        frame=Frame(M,45,CW,H-91,id='normal',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='normal',frames=frame,onPage=self.page))
    def page(self,c,d):
        if d.page==1:return
        c.saveState();c.setStrokeColor(colors.HexColor('#CCD7DF'));c.setLineWidth(.5)
        c.line(M,H-32,W-M,H-32)
        c.setFont('Sans',7);c.setFillColor(GRAY)
        c.drawString(M,H-24,'ANTIGRAVITY ENGINEERING SUITE  /  ARCHITECTURAL AUDIT')
        c.drawString(M,25,'25 September 2026  •  Research and implementation blueprint')
        c.drawRightString(W-M,25,str(d.page));c.restoreState()
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name=='h2' and f.getPlainText()!='Contents':
            text=f.getPlainText(); key='section-'+str(self.seq.nextf('section'))
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,0)
            self.notify('TOCEntry',(0,text,self.page,key))

ast=json.loads(subprocess.check_output(['pandoc',str(MD),'-f','gfm','-t','json']))
story=[]
story.append(Spacer(1,65))
story.append(Paragraph('ENGINEERING WHITEPAPER',ParagraphStyle('kicker',fontName='SansBold',fontSize=10,textColor=TEAL,spaceAfter=25)))
story.append(Paragraph('From Prompt Protocols<br/>to an Evidence-Controlled<br/>Engineering Runtime',ParagraphStyle('cover',fontName='SansBold',fontSize=29,leading=36,textColor=NAVY,spaceAfter=26)))
story.append(Paragraph('Architectural feasibility, adversarial testing, and a successor blueprint for the Antigravity Engineering Skills Suite',ParagraphStyle('subtitle',fontName='Sans',fontSize=15,leading=22,textColor=GRAY,spaceAfter=35)))
story.append(Paragraph('25 SEPTEMBER 2026  |  VERSION 1.0',styles['h3']))
story.append(Spacer(1,40))
story.append(Paragraph('<b>Central finding</b><br/>Keep the specialist skills. Move evidence capture, state transitions, ownership, and release authority into a deterministic runtime.',ParagraphStyle('coverbox',fontName='Sans',fontSize=12,leading=18,backColor=colors.HexColor('#EEF5F7'),borderPadding=16,textColor=NAVY)))
story.append(Spacer(1,30))
story.append(Paragraph('38 primary web references • Four adversarial scenarios • Nine local failure probes<br/>Typed contracts, lifecycle diagrams, and a phased migration roadmap',styles['body']))
story.append(PageBreak())
story.append(Paragraph('Contents',styles['h2']))
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Sans',fontSize=9.3,leading=15,spaceBefore=7,textColor=NAVY)]
story.append(toc)
story.append(Spacer(1,22))
story.append(Paragraph('<b>Evidence boundary.</b> The current ten-file suite was not available. This report audits the supplied design, current primary documentation, an earlier orchestrator artifact, and local counterexamples. It does not certify an installed AGY release.',styles['body']))

diagram_index=0
def addblocks(blocks, listprefix=None):
    global diagram_index
    for b in blocks:
        t=b['t'];c=b.get('c')
        if t=='Header':
            level,attr,ins=c;txt=inline(ins)
            if level==1:continue
            if level==2:
                if plain(ins).startswith('Architectural feasibility'):continue
                story.append(PageBreak() if plain(ins) in ('Executive summary','References and source register') else CondPageBreak(210));story.append(Spacer(1,12));story.append(Paragraph(txt,styles['h2']))
            else:story.append(Paragraph(txt,styles['h3' if level==3 else 'h4']))
        elif t in ('Para','Plain'):
            if plain(c).startswith('Engineering whitepaper |') or plain(c).startswith('Scope:'):continue
            story.append(Paragraph(inline(c),styles['body']))
        elif t=='BulletList':
            for item in c:
                for j,bb in enumerate(item):
                    if bb['t'] in ('Para','Plain'):
                        story.append(Paragraph(('• ' if j==0 else '')+inline(bb['c']),styles['bullet']))
                    else:addblocks([bb])
        elif t=='OrderedList':
            start=c[0][0]
            for idx,item in enumerate(c[1],start):
                for j,bb in enumerate(item):
                    if bb['t'] in ('Para','Plain'):story.append(Paragraph((f'{idx}. ' if j==0 else '')+inline(bb['c']),styles['bullet']))
                    else:addblocks([bb])
        elif t=='CodeBlock':
            attr,code=c
            if 'mermaid' in attr[1]:
                story.append(Spacer(1,8));story.append(Diagram(diagram_index));diagram_index+=1
                story.append(Paragraph('Figure '+str(diagram_index)+'. '+['Evidence lifecycle and release gate.','Control, execution, evidence and presentation boundaries.','Task lifecycle with invalidation and recovery.','Lease fencing rejects stale worker completion.'][diagram_index-1],styles['small']))
                story.append(Spacer(1,8))
            else:
                lines=[]
                for line in code.splitlines():
                    lines.extend(textwrap.wrap(line,width=103,replace_whitespace=False,drop_whitespace=False,subsequent_indent='  ') or [''])
                story.append(Preformatted('\n'.join(lines),styles['code']))
        elif t=='Table':
            _,caption,specs,head,bodies,foot=c
            rows=head[1]+[r for body in bodies for r in body[2]+body[3]]+foot[1]
            n=len(specs);data=[]
            for ri,row in enumerate(rows):
                cells=row[1]
                data.append([Paragraph(blocks_text(cell[4]),styles['headcell' if ri==0 else 'cell']) for cell in cells])
            # Slightly prioritize explanatory columns over category labels.
            if n==2:weights=[.28,.72]
            elif n==3:weights=[.26,.36,.38]
            elif n==4:weights=[.18,.28,.27,.27]
            elif n==5:weights=[.12,.21,.25,.29,.13]
            else:weights=[1/n]*n
            table=Table(data,colWidths=[CW*x for x in weights],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([
             ('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
             ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
             ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
             ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F5F7'),colors.white]),
             ('LINEBELOW',(0,0),(-1,0),.7,TEAL),
             ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D8E2E7'))]))
            story.append(Spacer(1,5));story.append(table);story.append(Spacer(1,10))
        elif t=='BlockQuote':addblocks(c)
        elif t in ('HorizontalRule','Null'):pass
        else:print('UNHANDLED',t)

addblocks(ast['blocks'])
doc=Doc(str(PDF),pagesize=A4,title='Antigravity Engineering Skills Suite: Architectural Audit',author='Engineering Research',leftMargin=M,rightMargin=M,topMargin=46,bottomMargin=45)
doc.multiBuild(story)
print(PDF)
