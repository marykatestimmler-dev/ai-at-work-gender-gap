import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import json, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=json.load(open('data/derived/results.json'))
BLUE='#2a78d6'; ORANGE='#eb6834'; AQUA='#1baf7a'; GRAY='#9a9891'; INK='#0b0b0b'; INK2='#52514e'; SURF='#fcfcfb'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.edgecolor':'#d8d6cf','axes.linewidth':0.6,'axes.titleweight':'bold',
 'axes.titlesize':10.5,'axes.titlelocation':'left','axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2,'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.dpi':200})
def clean(ax, x=True):
    for s in ['top','right']: ax.spines[s].set_visible(False)
    ax.grid(axis='x' if x else 'y', color='#e6e4dd', lw=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
Z=1.645  # 90% CI (Census convention)

# 1. Funnel
fig,ax=plt.subplots(figsize=(6.5,2.4))
labs=['Used AI for any work task (no time limit)','Used AI at work last week','Used AI at work every day last week']
vals=[R['any_ai']['est'],R['ai_lastweek']['est'],R['ai_daily']['est']]; ses=[R['any_ai']['se'],R['ai_lastweek']['se'],R['ai_daily']['se']]
y=np.arange(3)[::-1]; ax.barh(y,[v*100 for v in vals],color=BLUE,height=0.55)
ax.errorbar([v*100 for v in vals],y,xerr=[s*100*Z for s in ses],fmt='none',ecolor=INK,elinewidth=0.8,capsize=2)
for yi,v in zip(y,vals): ax.text(v*100+2.5,yi,f'{v*100:.1f}%',va='center',color=INK,fontsize=9.5)
ax.set_yticks(y); ax.set_yticklabels(labs); ax.set_xlim(0,70); ax.set_xlabel('Percent of employed adults (weighted; bars show 90% CI)'); clean(ax)
ax.set_title('Adoption narrows sharply from "ever" to "daily"',x=-0.62); fig.tight_layout(); fig.savefig('charts/fig1_funnel.png'); plt.close()

# 2. Task mix, all workers vs users
ta=R['task_all']; tu=R['task_users']
items=sorted(ta, key=lambda k: ta[k]['est'])
fig,ax=plt.subplots(figsize=(6.5,4.2)); y=np.arange(len(items))
ax.barh(y+0.2,[tu[k]['est']*100 for k in items],height=0.38,color='#a9c9ee',label='Among AI users')
ax.barh(y-0.2,[ta[k]['est']*100 for k in items],height=0.38,color=BLUE,label='Among all workers')
for yi,k in zip(y,items):
    ax.text(ta[k]['est']*100+1,yi-0.2,f"{ta[k]['est']*100:.0f}",va='center',fontsize=8,color=INK)
    ax.text(tu[k]['est']*100+1,yi+0.2,f"{tu[k]['est']*100:.0f}",va='center',fontsize=8,color=INK2)
ax.set_yticks(y); ax.set_yticklabels([k.replace(' / ','/') for k in items],fontsize=8.5); ax.set_xlim(0,82); ax.set_xlabel('Percent'); clean(ax)
ax.legend(frameon=False,loc='lower right'); ax.set_title('Information, writing and summarizing dominate',x=-0.55)
fig.tight_layout(); fig.savefig('charts/fig2_tasks.png'); plt.close()

# 3. Occupation: ever / last week / daily (dot plot)
b=pd.DataFrame(R['breakdowns']['occ']['any_ai']).set_index('occ'); lw=pd.DataFrame(R['breakdowns']['occ']['ai_lastweek']).set_index('occ'); dl=pd.DataFrame(R['breakdowns']['occ']['ai_daily']).set_index('occ')
b=b.drop('Farming/fishing/forestry'); occs=b.sort_values('est').index
fig,ax=plt.subplots(figsize=(6.5,4)); y=np.arange(len(occs))
for yi,o in zip(y,occs):
    ax.plot([dl.loc[o,'est']*100,b.loc[o,'est']*100],[yi,yi],color='#d8d6cf',lw=1.5,zorder=1)
ax.scatter(b.loc[occs,'est']*100,y,color=BLUE,s=42,zorder=3,label='Ever used for a work task')
ax.scatter(lw.loc[occs,'est']*100,y,color=ORANGE,s=42,zorder=3,label='Used last week')
ax.scatter(dl.loc[occs,'est']*100,y,color=AQUA,s=42,zorder=3,label='Used every day last week',edgecolor=INK2,linewidth=0.4)
for yi,o in zip(y,occs): ax.text(b.loc[o,'est']*100+2,yi,f"{b.loc[o,'est']*100:.0f}",va='center',fontsize=8,color=INK)
ax.set_yticks(y); ax.set_yticklabels(occs,fontsize=8.5); ax.set_xlim(0,100); ax.set_xlabel('Percent of workers in occupation group'); clean(ax)
ax.legend(frameon=False,loc='lower right',fontsize=8); ax.set_title('Occupation is the strongest single predictor',x=-0.5); fig.tight_layout(); fig.savefig('charts/fig3_occ.png'); plt.close()

# 4. Telework x occupation dumbbell
t=R['ai_by_tw_occ']; occs=[o for o in b.sort_values('est').index]
fig,ax=plt.subplots(figsize=(6.5,4)); y=np.arange(len(occs))
for yi,o in zip(y,occs):
    a,c=t['0.0'][o]*100,t['1.0'][o]*100
    ax.plot([a,c],[yi,yi],color='#d8d6cf',lw=2,zorder=1)
    if abs(a-c)<6:
        ax.text(a,yi+0.34,f'{a:.0f}',ha='center',va='center',fontsize=8,color=INK2); ax.text(c,yi-0.36,f'{c:.0f}',ha='center',va='center',fontsize=8,color=INK)
    else:
        ax.text(a-2,yi,f'{a:.0f}',ha='right',va='center',fontsize=8,color=INK2); ax.text(c+2,yi,f'{c:.0f}',va='center',fontsize=8,color=INK)
ax.scatter([t['0.0'][o]*100 for o in occs],y,color=GRAY,s=46,zorder=3,label='No telework last week')
ax.scatter([t['1.0'][o]*100 for o in occs],y,color=BLUE,s=46,zorder=3,label='Teleworked at least 1 day')
ax.set_yticks(y); ax.set_yticklabels(occs,fontsize=8.5); ax.set_xlim(0,100); ax.set_xlabel('Percent who have used AI for a work task'); clean(ax)
ax.legend(frameon=False,loc='upper left',fontsize=8,bbox_to_anchor=(0,1.0)); ax.set_title('Among teleworkers, every occupation is majority-AI',x=-0.5); fig.tight_layout(); fig.savefig('charts/fig4_telework.png'); plt.close()

# 5. Hours distribution
hd=R['hours_dist']; labs=['<1 hour','1 hour','2 hours','3 hours','4 hours','>4 hours','No time saved','Needed MORE time']
fig,ax=plt.subplots(figsize=(6.5,2.8)); x=np.arange(8)
cols=[BLUE]*6+[GRAY,ORANGE]
ax.bar(x,[hd[str(k)]['est']*100 for k in range(1,9)],color=cols,width=0.62)
for xi,k in zip(x,range(1,9)): ax.text(xi,hd[str(k)]['est']*100+0.8,f"{hd[str(k)]['est']*100:.0f}%",ha='center',fontsize=8.5,color=INK)
ax.set_xticks(x); ax.set_xticklabels(labs,fontsize=8,rotation=20,ha='right'); ax.set_ylim(0,32); ax.set_ylabel('Percent of last-week users'); clean(ax,x=False)
ax.set_title('Hours that would have been needed without AI last week',x=-0.06); fig.tight_layout(); fig.savefig('charts/fig5_hours.png'); plt.close()

# 6. Gender: adoption same, intensity differs
sx=R['breakdowns']['sex']
fig,axs=plt.subplots(1,3,figsize=(6.5,2.6))
for ax,(key,ttl,fmt,lim) in zip(axs,[('any_ai','Ever used AI at work','{:.0f}%',100),('ai_daily','Used every day last week','{:.0f}%',32),('hrs_saved','Hours saved, last-week users','{:.1f}h',3.4)]):
    df=pd.DataFrame(sx[key]).set_index('sex'); v=df.loc[['Female','Male'],'est']*(100 if '%' in fmt else 1); s=df.loc[['Female','Male'],'se']*(100 if '%' in fmt else 1)
    ax.bar([0,1],v,color=[ORANGE,BLUE],width=0.55); ax.errorbar([0,1],v,yerr=s*Z,fmt='none',ecolor=INK,elinewidth=0.8,capsize=2)
    for i,(val,se_) in enumerate(zip(v,s)): ax.text(i,val+se_*Z+lim*0.03,fmt.format(val),ha='center',fontsize=9,color=INK)
    ax.set_xticks([0,1]); ax.set_xticklabels(['Women','Men']); ax.set_ylim(0,lim); ax.set_title(ttl,fontsize=8.5,loc='center'); clean(ax,x=False)
fig.suptitle('Same adoption, different intensity: the gender gap is in depth of use',fontweight='bold',fontsize=10.5,x=0.02,ha='left'); fig.tight_layout(); fig.savefig('charts/fig6_gender.png'); plt.close()

# 7. Education x telework
te=R['ai_by_tw_edu']; ed=['< HS','HS grad','Some college',"Associate's","Bachelor's",'Graduate']
fig,ax=plt.subplots(figsize=(6.5,2.8)); x=np.arange(6)
ax.plot(x,[te['0.0'][e]*100 for e in ed],color=GRAY,marker='o',lw=2,label='No telework')
ax.plot(x,[te['1.0'][e]*100 for e in ed],color=BLUE,marker='o',lw=2,label='Teleworked ≥1 day')
for i,e in enumerate(ed):
    ax.text(i,te['1.0'][e]*100+4,f"{te['1.0'][e]*100:.0f}",ha='center',fontsize=8,color=INK); ax.text(i,te['0.0'][e]*100-8,f"{te['0.0'][e]*100:.0f}",ha='center',fontsize=8,color=INK2)
ax.set_xticks(x); ax.set_xticklabels(ed); ax.set_ylim(0,100); ax.set_ylabel('% ever used AI at work'); clean(ax,x=False); ax.legend(frameon=False,fontsize=8,loc='lower right')
ax.set_title('Education gradient: steep on-site, nearly flat among teleworkers',x=-0.08); fig.tight_layout(); fig.savefig('charts/fig7_edu_tw.png'); plt.close()
print('ok')
