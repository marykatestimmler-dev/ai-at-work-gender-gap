"""Turn data/derived/results.json into the table rows used by the main report (data/derived/tables.json)."""
import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import json,pandas as pd
R=json.load(open('data/derived/results.json'))
T={}
pct=lambda e: f"{100*e['est']:.1f}"
def row(e): return [pct(e), f"{100*e['se']:.1f}", f"{100*e['unw']:.1f}", str(e['n'])]
T['headline']=[['Measure','Weighted %','SE','Unweighted %','n']]+[[l]+row(R[k]) for l,k in [('Used AI for at least one work task (no time frame)','any_ai'),('Used AI at work last week','ai_lastweek'),('Used AI at work every day last week','ai_daily')]]
T['tasks']=[['Task','All workers %','SE','Among users %','SE']]+[[k,pct(R['task_all'][k]),f"{100*R['task_all'][k]['se']:.1f}",pct(R['task_users'][k]),f"{100*R['task_users'][k]['se']:.1f}"] for k in sorted(R['task_all'],key=lambda k:-R['task_all'][k]['est'])]
order={'occ':None,'edu':['< HS','HS grad','Some college',"Associate's","Bachelor's",'Graduate'],'agegrp':['25-34*','35-44','45-54','55-64','65+'],'sex':['Female','Male'],'race':['Asian','Black','Hispanic','White','Other/multiracial'],'inc':['<$25k','$25-35k','$35-50k','$50-75k','$75-100k','$100-150k','$150k+'],'cls':['Private','Government','Nonprofit','Self-employed','Family business'],'tw':['No telework','Telework 1-2 days','Telework 3-4 days','Telework 5+ days'],'region':['Northeast','Midwest','South','West']}
names={'occ':'Occupation','edu':'Education','agegrp':'Age','sex':'Sex','race':'Race/ethnicity','inc':'Household income (2025)','cls':'Class of worker','tw':'Telework last week','region':'Region'}
rows=[['Group','Ever used %','(SE)','Unweighted %','Last week %','Daily %','Hours saved (users)','No time saved %','n']]
for g,o in order.items():
    B=R['breakdowns'][g]; a=pd.DataFrame(B['any_ai']).set_index(g); l=pd.DataFrame(B['ai_lastweek']).set_index(g); d=pd.DataFrame(B['ai_daily']).set_index(g); h=pd.DataFrame(B['hrs_saved']).set_index(g); ns=pd.DataFrame(B['no_saving']).set_index(g)
    keys=o or [k for k in a.sort_values('est',ascending=False).index if k!='Farming/fishing/forestry']
    rows.append([names[g],'','','','','','','',''])
    for k in keys:
        rows.append(['   '+k,f"{100*a.loc[k,'est']:.1f}",f"({100*a.loc[k,'se']:.1f})",f"{100*a.loc[k,'unw']:.1f}",f"{100*l.loc[k,'est']:.1f}",f"{100*d.loc[k,'est']:.1f}",f"{h.loc[k,'est']:.2f}" if k in h.index else '–',f"{100*ns.loc[k,'est']:.1f}" if k in ns.index else '–',str(int(a.loc[k,'n']))])
T['breakdown']=rows
labs={1:'Less than 1 hour',2:'1 hour',3:'2 hours',4:'3 hours',5:'4 hours',6:'More than 4 hours',7:'No time savings',8:'Required additional time'}
T['hours']=[['Response','Weighted %','SE','Unweighted %']]+[[labs[k],pct(R['hours_dist'][str(k)]),f"{100*R['hours_dist'][str(k)]['se']:.1f}",f"{100*R['hours_dist'][str(k)]['unw']:.1f}"] for k in range(1,9)]
lab={'anx_sympt':'Anxiety symptoms (GAD-2 ≥3)','dep_sympt':'Depressive symptoms (PHQ-2 ≥3)','phq4':'PHQ-4 score (0–12, mean)','lonely_often':'Lonely always/usually','lonely_any':'Lonely at least sometimes','support_low':'Rarely/never gets needed support','lifesat':'Life satisfaction (0–10, mean)','trust_fedstat':'Tends to trust federal statistics','trust_statistical_hi':'Confidence in statistical agencies (great deal/quite a lot)','trust_census_hi':'Confidence in Census Bureau','trust_military_hi':'Confidence in the military','trust_police_hi':'Confidence in police','trust_supreme_hi':'Confidence in Supreme Court','trust_presidency_hi':'Confidence in the presidency','trust_schools_hi':'Confidence in public schools','trust_crimjust_hi':'Confidence in criminal justice system','trust_congress_hi':'Confidence in Congress','exp_diff':'Somewhat/very difficult to pay usual expenses','workloss':'Household lost employment income (4 wks)','price_vstress':'Price increases "very stressful"','price_concern':'Very concerned prices will rise','renter':'Renter','fd_insuff':'Food sometimes/often not enough'}
rows=[['Outcome','Non-users','Users','Raw difference','z','Adjusted coef. (LPM)','z']]
for y,l in lab.items():
    S=R['secondary'][y]; a=pd.DataFrame(S['by_any_ai']).set_index('any_ai'); mult=1 if y in('phq4','lifesat') else 100
    reg=R['reg'].get('sec_'+y); rc=''; rz=''
    if reg:
        rr=[r for r in reg if r['index']=='any_ai'][0]; rc=f"{rr['coef']*mult:+.2f}" if mult==1 else f"{rr['coef']*100:+.1f}"; rz=f"{rr['z']:.2f}"
    f=(lambda v: f"{v:.2f}") if mult==1 else (lambda v: f"{100*v:.1f}")
    rows.append([l,f(a.loc[0.0,'est']),f(a.loc[1.0,'est']),("+" if S['diff']['diff']>=0 else "")+f(S['diff']['diff']),f"{S['diff']['z']:.2f}",rc,rz])
T['secondary']=rows
def regtab(k, drop=('const',)):
    df=pd.DataFrame(R['reg'][k]).set_index('index')
    out=[['Variable (reference in note)','Coef. (weighted)','SE','z','Coef. (unweighted)']]
    for i,r in df.iterrows():
        if i in drop: continue
        star='***' if abs(r.z)>2.576 else '**' if abs(r.z)>1.96 else '*' if abs(r.z)>1.645 else ''
        out.append([i.replace('_',': ',1),f"{r.coef:+.3f}{star}",f"{r.se:.3f}",f"{r.z:.2f}",f"{r.coef_unw:+.3f}"])
    out.append(['N',str(int(df.n.iloc[0])),'','',''])
    return out
T['reg_any']=regtab('any_ai_tw'); T['reg_daily']=regtab('daily_tw'); T['reg_hours']=regtab('hrs_saved'); T['reg_nosave']=regtab('no_saving')
T['freq']=[['Frequency (among users)','Weighted %','SE']]+[[l,pct(R['freq_dist'][k]),f"{100*R['freq_dist'][k]['se']:.1f}"] for k,l in [('1','Every day last week'),('2','At least 1 day last week, not every day'),('3','Used, but not last week')]]
T['ntasks']={k:round(v*100,1) for k,v in R['ntasks_dist_users'].items()}
T['occshare']=[['Occupation','Share of all workers %','Share of AI users %','Share of daily users %']]+[[o,f"{100*R['occ_share_workers'][o]:.1f}",f"{100*R['occ_share_users'][o]:.1f}",f"{100*R['occ_share_daily'][o]:.1f}"] for o in sorted(R['occ_share_workers'],key=lambda o:-R['occ_share_daily'][o])]
json.dump(T,open('data/derived/tables.json','w'),indent=1); print('ok')
