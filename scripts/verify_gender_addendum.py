import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import pandas as pd, numpy as np, statsmodels.api as sm
D='data/raw/'
items=['AIWRK_ADMIN','AIWRK_CODE','AIWRK_CUSTSUPP','AIWRK_DATAVIS','AIWRK_GENIDEA','AIWRK_INTERP','AIWRK_LOG','AIWRK_MED','AIWRK_SEARCH','AIWRK_TUTOR','AIWRK_COMM']
ctrl=['RRACETH','REGION','METRO_STATUS','REDUC','RHHINCOME','AI_OCC','CLASS_WORKER','TWDAYS']
cols=['SCRAMID','PWEIGHT','ANYWORK','AIWRK_FREQ','AIWRK_HOURS','ESEX','TAGE']+ctrl+items
df=pd.read_csv(D+'HTOPS_HPS_2603_PUF.csv',usecols=cols)
rw=pd.read_csv(D+'HTOPS_HPS_2603_REPWGT_PUF.csv',usecols=['SCRAMID']+[f'PWEIGHT{i}' for i in range(1,81)])
df=df.merge(rw,on='SCRAMID',how='left')
RW=[f'PWEIGHT{i}' for i in range(1,81)]
w=df[df.ANYWORK==1].copy()
w['male']=(w.ESEX==1).astype(float)
it=w[items].where(w[items].isin([1,2]))
ans=it.notna().any(axis=1)
w['any_ai']=np.where(ans,(it==1).any(axis=1).astype(float),np.nan)
w['daily']=np.where(w.any_ai==0,0.0,np.where(w.any_ai==1,np.where(w.AIWRK_FREQ==1,1.0,np.where(w.AIWRK_FREQ.isin([2,3]),0.0,np.nan)),np.nan))
w['lastweek']=(w.any_ai==1)&w.AIWRK_FREQ.isin([1,2])
hm={1:0.5,2:1,3:2,4:3,5:4,6:5,7:0,8:-1}
w['hours']=w.AIWRK_HOURS.map(hm)

def wmean(d,y,wt='PWEIGHT'):
    m=d[y].notna(); return np.average(d.loc[m,y],weights=d.loc[m,wt])
def sdr(d,func):
    t=func(d,'PWEIGHT'); reps=np.array([func(d,r) for r in RW])
    return t,np.sqrt(4/80*((reps-t)**2).sum())
def gap(d,y):
    f=lambda dd,wt: wmean(dd[dd.male==1],y,wt)-wmean(dd[dd.male==0],y,wt)
    t,se=sdr(d,f)
    uw=d[d.male==1][y].mean()-d[d.male==0][y].mean()
    return wmean(d[d.male==0],y),wmean(d[d.male==1],y),t,se,uw

print('== 1. raw gaps (women, men, gap, SE, unweighted gap)')
print('any_ai',np.round(gap(w,'any_ai'),4))
print('daily ',np.round(gap(w,'daily'),4))
lw=w[w.lastweek]
print('hours ',np.round(gap(lw,'hours'),4), 'N',len(lw))

print('== 2. composition (men)')
m=w[w.male==1]
print('AI_OCC==2 weighted',np.average(m.AI_OCC==2,weights=m.PWEIGHT),'unw',(m.AI_OCC==2).mean())
print('REDUC==7 weighted',np.average(m.REDUC==7,weights=m.PWEIGHT),'unw',(m.REDUC==7).mean())

print('== 3. regression')
r=w.copy()
for c in ctrl+['TAGE','ESEX']:
    r=r[~r[c].isin([-99,-88])&r[c].notna()]
r['ageg']=pd.cut(r.TAGE,[24,34,44,54,64,200],labels=['25-34','35-44','45-54','55-64','65+'])
r['REDUC']=r.REDUC.replace({1:2})
def X(d):
    x=pd.get_dummies(d[['ageg','RRACETH','REGION','METRO_STATUS','REDUC','RHHINCOME','AI_OCC','CLASS_WORKER','TWDAYS']].astype(str),drop_first=True).astype(float)
    x.insert(0,'male',d.male.values); return sm.add_constant(x)
for y in ['daily','any_ai']:
    d=r[r[y].notna()]; x=X(d)
    f=lambda dd,wt: sm.WLS(dd[y],x.loc[dd.index],weights=dd[wt]).fit().params['male']
    t,se=sdr(d,f)
    uw=sm.OLS(d[y],x).fit(cov_type='HC1')
    print(y,'N',len(d),'WLS male',round(t,4),'SDR SE',round(se,4),'| OLS',round(uw.params['male'],4),'HC1 SE',round(uw.bse['male'],4))

print('== 4. task shares among users')
u=w[w.any_ai==1]
for c in ['AIWRK_CODE','AIWRK_SEARCH','AIWRK_COMM']:
    out=[]
    for s in [0,1]:
        d=u[(u.male==s)&u[c].isin([1,2])]
        out.append(round(100*np.average(d[c]==1,weights=d.PWEIGHT),1))
    print(c,'women',out[0],'men',out[1])

print('== 5. daily within AI_OCC==1')
c1=w[w.AI_OCC==1]
print(np.round(gap(c1,'daily'),4))

print('== 6. weight diagnostics (workers)')
pw=w.PWEIGHT.sort_values(ascending=False); tot=pw.sum()
n=len(pw)
print('top1%',pw.iloc[:int(np.ceil(0.01*n))].sum()/tot,'top10%',pw.iloc[:int(np.ceil(0.10*n))].sum()/tot)
for s,l in [(1,'men'),(0,'women')]:
    p=w[w.male==s].PWEIGHT; print(l,'CV',p.std()/p.mean(), 'CV(ddof0)',p.std(ddof=0)/p.mean())
print('max',pw.max(),'median',pw.median(),'N workers',n)
