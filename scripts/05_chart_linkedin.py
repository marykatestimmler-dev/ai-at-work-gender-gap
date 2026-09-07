"""LinkedIn share image: what women and men use AI for at work (sorted by size of gap)."""
import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.font_manager as fm
FONT_DIR='fonts'
if os.path.isdir(FONT_DIR):
    for f in os.listdir(FONT_DIR):
        if f.endswith('.ttf'): fm.fontManager.addfont(os.path.join(FONT_DIR,f))
    plt.rcParams['font.family']='Inter'
G=json.load(open('data/derived/gender.json')); T=G['tasks']
BG='#FDFBF7'; W='#F26B5B'; M='#1B6B93'; INK='#1F2933'; INK2='#6B7280'; LINE='#D9D4C7'
items=sorted(T,key=lambda k:-abs(T[k]['users']['gap']))   # biggest gap at top
fig,ax=plt.subplots(figsize=(8,7.2),dpi=200); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
yy=np.arange(len(items))[::-1]
for yi,k in zip(yy,items):
    f,m=T[k]['users']['female']*100,T[k]['users']['male']*100
    ax.plot([f,m],[yi,yi],color=LINE,lw=4,zorder=1,solid_capstyle='round')
    lo,hi=min(f,m),max(f,m)
    if hi-lo>=4:
        ax.text(lo-2.2,yi,f'{lo:.0f}%',ha='right',va='center',fontsize=11,color=INK2); ax.text(hi+2.2,yi,f'{hi:.0f}%',va='center',fontsize=11,color=INK,fontweight='semibold')
    else:
        ax.text(hi+2.2,yi,f'{f:.0f}% / {m:.0f}%',va='center',fontsize=11,color=INK2)
ax.scatter([T[k]['users']['female']*100 for k in items],yy,color=W,s=150,zorder=3,label='Women',edgecolor=BG,linewidth=1.5)
ax.scatter([T[k]['users']['male']*100 for k in items],yy,color=M,s=150,zorder=3,label='Men',edgecolor=BG,linewidth=1.5)
ax.set_yticks(yy); ax.set_yticklabels(items,fontsize=12.5,color=INK)
ax.set_xlim(0,100); ax.set_xticks([0,25,50,75,100]); ax.set_xticklabels(['0','25','50','75','100%'],fontsize=10.5,color=INK2)
for s in ['top','right','left']: ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(LINE); ax.grid(axis='x',color='#ECE8DD',lw=1); ax.set_axisbelow(True); ax.tick_params(length=0)
ax.set_xlabel('Share of workers who use AI at work and report using it for this task',fontsize=11,color=INK2,labelpad=10)
ax.legend(frameon=False,fontsize=12,loc='lower right',markerscale=1.1)
fig.text(0.02,0.965,'What women and men use AI for at work',fontsize=20,fontweight='bold',color=INK,ha='left',va='top')
fig.text(0.02,0.015,'Source: U.S. Census Bureau, Household Trends and Outlook Pulse Survey, March 2026 (n = 4,091 AI users). Weighted.',fontsize=9,color=INK2,ha='left')
fig.tight_layout(rect=(0,0.03,1,0.93)); fig.savefig('charts/linkedin_gender_tasks.png',facecolor=BG); print('ok')
