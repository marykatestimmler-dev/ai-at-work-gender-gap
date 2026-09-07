import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
G=json.load(open('data/derived/gender.json'))
BLUE='#2a78d6'; ORANGE='#eb6834'; GRAY='#9a9891'; INK='#0b0b0b'; INK2='#52514e'; SURF='#fcfcfb'; Z=1.645
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.edgecolor':'#d8d6cf','axes.linewidth':0.6,'axes.titleweight':'bold','axes.titlesize':10.5,'axes.titlelocation':'left','axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2,'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.dpi':200})
def clean(ax,x=True):
    for s in ['top','right']: ax.spines[s].set_visible(False)
    ax.grid(axis='x' if x else 'y',color='#e6e4dd',lw=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
short={'0 Raw':'Raw gap','1 + age, race, region, metro':'+ age, race, region','2 + education, income':'+ education, income','3 + occupation, sector, telework':'+ occupation, sector, telework','4 + family: marital, kids by age, hh size':'+ marital, children, hh size','5 + health, language, insurance, wellbeing (kitchen sink)':'+ health, language, wellbeing'}

# G1: ladder, 3 panels (any, daily, hours)
fig,axs=plt.subplots(1,3,figsize=(6.5,3.2))
for ax,(y,ttl,mult,unit) in zip(axs,[('any_ai','Any AI use','100','pp'),('ai_daily','Daily use','100','pp'),('hrs_saved','Hours saved (users)','1','hours')]):
    L=G['ladder'][y]; specs=list(L); yy=np.arange(len(specs))[::-1]; m=float(mult)
    ax.axvline(0,color='#d8d6cf',lw=1)
    ax.errorbar([L[s]['coef']*m for s in specs],yy+0.15,xerr=[L[s]['se']*m*Z for s in specs],fmt='o',color=BLUE,ms=5,elinewidth=1,capsize=2,label='Weighted')
    ax.errorbar([L[s]['coef_unw']*m for s in specs],yy-0.15,xerr=[L[s]['se_unw']*m*Z for s in specs],fmt='s',color=ORANGE,ms=4.5,elinewidth=1,capsize=2,label='Unweighted')
    ax.set_yticks(yy); ax.set_yticklabels([short[s] for s in specs] if y=='any_ai' else ['']*len(specs),fontsize=8); ax.set_title(ttl,fontsize=9.5,loc='center'); ax.set_xlabel(f'Male − female ({unit})',fontsize=8); clean(ax)
h,l=axs[0].get_legend_handles_labels(); fig.legend(h,l,frameon=False,fontsize=8,loc='lower center',ncol=2,bbox_to_anchor=(0.55,-0.01)); fig.suptitle('The adoption gap depends on weights and controls; the daily-use gap does not',fontweight='bold',fontsize=10,x=0.01,ha='left')
fig.tight_layout(rect=(0,0.06,1,1)); fig.savefig('charts/g1_ladder.png'); plt.close()

# G2: task dumbbell among users
T=G['tasks']; items=sorted(T,key=lambda k:-abs(T[k]['users']['gap'])); yy=np.arange(len(items))[::-1]
fig,ax=plt.subplots(figsize=(6.5,3.6))
for yi,k in zip(yy,items):
    f,mm=T[k]['users']['female']*100,T[k]['users']['male']*100; ax.plot([f,mm],[yi,yi],color='#d8d6cf',lw=2,zorder=1)
    ax.text(min(f,mm)-1.5,yi,f'{min(f,mm):.0f}',ha='right',va='center',fontsize=8,color=INK2); ax.text(max(f,mm)+1.5,yi,f'{max(f,mm):.0f}',va='center',fontsize=8,color=INK)
ax.scatter([T[k]['users']['female']*100 for k in items],yy,color=ORANGE,s=46,zorder=3,label='Women')
ax.scatter([T[k]['users']['male']*100 for k in items],yy,color=BLUE,s=46,zorder=3,label='Men')
ax.set_yticks(yy); ax.set_yticklabels(items,fontsize=8.5); ax.set_xlim(0,95); ax.set_xlabel('Percent of AI users reporting the task'); clean(ax); ax.legend(frameon=False,loc='lower right',fontsize=8)
ax.set_title('Same writing tasks, but men add search, analysis and code',x=-0.33); fig.tight_layout(); fig.savefig('charts/g2_tasks.png'); plt.close()

# G3: heterogeneity of daily gap
rows=[]
for g,lab in [('occ','Occupation'),('tw','Telework'),('agegrp','Age'),('parent','Children at home'),('edu','Education')]:
    rows.append((lab,None,None))
    for k,r in G['het'][g].items(): rows.append((lab,k,r['ai_daily']))
fig,ax=plt.subplots(figsize=(6.5,6.6)); yy=np.arange(len(rows))[::-1]
ax.axvline(0,color='#d8d6cf',lw=1)
data=[(yi,r) for yi,r in zip(yy,rows) if r[2] is not None]
ax.errorbar([r[2]['gap']*100 for _,r in data],[yi+0.18 for yi,_ in data],xerr=[r[2]['se']*100*Z for _,r in data],fmt='o',color=BLUE,ms=4.5,elinewidth=0.9,capsize=2,label='Weighted (90% CI)')
ax.scatter([r[2]['gap_unw']*100 for _,r in data],[yi-0.18 for yi,_ in data],marker='s',color=ORANGE,s=18,label='Unweighted',zorder=3)
ax.set_yticks(yy); ax.set_yticklabels([r[1] if r[1] else '' for r in rows],fontsize=8)
for yi,r in zip(yy,rows):
    if r[2] is None: ax.text(-34,yi,r[0].upper(),fontsize=7.5,color=INK2,fontweight='bold',va='center')
ax.set_xlim(-35,45); ax.set_xlabel('Male − female gap in daily AI use (percentage points)'); clean(ax); ax.legend(frameon=False,fontsize=8,loc='lower right')
ax.set_title('The daily-use gap is positive in almost every subgroup',x=-0.5); fig.tight_layout(); fig.savefig('charts/g3_het.png'); plt.close()

# G4: weight distribution by respondent: cumulative share
import pandas as pd
w=pd.read_pickle('data/derived/workers2.pkl'); s=np.sort(w.PWEIGHT.values)[::-1]; cs=np.cumsum(s)/s.sum(); x=np.arange(1,len(s)+1)/len(s)*100
fig,ax=plt.subplots(figsize=(6.5,2.6)); ax.plot(x,cs*100,color=BLUE,lw=2); ax.plot([0,100],[0,100],color=GRAY,lw=1,ls='--')
for q in [1,10,25]:
    i=int(len(s)*q/100)-1; ax.scatter([q],[cs[i]*100],color=BLUE,s=28,zorder=3); ax.text(q+1.5,cs[i]*100-6,f'top {q}% of respondents carry {cs[i]*100:.0f}% of the weight',fontsize=8,color=INK)
ax.set_xlabel('Respondents, ranked by weight (percent)'); ax.set_ylabel('Cumulative % of weight'); clean(ax,x=False); ax.set_xlim(0,100); ax.set_ylim(0,100)
ax.set_title('Highly skewed weights: a few respondents stand in for many',x=-0.08); fig.tight_layout(); fig.savefig('charts/g4_weights.png'); plt.close()
print('ok')
