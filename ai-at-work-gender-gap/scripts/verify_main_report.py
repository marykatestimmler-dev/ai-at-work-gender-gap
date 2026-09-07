import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import pandas as pd, numpy as np
D='data/raw/'
items=['AIWRK_ADMIN','AIWRK_CODE','AIWRK_CUSTSUPP','AIWRK_DATAVIS','AIWRK_GENIDEA','AIWRK_INTERP','AIWRK_LOG','AIWRK_MED','AIWRK_SEARCH','AIWRK_TUTOR','AIWRK_COMM']
cols=['SCRAMID','PWEIGHT','ANYWORK','AIWRK_FREQ','AIWRK_HOURS','AI_OCC','ESEX','TWDAYS','TAGE','REGION','REDUC']+items
df=pd.read_csv(D+'HTOPS_HPS_2603_PUF.csv',usecols=cols)
rw=pd.read_csv(D+'HTOPS_HPS_2603_REPWGT_PUF.csv')
print('total N',len(df))
df=df.merge(rw,on='SCRAMID',how='left')
w=df[df.ANYWORK==1].copy()
print('workers',len(w))
M=w[items].values
anyyes=(M==1).any(1); anyans=((M==1)|(M==2)).any(1)
w['any_ai']=np.where(anyyes,1.0,np.where(anyans,0.0,np.nan))
w['lastweek']=np.where(w.any_ai==1,w.AIWRK_FREQ.isin([1,2]).astype(float),np.where(w.any_ai==0,0.0,np.nan))
w['daily']=np.where(w.any_ai==1,(w.AIWRK_FREQ==1).astype(float),np.where(w.any_ai==0,0.0,np.nan))
hmap={1:0.5,2:1,3:2,4:3,5:4,6:5,7:0,8:-1}
w['hrs']=np.where(w.AIWRK_FREQ.isin([1,2]),w.AIWRK_HOURS.map(hmap),np.nan)
w['hrs_pos']=w.hrs.where(w.hrs>=0)   # exclude 'additional' (-1) from mean? compute both
RW=[f'PWEIGHT{i}' for i in range(1,81)]
def est(sub,col,pct=True):
    m=sub[col].notna(); s=sub[m]
    def f(wt): return np.average(s[col],weights=s[wt])
    t=f('PWEIGHT'); reps=np.array([f(r) for r in RW])
    se=np.sqrt(4/80*((reps-t)**2).sum())
    k=100 if pct else 1
    return round(t*k,2),round(se*k,2),round(s[col].mean()*k,2),m.sum()
print('any_ai',est(w,'any_ai'))
print('lastweek',est(w,'lastweek'))
print('daily',est(w,'daily'))
u=w[w.any_ai==1]
print('users answering FREQ',u.AIWRK_FREQ.isin([1,2,3]).sum(), 'users',len(u))
uf=u[u.AIWRK_FREQ.isin([1,2,3])]
for k in [1,2,3]:
    uf['f']=(uf.AIWRK_FREQ==k).astype(float); print('freq',k,est(uf,'f'))
for it in items:
    w['t']=np.where(w[it]==1,1.0,np.where(w[it]==2,0.0,np.nan)); print(it,est(w,'t'))
lw=w[w.hrs.notna()]
print('lastweek users w hours',len(lw), 'lastweek users total',(w.lastweek==1).sum())
for code,lab in hmap.items():
    lw['h']=(lw.AIWRK_HOURS==code).astype(float); print('hours',code,lab,est(lw,'h'))
print('mean hrs (excl additional)',est(lw,'hrs_pos',False))
print('mean hrs (additional as 0)',est(lw.assign(hrs0=lw.hrs.clip(lower=0)),'hrs0',False))
print('mean hrs (additional as -1)',est(lw,'hrs',False))
for k in [1,2]:
    print('mean hrs freq',k,est(lw[lw.AIWRK_FREQ==k],'hrs_pos',False))
for o in [1,2,6,7,10]: print('occ',o,est(w[w.AI_OCC==o],'any_ai'))
for s in [1,2]:
    print('sex',s,'any',est(w[w.ESEX==s],'any_ai'),'daily',est(w[w.ESEX==s],'daily'),'hrs',est(lw[lw.ESEX==s],'hrs_pos',False))
print('TW4',est(w[w.TWDAYS==4],'any_ai'),'TW1-3',est(w[w.TWDAYS.isin([1,2,3])],'any_ai'))
c=w[w.AI_OCC==2]; print('constr tw',est(c[c.TWDAYS.isin([1,2,3])],'any_ai'),'constr no tw',est(c[c.TWDAYS==4],'any_ai'))
for lo,hi in [(25,34),(35,44),(45,54),(55,64),(65,200)]: print('age',lo,hi,est(w[(w.TAGE>=lo)&(w.TAGE<=hi)],'any_ai'))
for r in [1,2,3,4]: print('region',r,est(w[w.REGION==r],'any_ai'))
w['grad']=(w.REDUC==7).astype(float); print('grad',est(w,'grad'))
print(w.REDUC.value_counts().sort_index())
