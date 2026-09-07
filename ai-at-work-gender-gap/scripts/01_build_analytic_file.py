import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import pandas as pd, numpy as np, json, warnings
warnings.filterwarnings('ignore')
import statsmodels.api as sm

D = 'data/raw/'
d = pd.read_csv(D+'HTOPS_HPS_2603_PUF.csv', low_memory=False)
r = pd.read_csv(D+'HTOPS_HPS_2603_REPWGT_PUF.csv')
d = d.merge(r[['SCRAMID']+[f'PWEIGHT{i}' for i in range(1,81)]], on='SCRAMID')
RW = [f'PWEIGHT{i}' for i in range(1,81)]

TASKS = {'AIWRK_SEARCH':'Searching for information / technical help','AIWRK_COMM':'Writing communications, documentation, instructions',
 'AIWRK_INTERP':'Interpreting, translating, summarizing','AIWRK_GENIDEA':'Generating ideas','AIWRK_ADMIN':'Administrative tasks',
 'AIWRK_DATAVIS':'Data analysis & visualization','AIWRK_TUTOR':'Tutoring, training, educational assistance','AIWRK_CODE':'Coding or modeling',
 'AIWRK_CUSTSUPP':'Customer support','AIWRK_MED':'Medical care','AIWRK_LOG':'Managing logistics / supply chains'}
OCC = {1:'Computer',2:'Construction/production/transport',3:'Education/social svc/arts/media',4:'Engineering/architecture/sciences',
 5:'Farming/fishing/forestry',6:'Healthcare',7:'Management/business/finance/legal',8:'Office & admin support',9:'Sales',10:'Service (security/food/cleaning/care)'}
EDU = {1:'< HS',2:'< HS',3:'HS grad',4:'Some college',5:"Associate's",6:"Bachelor's",7:'Graduate'}
INC = {1:'<$25k',2:'$25-35k',3:'$35-50k',4:'$50-75k',5:'$75-100k',6:'$100-150k',7:'$150k+'}
RACE = {1:'White',2:'Hispanic',3:'Black',4:'Asian',5:'Other/multiracial'}
CLS = {1:'Government',2:'Private',3:'Nonprofit',4:'Self-employed',5:'Family business'}
TW = {1:'Telework 1-2 days',2:'Telework 3-4 days',3:'Telework 5+ days',4:'No telework'}
REG = {1:'Northeast',2:'Midwest',3:'South',4:'West'}

# ---- analytic sample: worked for pay last 7 days
w = d[d.ANYWORK==1].copy()
tk = list(TASKS)
for t in tk: w[t+'_y'] = np.where(w[t]==1,1,np.where(w[t]==2,0,np.nan))
w['n_answered'] = w[[t+'_y' for t in tk]].notna().sum(axis=1)
w['ntasks'] = w[[t+'_y' for t in tk]].sum(axis=1, min_count=1)
w['any_ai'] = np.where(w.n_answered==0, np.nan, (w.ntasks>0).astype(float))
# frequency: universe = any_ai==1
w['freq'] = np.where(w.AIWRK_FREQ.isin([1,2,3]), w.AIWRK_FREQ, np.nan)
w['ai_lastweek'] = np.where(w.any_ai==0, 0, np.where(w.freq.isin([1,2]),1, np.where(w.freq==3,0,np.nan)))
w['ai_daily'] = np.where(w.any_ai==0, 0, np.where(w.freq==1,1, np.where(w.freq.isin([2,3]),0,np.nan)))
HRS_MID = {1:0.5,2:1,3:2,4:3,5:4,6:5,7:0,8:-1}  # 'more than 4' -> 5 (conservative); 'required additional time' -> -1
w['hours'] = np.where(w.AIWRK_HOURS.isin(range(1,9)), w.AIWRK_HOURS, np.nan)
w['hrs_saved'] = w.hours.map(HRS_MID)
w['no_saving'] = np.where(w.hours.notna(), (w.hours>=7).astype(float), np.nan)
w['big_saving'] = np.where(w.hours.notna(), (w.hours.isin([5,6])).astype(float), np.nan)  # >=4 hours
# covariates
w['occ'] = w.AI_OCC.map(OCC); w['edu'] = w.REDUC.map(EDU); w['inc'] = w.RHHINCOME.map(INC); w['race']=w.RRACETH.map(RACE)
w['sex'] = w.ESEX.map({1:'Male',2:'Female'}); w['cls']=w.CLASS_WORKER.map(CLS); w['tw']=w.TWDAYS.map(TW); w['region']=w.REGION.map(REG)
w['agegrp'] = pd.cut(w.TAGE,[0,34,44,54,64,120],labels=['25-34*','35-44','45-54','55-64','65+']).astype(str)
w['telework_any'] = np.where(w.TWDAYS.isin([1,2,3]),1,np.where(w.TWDAYS==4,0,np.nan))
w['metro'] = w.METRO_STATUS.map({1:'Metro',2:'Non-metro'})
# mental health PHQ-4 (0-3 each), lonely, support, satisfaction
for v in ['ANXIOUS','WORRY','INTEREST','DOWN']: w[v.lower()] = np.where(w[v].isin([1,2,3,4]), w[v]-1, np.nan)
w['phq4'] = w[['anxious','worry','interest','down']].sum(axis=1, min_count=4)
w['gad2'] = w[['anxious','worry']].sum(axis=1,min_count=2); w['phq2']=w[['interest','down']].sum(axis=1,min_count=2)
w['anx_sympt'] = np.where(w.gad2.notna(), (w.gad2>=3).astype(float), np.nan)
w['dep_sympt'] = np.where(w.phq2.notna(), (w.phq2>=3).astype(float), np.nan)
w['lonely_often'] = np.where(w.SOC_LONELY.isin([1,2,3,4,5]), w.SOC_LONELY.isin([1,2]).astype(float), np.nan)  # always/usually
w['lonely_any'] = np.where(w.SOC_LONELY.isin([1,2,3,4,5]), w.SOC_LONELY.isin([1,2,3]).astype(float), np.nan)
w['support_low'] = np.where(w.SOC_SUPPORT.isin([1,2,3,4,5]), w.SOC_SUPPORT.isin([4,5]).astype(float), np.nan)
w['lifesat'] = np.where(w.SATISFACTION.isin(range(1,12)), w.SATISFACTION-1, np.nan)
# trust
w['trust_fedstat'] = np.where(w.TRUST_FEDSTAT.isin([1,2]), (w.TRUST_FEDSTAT==1).astype(float), np.nan)
for v in ['TRUST_STATISTICAL','TRUST_MILITARY','TRUST_POLICE','TRUST_SUPREME','TRUST_PRESIDENCY','TRUST_SCHOOLS','TRUST_CRIMJUST','TRUST_CONGRESS','TRUST_CENSUS']:
    w[v.lower()+'_hi'] = np.where(w[v].isin([1,2,3,4]), w[v].isin([1,2]).astype(float), np.nan)
# economic stress
w['exp_diff'] = np.where(w.EXPENSE_DIFFICULT.isin([1,2,3,4]), w.EXPENSE_DIFFICULT.isin([3,4]).astype(float), np.nan)
w['workloss'] = np.where(w.WORKLOSS.isin([1,2]), (w.WORKLOSS==1).astype(float), np.nan)
w['price_vstress'] = np.where(w.PRICESTRESS.isin([1,2,3,4]), (w.PRICESTRESS==1).astype(float), np.nan)
w['price_concern'] = np.where(w.PRICECONCERN.isin([1,2,3,4]), (w.PRICECONCERN==1).astype(float), np.nan)
w['renter'] = np.where(w.TENURE.isin([1,2,3,4]), (w.TENURE==3).astype(float), np.nan)
w['fd_insuff'] = np.where(w.FD_SUFF.isin([1,2,3,4]), w.FD_SUFF.isin([3,4]).astype(float), np.nan)

# ---- SDR helpers
def wmean(df, y, wt='PWEIGHT'):
    m = df[y].notna(); return np.average(df.loc[m,y], weights=df.loc[m,wt])
def est(df, y, unw=True):
    m = df[y].notna(); s = df[m]
    if len(s)==0: return dict(est=np.nan,se=np.nan,n=0)
    th = np.average(s[y], weights=s.PWEIGHT)
    reps = np.array([np.average(s[y], weights=s[rw]) for rw in RW])
    se = np.sqrt(4/80*np.sum((reps-th)**2))
    out = dict(est=th, se=se, n=int(len(s)))
    if unw: out['unw']=s[y].mean()
    return out
def by(df, y, g):
    rows=[]
    for k,s in df.groupby(g):
        e=est(s,y); e[g]=k; rows.append(e)
    return pd.DataFrame(rows)
def diff_test(df,y,g,a,b):
    A=df[df[g]==a]; B=df[df[g]==b]
    ma,mb=A[y].notna(),B[y].notna()
    th=np.average(A.loc[ma,y],weights=A.loc[ma,'PWEIGHT'])-np.average(B.loc[mb,y],weights=B.loc[mb,'PWEIGHT'])
    reps=np.array([np.average(A.loc[ma,y],weights=A.loc[ma,rw])-np.average(B.loc[mb,y],weights=B.loc[mb,rw]) for rw in RW])
    se=np.sqrt(4/80*np.sum((reps-th)**2)); return th,se,th/se

R = {}
R['n_total']=int(len(d)); R['n_workers']=int(len(w)); R['n_any_ai_valid']=int(w.any_ai.notna().sum())
R['share_employed']=est(d.assign(emp=np.where(d.ANYWORK.isin([1,2]),(d.ANYWORK==1).astype(float),np.nan)),'emp')
R['any_ai']=est(w,'any_ai'); R['ai_lastweek']=est(w,'ai_lastweek'); R['ai_daily']=est(w,'ai_daily')
R['ntasks_mean_users']=est(w[w.any_ai==1],'ntasks')
R['ntasks_dist_users']= (w[w.any_ai==1].groupby('ntasks').PWEIGHT.sum()/w[w.any_ai==1].PWEIGHT.sum()).round(4).to_dict()
# frequency among users
u=w[w.any_ai==1]
R['freq_dist']={k:est(u.assign(f=(u.freq==k).astype(float).where(u.freq.notna())),'f') for k in [1,2,3]}
# task shares: among all workers and among users
R['task_all']={TASKS[t]:est(w,t+'_y') for t in tk}
R['task_users']={TASKS[t]:est(u,t+'_y') for t in tk}
# hours
lw=w[w.ai_lastweek==1]
R['hours_dist']={k:est(lw.assign(h=(lw.hours==k).astype(float).where(lw.hours.notna())),'h') for k in range(1,9)}
R['hrs_saved_mean']=est(lw,'hrs_saved'); R['no_saving']=est(lw,'no_saving'); R['big_saving']=est(lw,'big_saving')
R['hrs_saved_by_freq']=by(lw,'hrs_saved','freq').to_dict('records')
R['no_saving_by_freq']=by(lw,'no_saving','freq').to_dict('records')
R['hrs_saved_by_ntasks']=by(lw.assign(nt=lw.ntasks.clip(upper=6)),'hrs_saved','nt').to_dict('records')
# breakdowns
BR={}
for g in ['occ','edu','agegrp','sex','race','inc','cls','tw','region','metro']:
    BR[g]={'any_ai':by(w,'any_ai',g).to_dict('records'),'ai_lastweek':by(w,'ai_lastweek',g).to_dict('records'),
           'ai_daily':by(w,'ai_daily',g).to_dict('records'),'hrs_saved':by(lw,'hrs_saved',g).to_dict('records'),
           'no_saving':by(lw,'no_saving',g).to_dict('records')}
R['breakdowns']=BR
# task mix by occupation (among users)
R['task_by_occ']={o:{TASKS[t]:round(wmean(s,t+'_y'),3) for t in tk} for o,s in u.groupby('occ')}
# occupation composition of users vs workers
R['occ_share_workers']=(w.groupby('occ').PWEIGHT.sum()/w[w.occ.notna()].PWEIGHT.sum()).round(4).to_dict()
R['occ_share_users']=(u.groupby('occ').PWEIGHT.sum()/u[u.occ.notna()].PWEIGHT.sum()).round(4).to_dict()
R['occ_share_daily']=(w[w.ai_daily==1].groupby('occ').PWEIGHT.sum()/w[(w.ai_daily==1)&w.occ.notna()].PWEIGHT.sum()).round(4).to_dict()
# secondary bivariate
w['d3']=np.where(w.any_ai==0,'nonuser',np.where(w.freq==1,'daily',np.where(w.freq==2,'weekly',np.where(w.freq==3,'not last week',None))))
SEC={}
for y in ['anx_sympt','dep_sympt','phq4','lonely_often','lonely_any','support_low','lifesat','trust_fedstat','trust_statistical_hi','trust_census_hi','trust_military_hi','trust_police_hi','trust_supreme_hi','trust_presidency_hi','trust_schools_hi','trust_crimjust_hi','trust_congress_hi','exp_diff','workloss','price_vstress','price_concern','renter','fd_insuff','telework_any']:
    SEC[y]={'by_any_ai':by(w,y,'any_ai').to_dict('records'),'by_daily':by(w[w.d3.notna()],y,'d3').to_dict('records')}
    t=diff_test(w,y,'any_ai',1.0,0.0); SEC[y]['diff']=dict(diff=t[0],se=t[1],z=t[2])
R['secondary']=SEC
# telework x occ
R['ai_by_tw_occ']=w.groupby(['occ','telework_any']).apply(lambda s: wmean(s,'any_ai')).unstack().round(3).to_dict()
R['ai_by_tw_edu']=w.groupby(['edu','telework_any']).apply(lambda s: wmean(s,'any_ai')).unstack().round(3).to_dict()

# ---- regressions with SDR SEs
def wreg(df, y, X, kind='lpm'):
    m = df[[y]+X].notna().all(axis=1); s=df[m]
    Xm = pd.get_dummies(s[X], drop_first=True, dtype=float); Xm=sm.add_constant(Xm)
    def fit(wt):
        if kind=='lpm': return sm.WLS(s[y], Xm, weights=s[wt]).fit().params
        return sm.GLM(s[y], Xm, family=sm.families.Binomial(), freq_weights=s[wt]).fit().params
    b=fit('PWEIGHT'); reps=np.vstack([fit(rw).values for rw in RW])
    se=np.sqrt(4/80*((reps-b.values)**2).sum(axis=0))
    out=pd.DataFrame({'coef':b.values,'se':se,'z':b.values/se},index=b.index); out['n']=len(s)
    bu = sm.OLS(s[y], Xm).fit().params if kind=='lpm' else sm.GLM(s[y], Xm, family=sm.families.Binomial()).fit().params
    out['coef_unw']=bu.values
    return out
base=['agegrp','sex','race','edu','inc','cls','region','metro']
REG={}
REG['any_ai_demog']=wreg(w,'any_ai',base)
REG['any_ai_demog_occ']=wreg(w,'any_ai',base+['occ'])
REG['any_ai_tw']=wreg(w,'any_ai',base+['occ','tw'])
REG['daily_tw']=wreg(w,'ai_daily',base+['occ','tw'])
REG['any_ai_logit']=wreg(w,'any_ai',base+['occ','tw'],kind='logit')
REG['hrs_saved']=wreg(lw,'hrs_saved',base+['occ','tw','freq'])
REG['no_saving']=wreg(lw,'no_saving',base+['occ','tw','freq'])
# secondary outcomes regressed on AI use with controls (associational)
for y in ['anx_sympt','dep_sympt','lonely_often','support_low','lifesat','trust_fedstat','trust_statistical_hi','trust_presidency_hi','trust_military_hi','exp_diff','workloss','price_vstress']:
    REG['sec_'+y]=wreg(w.assign(any_ai=w.any_ai.astype(float)),y,['any_ai']+base+['occ','tw'])
R['reg']={k:v.round(4).reset_index().to_dict('records') for k,v in REG.items()}
w.to_pickle('data/derived/workers.pkl'); lw.to_pickle('data/derived/lastweek.pkl')
json.dump(R, open('data/derived/results.json','w'), default=lambda o: o.item() if hasattr(o,'item') else str(o), indent=1)
print('done', R['any_ai'], R['ai_lastweek'], R['ai_daily'], R['hrs_saved_mean'], R['no_saving'])
