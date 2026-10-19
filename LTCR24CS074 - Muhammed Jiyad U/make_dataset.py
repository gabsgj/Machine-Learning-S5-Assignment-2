import json
from pathlib import Path

def port(name,typ='ID',domain=('valid',),required=True):return dict(name=name,type=typ,domain=list(domain),required=required)
def cap(name,pre,effects,inputs=(),outputs=(),typ='API',money=.1,rel=.99,resources=('Network',),constraints=(),available=True):
    return dict(name=name,type=typ,mechanism={'operation':name,'target':('/'+name.lower()) if typ=='API' else name.lower()},inputs=list(inputs),outputs=list(outputs),preconditions=pre,effects=effects,constraints=list(constraints),resources=list(resources),quality=dict(time_ms=100,resource_cost=1,money=money,risk=.01,energy=.1),reliability=rel,available=available)
def eq(k,v):return [k,'eq',v]
problems=[]
for domain,names in [('commerce',['Order','Payment','Notification']),('document',['Document','Signature','Archive']),('data',['Extract','Transform','Publish'])]:
    a,b,c=names
    variables={a:[False,True],b:[False,True],c:[False,True],'Unrelated':[False,True],'Authenticated':[False,True],'quantity':[0,1,2]}
    first=cap('Create'+a,[],{a:True},[port('request')],[port(a.lower()+'_id')],constraints=[['quantity','gt',0],eq('Authenticated',True)])
    # Explicit required experiment pattern has no additional precondition or constraint.
    if domain=='commerce':first['constraints']=[]
    second=cap('Make'+b,[eq(a,True)],{b:True},first['outputs'],[port(b.lower()+'_id')],resources=('Network','Gateway'),money=.5)
    third=cap('Send'+c,[eq(b,True)],{c:True},second['outputs'],[port(c.lower()+'_id')])
    cancel=cap('Cancel'+a,[eq(a,False)],{a:False},first['outputs'],[])
    if domain=='commerce':cancel['name']='CancelCart'
    alternatives=[]
    for typ,money,rel,res in [('DATABASE',.03,.97,('Database',)),('GUI',.01,.90,('Browser',))]:
        v=cap('Create'+a+'_'+typ,first['preconditions'],first['effects'],first['inputs'],first['outputs'],typ,money,rel,res,first['constraints'])
        alternatives.append(v)
    irrelevant=cap('RotateLog',[],{'Unrelated':True},[],[],typ='FILE',resources=('FileSystem',))
    bad=cap('WrongInput',[eq(a,True)],{b:True},[port(a.lower()+'_id','INTEGER',(1,2))],[])
    constrained=cap('Constrained'+a,[],{a:True},first['inputs'],first['outputs'],constraints=[['quantity','gt',0],eq('Authenticated',True)])
    problems.append(dict(name=domain,variables=variables,initial_state={a:False,b:False,c:False,'Unrelated':False,'Authenticated':True,'quantity':1},goal=[eq(c,True)],available_resources=['Network','Gateway','Database','Browser','FileSystem'],global_constraints=[['quantity','le',2]],capabilities=[first,second,third,cancel,*alternatives,irrelevant,bad,constrained],compositions=[[first['name'],second['name'],third['name']]]))
Path(__file__).with_name('dataset.json').write_text(json.dumps({'schema_version':1,'problems':problems},indent=2))
