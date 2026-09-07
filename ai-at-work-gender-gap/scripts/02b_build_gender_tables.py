"""Turn data/derived/gender.json into the table rows used by the gender addendum (data/derived/gtables.json)."""
import os; os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
import json; G=json.load(open('data/derived/gender.json')); T={}
lab=G['labels']; pct=lambda v: f"{100*v:.1f}"
isc=lambda y: y in ('ntasks','hrs_saved')
f=lambda y,v: f"{v:.2f}" if isc(y) else pct(v)
T['raw']=[['Outcome','Women (w)','Men (w)','Gap (w)','SE (w)','Women (unw)','Men (unw)','Gap (unw)','SE (unw)','n (W/M)']]
for y,r in G['raw'].items():
    T['raw'].append([lab[y],f(y,r['female']),f(y,r['male']),('+' if r['gap']>=0 else '')+f(y,r['gap']),f(y,r['se']),f(y,r['female_unw']),f(y,r['male_unw']),('+' if r['gap_unw']>=0 else '')+f(y,r['gap_unw']),f(y,r['se_unw']),f"{r['n_f']}/{r['n_m']}"])
specs=list(G['ladder']['any_ai']); short=['Raw','+ age, race, region, metro','+ education, income','+ occupation, sector, telework','+ marital, children, hh size','+ health, language, insurance, wellbeing']
def star(c,s): z=abs(c/s); return '***' if z>2.576 else '**' if z>1.96 else '*' if z>1.645 else ''
for y in ['any_ai','ai_lastweek','ai_daily','ntasks','hrs_saved','big_saving']:
    rows=[['Specification','Weighted coef.','SE','Unweighted coef.','SE','n']]
    for s,sh in zip(specs,short):
        r=G['ladder'][y][s]; m=1 if isc(y) else 100; d=2 if isc(y) else 1
        rows.append([sh,f"{r['coef']*m:+.{d}f}{star(r['coef'],r['se'])}",f"{r['se']*m:.{d}f}",f"{r['coef_unw']*m:+.{d}f}{star(r['coef_unw'],r['se_unw'])}",f"{r['se_unw']*m:.{d}f}",str(r['n'])])
    T['ladder_'+y]=rows
rows=[['Task','Women users %','Men users %','Gap (pp)','SE','Conditional gap (w)','Conditional gap (unw)','Gap among all workers']]
for t,r in sorted(G['tasks'].items(),key=lambda kv:-kv[1]['users']['gap']):
    u=r['users']; c=r['cond_users']
    rows.append([t,pct(u['female']),pct(u['male']),f"{u['gap']*100:+.1f}",f"{u['se']*100:.1f}",f"{c['coef']*100:+.1f}{star(c['coef'],c['se'])}",f"{c['coef_unw']*100:+.1f}{star(c['coef_unw'],c['se_unw'])}",f"{r['all']['gap']*100:+.1f}"])
T['tasks']=rows
names={'occ':'Occupation','tw':'Telework','agegrp':'Age','parent':'Children at home','edu':'Education','inc':'Household income','race':'Race/ethnicity','cls':'Class of worker','region':'Region','ms':'Marital status'}
rows=[['Group','Any use: W / M / gap (w)','gap (unw)','Daily: W / M / gap (w)','SE','gap (unw)','Hours: W / M / gap (w)','gap (unw)','n W/M']]
for g,H in G['het'].items():
    rows.append([names[g]]+['']*8)
    for k,r in H.items():
        a=r['any_ai']; d=r['ai_daily']; h=r['hrs']
        rows.append(['   '+k,f"{a['female']*100:.0f} / {a['male']*100:.0f} / {a['gap']*100:+.1f}",f"{a['gap_unw']*100:+.1f}",f"{d['female']*100:.1f} / {d['male']*100:.1f} / {d['gap']*100:+.1f}",f"{d['se']*100:.1f}",f"{d['gap_unw']*100:+.1f}",(f"{h['female']:.2f} / {h['male']:.2f} / {h['gap']:+.2f}" if h else '–'),(f"{h['gap_unw']:+.2f}" if h else '–'),f"{a['n_f']}/{a['n_m']}"])
T['het']=rows
vn={'tele':'Male × any telework','kid_u5':'Male × child under 5 at home','anykid':'Male × any child under 18','comp':'Male × computer occupation','mgmt':'Male × management/business occupation','young':'Male × age under 45','married':'Male × married'}
rows=[['Interaction term','Daily use (w)','SE','Daily use (unw)','SE','Any use (w)','SE','Any use (unw)','SE','Hours saved (w)','SE','Hours (unw)','SE']]
for v,l in vn.items():
    d=G['inter']['ai_daily'][v]; a=G['inter']['any_ai'][v]; h=G['inter']['hrs_saved'][v]
    rows.append([l,f"{d['coef']*100:+.1f}{star(d['coef'],d['se'])}",f"{d['se']*100:.1f}",f"{d['coef_unw']*100:+.1f}{star(d['coef_unw'],d['se_unw'])}",f"{d['se_unw']*100:.1f}",f"{a['coef']*100:+.1f}{star(a['coef'],a['se'])}",f"{a['se']*100:.1f}",f"{a['coef_unw']*100:+.1f}{star(a['coef_unw'],a['se_unw'])}",f"{a['se_unw']*100:.1f}",f"{h['coef']:+.2f}{star(h['coef'],h['se'])}",f"{h['se']:.2f}",f"{h['coef_unw']:+.2f}{star(h['coef_unw'],h['se_unw'])}",f"{h['se_unw']:.2f}"])
T['inter']=rows
rows=[['Outcome / specification','Total gap','Explained by composition','Unexplained','Share unexplained','Largest composition terms']]
gn={'occ':'occupation','edu':'education','inc':'income','tw':'telework','freq':'frequency','race':'race','agegrp':'age','cls':'sector','region':'region','ms':'marital','hhsize':'hh size','kid':'children','lang':'language','lifesat':'life sat.','phq4':'PHQ-4','cogdiff':'cognition','ins':'insurance','disab':'disability','metro':'metro'}
for y,l in [('any_ai','Any AI use (pp)'),('ai_daily','Daily use (pp)'),('ntasks','Task types (users)'),('hrs_saved','Hours saved (last-week users)')]:
    for s,sl in [('spec3_w','labor-market controls, weighted'),('spec3_unw','labor-market controls, unweighted'),('spec5_w','kitchen sink, weighted'),('spec5_unw','kitchen sink, unweighted')]:
        r=G['kob'][y][s]; m=1 if isc(y) else 100; d=2 if isc(y) else 1
        top=', '.join(f"{gn.get(k,k)} {v*m:+.{d}f}" for k,v in sorted(r['groups'].items(),key=lambda kv:-abs(kv[1]))[:3])
        rows.append([f"{l}: {sl}",f"{r['total']*m:+.{d}f}",f"{r['explained']*m:+.{d}f}",f"{r['unexplained']*m:+.{d}f}",f"{100*r['unexplained']/r['total']:.0f}%" if abs(r['total'])>1e-6 else '–',top])
T['kob']=rows
rows=[['Characteristic','Women (w) %','Men (w) %','Women (unw) %','Men (unw) %']]
for c,l in [('occ','Occupation'),('edu','Education'),('inc','Household income'),('tw','Telework'),('cls','Class of worker'),('agegrp','Age'),('parent','Children at home'),('ms','Marital status')]:
    rows.append([l,'','','',''])
    for k,v in G['comp'][c].items(): rows.append(['   '+k,pct(v['f_w']),pct(v['m_w']),pct(v['f_unw']),pct(v['m_unw'])])
T['comp']=rows
W=G['wdiag']
T['wdiag']=[['Diagnostic','Value'],['Male share of workers, weighted / unweighted',f"{W['share_male_w']*100:.1f}% / {W['share_male_unw']*100:.1f}%"],['Mean person weight, men / women',f"{W['mean_w_m']:,.0f} / {W['mean_w_f']:,.0f}"],['Coefficient of variation of weights, men / women',f"{W['cv_w_m']:.2f} / {W['cv_w_f']:.2f}"],['Kish design effect from weight variation, men / women',f"{W['deff_m']:.1f} / {W['deff_f']:.1f}"],['Daily-use gap across the 80 replicate weightings (min – max)',f"{W['daily_gap_rep_min']*100:+.1f} to {W['daily_gap_rep_max']*100:+.1f} pp"],['Daily-use gap with weights trimmed at 99th / 95th percentile',f"{W['daily_gap_trim99']*100:+.1f} / {W['daily_gap_trim95']*100:+.1f} pp"]]
json.dump(T,open('data/derived/gtables.json','w'),indent=1); print('ok')
