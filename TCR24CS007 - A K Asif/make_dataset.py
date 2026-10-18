import json
from pathlib import Path

def p(v,op,value):return dict(var=v,op=op,value=value)
def eq(v,value):return p(v,'eq',value)
def port(name,typ='ID',domain=('valid',),required=True):return dict(name=name,type=typ,domain=list(domain),required=required)
def cap(name,pre,effects,inputs=(),outputs=(),typ='API',mechanism=None,resources=('Network',),constraints=(),money=.08,rel=.98,available=True):
    return dict(name=name,type=typ,mechanism=mechanism or {'operation':name,'target':'/'+name.lower()},preconditions=pre,effects=effects,inputs=list(inputs),outputs=list(outputs),constraints=list(constraints),resources=list(resources),quality=dict(time_ms=80,money=money,energy=.12,risk=.02,resource_cost=1),reliability=rel,available=available)
def alternatives(first):
    result=[]
    for typ,money,rel,res in [('DATABASE',.02,.94,['Database']),('GUI',.005,.82,['Browser'])]:
        c=json.loads(json.dumps(first));c.update(name=first['name']+'_'+typ,type=typ,mechanism={'operation':'INSERT' if typ=='DATABASE' else 'CLICK','target':'records' if typ=='DATABASE' else 'submit_button'},resources=res,reliability=rel);c['quality']['money']=money;c['quality']['time_ms']=60 if typ=='DATABASE' else 240;result.append(c)
    return result

def finish(name,variables,initial,goal,caps,compositions):
    return dict(name=name,variables=variables,initial_state=initial,goal=goal,global_constraints=[],available_resources=sorted({r for c in caps for r in c['resources']}),capabilities=caps,compositions=compositions)
order=port('order_id');receipt=port('receipt_id')
a=cap('CreateOrder',[],{'order':True},[port('cart_id')],[order])
b=cap('MakePayment',[eq('order',True)],{'payment':'SUCCESS'},[order],[receipt],resources=('Network','Gateway'),money=.35)
c=cap('SendNotification',[eq('payment','SUCCESS')],{'notification':True},[receipt],[port('message_id')],typ='MESSAGE',resources=('Queue',))
cancel=cap('CancelCart',[eq('order',False)],{'cart':False})
wrong=cap('WrongTypedPayment',[eq('order',True)],{'payment':'SUCCESS'},[port('order_id','INTEGER',(1,2))],[])
extra=[cap('ChangeTheme',[],{'theme':'DARK'},typ='FUNCTION',resources=()),cap('ClearCart',[eq('order',False)],{'cart':False},typ='FUNCTION',resources=()),cap('CheckedOrder',[eq('authenticated',True)],{'order':True},a['inputs'],a['outputs'],constraints=[p('quantity','gt',0)]),cap('Refund',[eq('payment','SUCCESS')],{'payment':'REFUNDED'},[receipt],[])]
commerce=finish('commerce',dict(order=[False,True],payment=['NOT_STARTED','SUCCESS','REFUNDED'],notification=[False,True],cart=[False,True],authenticated=[False,True],quantity=[0,1,2,3],theme=['LIGHT','DARK']),dict(order=False,payment='NOT_STARTED',notification=False,cart=True,authenticated=True,quantity=2,theme='LIGHT'),[eq('payment','SUCCESS'),eq('notification',True)],[a,b,c,cancel,*alternatives(a),wrong,*extra],[['CreateOrder','MakePayment','SendNotification']])
stock=port('stock_id');label=port('label_id')
a=cap('ReserveStock',[eq('reserved',False)],{'reserved':True},[port('request')],[stock],constraints=[p('quantity','gt',0),p('role','in',['STAFF','ADMIN'])],resources=('InventoryDB',))
b=cap('CreateLabel',[eq('reserved',True)],{'labelled':True},[stock],[label],typ='FILE',resources=('FileSystem',))
c=cap('Dispatch',[eq('labelled',True)],{'dispatched':True},[label],[port('tracking_id')],resources=('Courier',),money=.7)
notify=cap('NotifyWarehouse',[eq('reserved',True)],{'notified':True},[stock],[port('warehouse_message')],typ='EVENT',resources=('Queue',))
cancel=cap('ReleaseStock',[eq('reserved',True)],{'reserved':False},[stock],[])
wrong=cap('BadLabel',[eq('reserved',True)],{'labelled':True},[port('stock_id','INTEGER',(1,2))],[])
extra=cap('RotateAudit',[],{'audit':True},typ='FUNCTION',resources=())
logistics=finish('logistics',dict(reserved=[False,True],labelled=[False,True],dispatched=[False,True],notified=[False,True],audit=[False,True],quantity=[0,1,2,3],role=['GUEST','STAFF','ADMIN']),dict(reserved=False,labelled=False,dispatched=False,notified=False,audit=False,quantity=2,role='STAFF'),[eq('dispatched',True),eq('notified',True)],[a,b,c,notify,cancel,*alternatives(a),wrong,extra],[['ReserveStock','CreateLabel','Dispatch'],['ReserveStock','NotifyWarehouse','CreateLabel','Dispatch']])
artifact=port('artifact_id');testresult=port('test_result','STATUS',('PASS',))
a=cap('Compile',[eq('stage','RAW')],{'stage':'BUILT','artifact':True},[port('source_id')],[artifact],typ='COMPUTATION',resources=('CPU',),constraints=[p('size','gt',0)])
b=cap('Test',[eq('stage','BUILT')],{'stage':'TESTED'},[artifact],[testresult],typ='COMPUTATION',resources=('Runner',))
c=cap('Deploy',[eq('stage','TESTED')],{'stage':'DEPLOYED'},[testresult],[port('deployment_id')],resources=('Network','Credentials'),constraints=[eq('credentials',True),eq('environment','PROD')],money=.25)
cancel=cap('ResetBuild',[eq('stage','RAW')],{'stage':'RAW','artifact':False})
wrong=cap('BadTest',[eq('stage','BUILT')],{'stage':'TESTED'},[port('artifact_id','INTEGER',(1,2))],[])
extra=[cap('WarmCache',[],{'cache':True},typ='FUNCTION',resources=('CPU',)),cap('Rollback',[eq('stage','DEPLOYED')],{'stage':'BUILT'},[port('deployment_id')],[])]
build=finish('build',dict(stage=['RAW','BUILT','TESTED','DEPLOYED'],artifact=[False,True],credentials=[False,True],cache=[False,True],size=[0,1,2],environment=['DEV','PROD']),dict(stage='RAW',artifact=False,credentials=True,cache=False,size=1,environment='PROD'),[eq('stage','DEPLOYED')],[a,b,c,cancel,*alternatives(a),wrong,*extra],[['Compile','Test','Deploy']])
# Nontrivial global unary policy: disallow zero-size source states and successors.
build['global_constraints']=[p('size','gt',0)]
Path(__file__).with_name('dataset.json').write_text(json.dumps(dict(schema_version=2,problems=[commerce,logistics,build]),indent=2))
