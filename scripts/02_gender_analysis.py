import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
import statsmodels.api as sm
w = pd.read_pickle('data/derived/workers.pkl')
RW=[f'PWEIGHT{i}' for i in range(1,81)]
w['male']=(w.ESEX==1).astype(float)
w['UNW']=1.0
# extra controls
w['ms']=w.MS.map({1:'Married',2:'Widowed',3:'Divorced',4:'Separated',5:'Never married'})
w['ms']=w.ms.replace({'Widowed':'Div/Wid/Sep','Divorced':'Div/Wid/Sep','Separated':'Div/Wid/Sep'})
for k,v in [('kid_u5',['KIDS_LT1Y','KIDS_1_4Y']),('kid_5_11',['KIDS_5_11Y']),('kid_12_17',['KIDS_12_17Y'])]:
    w[k]=np.where(w.THHLD_NUMKID==0,0,np.where(w[v].eq(1).any(axis=1),1,np.where(w[v].eq(2).all(axis=1),0,np.nan)))
w['anykid']=np.where(w.THHLD_NUMKID.notna(),(w.THHLD_NUMKID>0).astype(float),np.nan)
w['hhsize']=w.THHLD_NUMPER.clip(upper=5).astype(str)
w['ins']=np.where(w.HLTHINS_EMP==1,'Employer',np.where(w.HLTHINS_NO==1,'Uninsured',np.where(w[['HLTHINS_MEDICARE','HLTHINS_MEDICAID','HLTHINS_PURCH','HLTHINS_VA','HLTHINS_TRICARE','HLTHINS_IHS','HLTHINS_OTH']].eq(1).any(axis=1),'Other','Missing')))
dis=['SEEING','HEARING','MOBILITY','REMEMBERING','SELFCARE','UNDERSTAND']
w['disab']=np.where(w[dis].isin([1,2,3,4]).all(axis=1),(w[dis]>=3).any(axis=1).astype(float),np.nan)
w['cogdiff']=np.where(w.REMEMBERING.isin([1,2,3,4]),(w.REMEMBERING>=2).astype(float),np.nan)
w['lang']=np.where(w.LANG_OTHER_HOME.isin([1,2]),w.LANG_OTHER_HOME.map({1:'Other lang',2:'English'}),np.nan)
w['tw_s']=w.tw
w['parent_u5']=w.kid_u5
# outcomes
u=w[w.any_ai==1].copy(); lw=w[w.ai_lastweek==1].copy()
u['lapsed']=(u.freq==3).astype(float).where(u.freq.notna())
u['daily_u']=(u.freq==1).astype(float).where(u.freq.notna())
tk=[c for c in w.columns if c.startswith('AIWRK_') and c.endswith('_y')]
TASKS={'AIWRK_SEARCH_y':'Search/technical help','AIWRK_COMM_y':'Writing communications','AIWRK_INTERP_y':'Interpreting/summarizing','AIWRK_GENIDEA_y':'Generating ideas','AIWRK_ADMIN_y':'Administrative','AIWRK_DATAVIS_y':'Data analysis/viz','AIWRK_TUTOR_y':'Tutoring/training','AIWRK_CODE_y':'Coding/modeling','AIWRK_CUSTSUPP_y':'Customer support','AIWRK_MED_y':'Medical care','AIWRK_LOG_y':'Logistics'}

def sdr(fn):
    th=fn('PWEIGHT'); reps=np.array([fn(r) for r in RW]); return th, np.sqrt(4/80*np.sum((reps-th)**2,axis=0))
def gap(df,y):
    m=df[y].notna(); s=df[m]
    f=lambda wt: np.average(s.loc[s.male==1,y],weights=s.loc[s.male==1,wt])-np.average(s.loc[s.male==0,y],weights=s.loc[s.male==0,wt])
    th,se=sdr(f)
    fu=s[s.male==1][y]; ff=s[s.male==0][y]
    unw=fu.mean()-ff.mean(); seu=np.sqrt(fu.var(ddof=1)/len(fu)+ff.var(ddof=1)/len(ff))
    return dict(female=np.average(s.loc[s.male==0,y],weights=s.loc[s.male==0,'PWEIGHT']),male=np.average(s.loc[s.male==1,y],weights=s.loc[s.male==1,'PWEIGHT']),
                gap=th,se=se,female_unw=ff.mean(),male_unw=fu.mean(),gap_unw=unw,se_unw=seu,n_f=int(len(ff)),n_m=int(len(fu)))

SPECS={'0 Raw':[], '1 + age, race, region, metro':['agegrp','race','region','metro'],
 '2 + education, income':['agegrp','race','region','metro','edu','inc'],
 '3 + occupation, sector, telework':['agegrp','race','region','metro','edu','inc','occ','cls','tw'],
 '4 + family: marital, kids by age, hh size':['agegrp','race','region','metro','edu','inc','occ','cls','tw','ms','kid_u5','kid_5_11','kid_12_17','hhsize'],
 '5 + health, language, insurance, wellbeing (kitchen sink)':['agegrp','race','region','metro','edu','inc','occ','cls','tw','ms','kid_u5','kid_5_11','kid_12_17','hhsize','ins','disab','cogdiff','lang','phq4','lifesat']}
def reg_gap(df,y,X,extra=None):
    cols=['male']+X+(extra or [])
    m=df[[y]+cols].notna().all(axis=1); s=df[m]
    cat=[c for c in cols if not pd.api.types.is_numeric_dtype(s[c])]; num=[c for c in cols if c not in cat]
    Xm=pd.concat([s[num].astype(float), pd.get_dummies(s[cat],drop_first=True,dtype=float)],axis=1) if cat else s[num].astype(float)
    Xm=sm.add_constant(Xm)
    f=lambda wt: sm.WLS(s[y],Xm,weights=s[wt]).fit().params['male']
    th,se=sdr(f)
    ru=sm.OLS(s[y],Xm).fit(cov_type='HC1')
    return dict(coef=th,se=se,coef_unw=ru.params['male'],se_unw=ru.bse['male'],n=int(len(s)))
OUT={}
outcomes=[('any_ai','Any AI use at work',w),('ai_lastweek','Used AI at work last week',w),('ai_daily','Used AI every day last week',w),
 ('ntasks','Number of task types (users)',u),('lapsed','Used before, not last week (users)',u),('daily_u','Daily use (users)',u),
 ('hrs_saved','Hours saved last week (last-week users)',lw),('no_saving','No time saved / cost time (last-week users)',lw),('big_saving','Saved 4+ hours (last-week users)',lw)]
OUT['raw']={y:gap(df,y) for y,_,df in outcomes}
OUT['ladder']={y:{s:reg_gap(df,y,X,(['freq'] if y in('hrs_saved','no_saving','big_saving') and s!='0 Raw' else None)) for s,X in SPECS.items()} for y,_,df in outcomes}
OUT['labels']={y:l for y,l,_ in outcomes}
# tasks by sex among users and among all; conditional gap (spec 3)
OUT['tasks']={TASKS[t]:{'users':gap(u,t),'all':gap(w,t),'cond_users':reg_gap(u,t,SPECS['3 + occupation, sector, telework'])} for t in tk}
# heterogeneity: gap in any_ai, daily, hrs by group (n>=100 per sex cell)
w['parent']=np.where(w.kid_u5==1,'Child under 5',np.where(w.kid_5_11==1,'Youngest 5-11',np.where(w.kid_12_17==1,'Youngest 12-17',np.where(w.anykid==0,'No children <18',None))))
w['agegrp2']=w.agegrp
HET={}
for g in ['occ','tw','agegrp','parent','edu','inc','race','cls','region','ms']:
    HET[g]={}
    for k,s in w.groupby(g):
        if (s.male==1).sum()<100 or (s.male==0).sum()<100: continue
        HET[g][k]={'any_ai':gap(s,'any_ai'),'ai_daily':gap(s,'ai_daily'),'hrs':gap(s[s.ai_lastweek==1],'hrs_saved') if ((s.ai_lastweek==1)&(s.male==1)).sum()>=50 and ((s.ai_lastweek==1)&(s.male==0)).sum()>=50 else None}
OUT['het']=HET
# interaction tests: male x telework, male x parent_u5, male x occ(computer) in daily model spec 3
def inter(df,y,var,X):
    d=df.copy(); d['int']=d.male*d[var]
    X=[c for c in X if not (var=='tele' and c=='tw')]
    main=[] if var in ('comp','mgmt') else [var]
    cols=['male']+main+['int']+X; m=d[[y]+cols].notna().all(axis=1); s=d[m]
    cat=[c for c in X if not pd.api.types.is_numeric_dtype(s[c])]; num=[c for c in cols if c not in cat]
    Xm=sm.add_constant(pd.concat([s[num].astype(float),pd.get_dummies(s[cat],drop_first=True,dtype=float)],axis=1))
    f=lambda wt: sm.WLS(s[y],Xm,weights=s[wt]).fit().params['int']; th,se=sdr(f); ru=sm.OLS(s[y],Xm).fit(cov_type='HC1')
    return dict(coef=th,se=se,coef_unw=ru.params['int'],se_unw=ru.bse['int'],n=int(len(s)))
w['tele']=w.telework_any; w['comp']=(w.occ=='Computer').astype(float).where(w.occ.notna()); w['mgmt']=(w.occ=='Management/business/finance/legal').astype(float).where(w.occ.notna())
w['young']=(w.TAGE<45).astype(float); w['married']=(w.ms=='Married').astype(float).where(w.ms.notna())
INT={}
for y,df in [('ai_daily',w),('any_ai',w)]:
    INT[y]={v:inter(df,y,v,['agegrp','race','region','metro','edu','inc','occ','cls','tw']) for v in ['tele','kid_u5','anykid','comp','mgmt','young','married']}
lw['tele']=lw.telework_any; lw['kid_u5']=w.loc[lw.index,'kid_u5']; lw['anykid']=w.loc[lw.index,'anykid']; lw['comp']=w.loc[lw.index,'comp']; lw['mgmt']=w.loc[lw.index,'mgmt']; lw['young']=w.loc[lw.index,'young']; lw['married']=w.loc[lw.index,'married']
for c in ['ms','kid_5_11','kid_12_17','hhsize']: lw[c]=w.loc[lw.index,c]
INT['hrs_saved']={v:inter(lw,'hrs_saved',v,['agegrp','race','region','metro','edu','inc','occ','cls','tw','freq']) for v in ['tele','kid_u5','anykid','comp','mgmt','young','married']}
OUT['inter']=INT
# Kitagawa-Oaxaca-Blinder, pooled (Neumark) coefficients, weighted and unweighted, for ai_daily (workers) and hrs_saved (lw)
def kob(df,y,X,wt):
    m=df[[y,'male']+X].notna().all(axis=1); s=df[m]
    cat=[c for c in X if not pd.api.types.is_numeric_dtype(s[c])]; num=[c for c in X if c not in cat]
    Xm=sm.add_constant(pd.concat([s[num].astype(float),pd.get_dummies(s[cat],drop_first=True,dtype=float)],axis=1))
    ww=s[wt] if wt else pd.Series(1.0,index=s.index)
    bp=sm.WLS(s[y],Xm,weights=ww).fit().params  # pooled (without male dummy)
    Xm2=Xm.assign(male=s.male); bp2=sm.WLS(s[y],Xm2,weights=ww).fit().params; bp=bp2.drop('male')
    M=s.male==1; F=s.male==0
    xbar_m=np.average(Xm[M],weights=ww[M],axis=0); xbar_f=np.average(Xm[F],weights=ww[F],axis=0)
    ybar_m=np.average(s[y][M],weights=ww[M]); ybar_f=np.average(s[y][F],weights=ww[F])
    contrib=pd.Series((xbar_m-xbar_f)*bp.values,index=Xm.columns)
    explained=contrib.sum(); total=ybar_m-ybar_f
    # group contributions
    grp={}
    for c,v in contrib.items():
        if c=='const': continue
        g=c.split('_')[0] if c in num else next((cc for cc in cat if c.startswith(cc+'_')),c)
        grp[g]=grp.get(g,0)+v
    return dict(total=total,explained=explained,unexplained=total-explained,groups=grp,n=int(len(s)))
X3=SPECS['3 + occupation, sector, telework']; X5=SPECS['5 + health, language, insurance, wellbeing (kitchen sink)']
KOB={}
for y,df in [('ai_daily',w),('any_ai',w),('hrs_saved',lw),('ntasks',u)]:
    for c in X5:
        if c not in df.columns: df[c]=w.loc[df.index,c]
    KOB[y]={'spec3_w':kob(df,y,X3+(['freq'] if y=='hrs_saved' else []),'PWEIGHT'),'spec3_unw':kob(df,y,X3+(['freq'] if y=='hrs_saved' else []),None),
            'spec5_w':kob(df,y,X5+(['freq'] if y=='hrs_saved' else []),'PWEIGHT'),'spec5_unw':kob(df,y,X5+(['freq'] if y=='hrs_saved' else []),None)}
OUT['kob']=KOB
# composition: how men and women differ on covariates (weighted, unweighted)
COMP={}
for c in ['occ','edu','inc','tw','cls','agegrp','parent','ms','race']:
    t=w.groupby([c,'male']).PWEIGHT.sum().unstack(); t=t/t.sum(); tu=pd.crosstab(w[c],w.male,normalize='columns')
    COMP[c]={k:{'f_w':t.loc[k,0.0],'m_w':t.loc[k,1.0],'f_unw':tu.loc[k,0.0],'m_unw':tu.loc[k,1.0]} for k in t.index}
OUT['comp']=COMP
# weight diagnostics by sex
OUT['wdiag']={'share_male_w':np.average(w.male,weights=w.PWEIGHT),'share_male_unw':w.male.mean(),
  'mean_w_m':w[w.male==1].PWEIGHT.mean(),'mean_w_f':w[w.male==0].PWEIGHT.mean(),'cv_w_m':w[w.male==1].PWEIGHT.std()/w[w.male==1].PWEIGHT.mean(),'cv_w_f':w[w.male==0].PWEIGHT.std()/w[w.male==0].PWEIGHT.mean(),
  'deff_m':1+(w[w.male==1].PWEIGHT.std()/w[w.male==1].PWEIGHT.mean())**2,'deff_f':1+(w[w.male==0].PWEIGHT.std()/w[w.male==0].PWEIGHT.mean())**2}
# replicate-weight range of daily gap (how much do 80 alternative weightings move it)
s=w[w.ai_daily.notna()]
reps=[np.average(s.loc[s.male==1,'ai_daily'],weights=s.loc[s.male==1,r])-np.average(s.loc[s.male==0,'ai_daily'],weights=s.loc[s.male==0,r]) for r in RW]
OUT['wdiag']['daily_gap_rep_min']=min(reps); OUT['wdiag']['daily_gap_rep_max']=max(reps)
# trimmed weights sensitivity
for q in [0.99,0.95]:
    cap=w.PWEIGHT.quantile(q); wt=w.PWEIGHT.clip(upper=cap)
    wts=wt.loc[s.index]
    OUT['wdiag'][f'daily_gap_trim{int(q*100)}']=np.average(s.loc[s.male==1,'ai_daily'],weights=wts[s.male==1])-np.average(s.loc[s.male==0,'ai_daily'],weights=wts[s.male==0])

# task shares by sex within occupation groups (users), weighted and unweighted
TWO={}
for occ,so in u.groupby('occ'):
    if (so.male==1).sum()<50 or (so.male==0).sum()<50: continue
    TWO[occ]={}
    for t in ['AIWRK_CODE_y','AIWRK_DATAVIS_y','AIWRK_SEARCH_y','AIWRK_TUTOR_y','AIWRK_COMM_y','AIWRK_GENIDEA_y']:
        TWO[occ][TASKS[t]]=gap(so,t)
OUT['tasks_within_occ']=TWO
json.dump(OUT,open('data/derived/gender.json','w'),default=lambda o:o.item() if hasattr(o,'item') else str(o),indent=1)
w.to_pickle('data/derived/workers2.pkl')
print(json.dumps(OUT['raw'],default=float,indent=0)[:1500])
