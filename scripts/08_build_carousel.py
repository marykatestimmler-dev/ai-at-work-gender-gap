"""LinkedIn carousel: the AI gender gap in four slides. Uniform 1600x1600 PNGs + a 4-page PDF."""
import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.font_manager as fm
from matplotlib.backends.backend_pdf import PdfPages
FONT_DIR='fonts'
if os.path.isdir(FONT_DIR):
    for f in os.listdir(FONT_DIR):
        if f.endswith('.ttf'): fm.fontManager.addfont(os.path.join(FONT_DIR,f))
    plt.rcParams['font.family']='Inter'
OUT='charts/carousel'; os.makedirs(OUT,exist_ok=True)

BG='#FDFBF7'; W='#F26B5B'; M='#0E6C99'; INK='#1F2933'; INK2='#6B7280'; RULE='#E3DED2'; GAPC='#8A8577'; Z=1.645
FIG=(8,8); DPI=200; NP=4
SRC='Source: U.S. Census Bureau, Household Trends and Outlook Pulse Survey, March 2026.'

def frame(title,page,ts=22):
    fig=plt.figure(figsize=FIG,dpi=DPI); fig.patch.set_facecolor(BG)
    fig.text(0.055,0.952,title,fontsize=ts,fontweight='bold',color=INK,ha='left',va='top',linespacing=1.35)
    fig.text(0.945,0.952,f'{page} / {NP}',fontsize=10.5,color=INK2,ha='right',va='top')
    return fig
NOTE='The Census Bureau is revising the March 2026 weights. Weighted and unweighted analyses give the same pattern throughout.'
def source(fig,extra='',byline=False):
    fig.text(0.055,0.038,'\n'.join([SRC]+([extra] if extra else [])+[NOTE]),fontsize=8.5,color=INK2,ha='left',va='bottom',linespacing=1.6)
    if byline:
        fig.text(0.055,0.122,'Mary Kate Stimmler, PhD  ·  linkedin.com/in/marykatestimmler',fontsize=10,color=INK,ha='left',va='bottom')
def bare(ax):
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])

w=pd.read_pickle('data/derived/workers2.pkl'); RW=[f'PWEIGHT{i}' for i in range(1,81)]
def wmean(df,y,wt='PWEIGHT'):
    s=df[df[y].notna()]; return np.average(s[y],weights=s[wt])
def sdr_se(df,y):
    s=df[df[y].notna()]; th=np.average(s[y],weights=s.PWEIGHT)
    reps=np.array([np.average(s[y],weights=s[r]) for r in RW]); return np.sqrt(4/80*((reps-th)**2).sum())

# ============ Slide 1: parity
fig=frame('At first glance, there appears to be\nno gender gap in AI use...',1)
ax=fig.add_axes([0.055,0.285,0.89,0.475]); ax.set_facecolor(BG)
for i,(lab,sex,col) in enumerate([('Women',0.0,W),('Men',1.0,M)]):
    g=w[(w.male==sex)&w.any_ai.notna()]; v=wmean(g,'any_ai')*100; se=sdr_se(g,'any_ai')*100; y=1-i
    ax.barh(y,v,height=0.40,color=col,zorder=2)
    ax.errorbar(v,y,xerr=se*Z,fmt='none',ecolor=INK,elinewidth=1.6,capsize=6,capthick=1.6,zorder=3)
    ax.text(v+se*Z+2.5,y,f'{v:.0f}%',ha='left',va='center',fontsize=40,fontweight='bold',color=INK)
    ax.text(0,y+0.30,lab,ha='left',va='bottom',fontsize=15,color=INK)
ax.set_xlim(0,78); ax.set_ylim(-0.55,1.75); bare(ax)
fig.text(0.055,0.805,'Share of employed adults who have used AI for a work task',fontsize=13.5,color=INK2,ha='left',va='top')
fig.text(0.055,0.225,'Bars show 90% confidence intervals. The two overlap: the difference is\nwithin the survey’s margin of error.',fontsize=11,color=INK2,ha='left',va='top',linespacing=1.6)
source(fig,'Weighted; n = 6,573 employed adults.',byline=True)
fig.savefig(f'{OUT}/slide1.png',facecolor=BG); plt.close()

# ============ Slide 2: intensity ladder, with a gap column
LEV=[('any_ai','Have used AI for a work task'),('ai_lastweek','Used AI at work last week'),('ai_daily','Used AI at work every day last week')]
GX=66.0; SP=1.45
fig=frame('The gender gap opens when you ask\nhow often AI is used',2)
ax=fig.add_axes([0.055,0.112,0.89,0.663]); ax.set_facecolor(BG)
rows=len(LEV)
for gi,(y,lab) in enumerate(LEV):
    base=(rows-1-gi)*SP
    ax.text(0,base+0.50,lab,ha='left',va='bottom',fontsize=13.5,color=INK)
    vals={}
    for j,(nm,sex,col) in enumerate([('Women',0.0,W),('Men',1.0,M)]):
        g=w[(w.male==sex)&w[y].notna()]; v=wmean(g,y)*100; vals[nm]=v
        yy_=base+(0.20 if j==0 else -0.20)
        ax.barh(yy_,v,height=0.30,color=col,zorder=2)
        t=ax.text(v+1.5,yy_,f'{v:.0f}%',ha='left',va='center',fontsize=15,fontweight='bold',color=INK)
    gap=vals['Men']-vals['Women']
    ax.barh(base,gap,left=GX,height=0.34,color=GAPC,zorder=2)
    ax.text(GX+gap+1.5,base,f'+{gap:.0f}',ha='left',va='center',fontsize=15,fontweight='bold',color=INK)
ax.text(GX,(rows-1)*SP+0.50,'gap, in points',ha='left',va='bottom',fontsize=11,color=INK2)
ax.set_xlim(0,86); ax.set_ylim(-0.72,(rows-1)*SP+0.92); bare(ax)
fig.text(0.055,0.816,'The same workers, counted three ways',fontsize=13.5,color=INK2,ha='left',va='top')
for lx,(nm,col) in zip([0.60,0.755],[('Women',W),('Men',M)]):
    fig.patches.append(plt.Rectangle((lx,0.799),0.022,0.014,transform=fig.transFigure,facecolor=col,edgecolor='none'))
    fig.text(lx+0.030,0.7995,nm,fontsize=12.5,color=INK2,ha='left',va='baseline')
source(fig,'Weighted; n = 6,573 employed adults (6,550 for the frequency measures).')
fig.savefig(f'{OUT}/slide2.png',facecolor=BG); plt.close()

# ============ Slide 3: composition
sc=w[w.any_ai.notna()&w.occ.notna()].copy()
rate=sc.groupby('occ').apply(lambda g: np.average(g.any_ai,weights=g.PWEIGHT))*100
dist=sc.groupby(['occ','male']).PWEIGHT.sum().unstack(); dist=dist/dist.sum()*100
d=pd.DataFrame({'rate':rate,'wshare':dist[0.0],'mshare':dist[1.0]}).drop('Farming/fishing/forestry').sort_values('rate',ascending=False)
NAMES={'Computer':'Computer & IT','Engineering/architecture/sciences':'Engineering & sciences',
 'Management/business/finance/legal':'Management, business & legal','Education/social svc/arts/media':'Education, social services & arts',
 'Office & admin support':'Office & admin support','Sales':'Sales','Healthcare':'Healthcare',
 'Construction/production/transport':'Construction, production & transport','Service (security/food/cleaning/care)':'Food, cleaning, security & care'}
GUT=26.0
fig=frame("Women hold more jobs in 'High AI' occupations",3,ts=20)
fig.text(0.055,0.884,"Women hold more jobs in occupations where most workers use AI — education,\n"
         "admin, and (at almost exactly half) healthcare. Men hold more of the construction,\n"
         "production and transport jobs, where AI use is very low. That alone should mean women\n"
         "use AI about 5 points more often than men. Something is going on inside the jobs.",
         fontsize=11.5,color=INK2,ha='left',va='top',linespacing=1.6)
ax=fig.add_axes([0.055,0.105,0.89,0.655]); ax.set_facecolor(BG)
n=len(d); yy=np.arange(n)[::-1]
for yi,(occ,r) in zip(yy,d.iterrows()):
    ax.barh(yi,-r.wshare,left=-GUT,height=0.52,color=W,zorder=2)
    ax.barh(yi, r.mshare,left= GUT,height=0.52,color=M,zorder=2)
    ax.text(-GUT-r.wshare-1.8,yi,f'{r.wshare:.0f}%',ha='right',va='center',fontsize=11,color=INK,fontweight='semibold')
    ax.text( GUT+r.mshare+1.8,yi,f'{r.mshare:.0f}%',ha='left', va='center',fontsize=11,color=INK,fontweight='semibold')
    ax.text(0,yi+0.17,NAMES[occ],ha='center',va='center',fontsize=10.5,color=INK)
    ax.text(0,yi-0.20,f'{r.rate:.0f}% use AI',ha='center',va='center',fontsize=9.5,color=INK2)
    ax.plot([-GUT+0.4,GUT-0.4],[yi-0.46,yi-0.46],color=RULE,lw=0.8,zorder=1)
ax.set_xlim(-70,70); ax.set_ylim(-0.75,n+0.15); bare(ax)
ax.text(-GUT-7,n-0.22,'W O M E N',ha='center',va='center',fontsize=10.5,color=W,fontweight='bold')
ax.text( GUT+7,n-0.22,'M E N',ha='center',va='center',fontsize=10.5,color=M,fontweight='bold')
ax.text(0,n-0.22,'share of employment',ha='center',va='center',fontsize=9.5,color=INK2)
source(fig,'Weighted. Occupations ordered by the share of workers who have used AI. Farming, fishing and forestry omitted (1% of workers).')
fig.savefig(f'{OUT}/slide3.png',facecolor=BG); plt.close()

# ============ Slide 4: task mix
G=json.load(open('data/derived/gender.json')); T=G['tasks']
items=sorted(T,key=lambda k:-abs(T[k]['users']['gap']))
fig=frame('The gender gap is based on\nfour technical tasks',4)
ax=fig.add_axes([0.30,0.183,0.66,0.609]); ax.set_facecolor(BG)
yy=np.arange(len(items))[::-1]
for yi,k in zip(yy,items):
    f_,m_=T[k]['users']['female']*100,T[k]['users']['male']*100
    ax.plot([f_,m_],[yi,yi],color=RULE,lw=4,zorder=1,solid_capstyle='round')
    lo,hi=min(f_,m_),max(f_,m_)
    if hi-lo>=4:
        ax.text(lo-2.4,yi,f'{lo:.0f}%',ha='right',va='center',fontsize=10.5,color=INK2)
        ax.text(hi+2.4,yi,f'{hi:.0f}%',ha='left',va='center',fontsize=10.5,color=INK,fontweight='semibold')
    else:
        ax.text(hi+2.4,yi,f'{f_:.0f}% / {m_:.0f}%',ha='left',va='center',fontsize=10.5,color=INK2)
ax.scatter([T[k]['users']['female']*100 for k in items],yy,color=W,s=135,zorder=3,label='Women',edgecolor=BG,linewidth=1.5)
ax.scatter([T[k]['users']['male']*100 for k in items],yy,color=M,s=135,zorder=3,label='Men',edgecolor=BG,linewidth=1.5)
ax.set_yticks(yy); ax.set_yticklabels(items,fontsize=12,color=INK)
ax.set_xlim(0,100); ax.set_xticks([0,25,50,75,100]); ax.set_xticklabels(['0','25','50','75','100%'],fontsize=10,color=INK2)
for sp in ['top','right','left']: ax.spines[sp].set_visible(False)
ax.spines['bottom'].set_color(RULE); ax.grid(axis='x',color='#ECE8DD',lw=1); ax.set_axisbelow(True); ax.tick_params(length=0)
ax.legend(frameon=False,fontsize=12,loc='lower right',markerscale=1.05)
fig.text(0.055,0.816,'Share of workers who use AI at work and report using it for this task',fontsize=13.5,color=INK2,ha='left',va='top')
source(fig,'Weighted; n = 4,091 workers who have used AI for at least one work task.\n'
            'Data, code and the full write-up: github.com/marykatestimmler-dev/ai-at-work-gender-gap',byline=True)
fig.savefig(f'{OUT}/slide4.png',facecolor=BG); plt.close()

with PdfPages(f'{OUT}/AI_gender_gap_carousel.pdf') as pdf:
    for f in [f'{OUT}/slide{i}.png' for i in (1,2,3,4)]:
        fg=plt.figure(figsize=FIG,dpi=DPI); fg.patch.set_facecolor(BG)
        a=fg.add_axes([0,0,1,1]); a.axis('off'); a.imshow(plt.imread(f)); pdf.savefig(fg,facecolor=BG); plt.close()
print('ok')
