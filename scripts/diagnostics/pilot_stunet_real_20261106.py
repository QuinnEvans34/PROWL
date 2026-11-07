"""Six real train views and two native development resource profiles; nonpromotable."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from src.data.stunet_inputs_20261106 import Inputs,predict,sha
from src.training.stunet_transfer_20261106 import load_transfer
from src.training.stunet_session_20261106 import Session


def selected(provider):
    available=[n for n in provider.train if provider.sources[n]['ct']['path']]
    positive=sorted((n for n in available if provider.plan['members'][n]['positive']),key=lambda n:(provider.plan['members'][n]['lesion_voxels'],n))
    empty=sorted((n for n in available if not provider.plan['members'][n]['positive']),key=lambda n:(np.prod(provider.sources[n]['native_shape']),n))
    names=[group[i] for group in (positive,empty) for i in (0,len(group)//2,len(group)-1)]
    if len(set(names))!=6:raise ValueError('Six distinct pilot cases required')
    return [next(i for i,e in enumerate(provider.plan['schedule']) if e['case_id']==n) for n in names]


def figure(x,y,path):
    from PIL import Image,ImageDraw
    points=np.argwhere(y==2)
    center=np.median(points,axis=0).astype(int) if len(points) else np.array(y.shape)//2
    canvas=Image.new('RGB',(820,330),'white');draw=ImageDraw.Draw(canvas)
    draw.text((10,5),'Actual augmented128 training view; red pancreas, yellow lesion',fill='black')
    for axis in range(3):
        image=np.take(x[0],int(center[axis]),axis=axis);target=np.take(y,int(center[axis]),axis=axis)
        grey=np.repeat((np.clip(image.T,0,1)*255).astype(np.uint8)[...,None],3,axis=2)
        for code,color in [(1,np.array([255,0,0])),(2,np.array([255,255,0]))]:
            mask=target.T==code;grey[mask]=(.65*grey[mask]+.35*color).astype(np.uint8)
        panel=Image.fromarray(grey[::-1].copy()).resize((256,256),Image.Resampling.NEAREST)
        canvas.paste(panel,(10+270*axis,50));draw.text((10+270*axis,30),f'axis{axis} index{center[axis]}',fill='black')
    canvas.save(path)


def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--source',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(exist_ok=False);started=time.monotonic();stage='load';report={}
    try:
        import torch
        torch.set_num_threads(2);torch.manual_seed(42);torch.cuda.manual_seed_all(42)
        torch.cuda.set_per_process_memory_fraction(6*1024**3/torch.cuda.get_device_properties(0).total_memory)
        torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
        torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
        provider=Inputs(a.inputs,qualification=True);indices=selected(provider)
        identity=dict(input_sha256=provider.identity,train=sorted(provider.train),qualification_indices=indices,nonpromotable=True,precision='fp32')
        model,proof=load_transfer(a.source,a.checkpoint,pools=[[2,2,2]]*4+[[1,1,2]])
        session=Session(model,identity);training=[]
        for address in indices:
            stage='real_view';x,y,trace=provider.training(address);name=trace['case_id'];png=out/(name+'.png');figure(x,y,png)
            before=time.monotonic();stage='real_update';result=session.update(provider);elapsed=time.monotonic()-before
            if result['input']['image_sha256']!=trace['image_sha256'] or result['input']['target_sha256']!=trace['target_sha256']:raise ValueError('Stateless input replay differs')
            training.append(dict(result,seconds=elapsed,png=png.name,png_sha256=sha(png)))
            print(json.dumps(dict(event='diagnostic_update',case_id=name,seconds=elapsed,loss=result['loss'])),flush=True)
        profile=provider.config['native_profile'];available=[n for n in provider.dev if provider.sources[n]['ct']['path']]
        largest=max(available,key=lambda n:profile[n]['tiles']);second=max(available,key=lambda n:np.prod(provider.sources[n]['native_shape']))
        if second==largest:second=sorted(available,key=lambda n:profile[n]['tiles'])[len(available)//2]
        native=[]
        for name in (largest,second):
            stage='native_resource_profile';before=time.monotonic();case=provider.development(name)
            def progress(**kw):
                if kw['tile']%50==0:print(json.dumps(dict(event='native_tiles',case_id=name,**kw)),flush=True)
            result=predict(model,case,progress=progress);result['seconds']=time.monotonic()-before;native.append(result)
            with (out/(name+'-native.json')).open('x') as f:json.dump(result,f)
            del case
        train_seconds=max(x['seconds'] for x in training)*12000*1.5
        native_seconds=max(x['seconds']/x['tiles'] for x in native)*sum(x['tiles'] for x in profile.values())*6*1.5
        estimate=train_seconds+native_seconds+3600
        report=dict(status='PASS',proof=proof,training=training,native=native,
                    native70_tiles=sum(x['tiles'] for x in profile.values()),
                    conservative_training_seconds=train_seconds,conservative_validation_seconds=native_seconds,
                    projected_total_seconds=estimate,within48h=estimate<=48*3600,
                    allocated_peak=torch.cuda.max_memory_allocated(),reserved_peak=torch.cuda.max_memory_reserved(),
                    seconds=time.monotonic()-started,scientific_updates=0,diagnostic_updates=6,
                    inputs_sha256=provider.identity,actual_scope='engineering_only_no_scientific_scores_or_hours')
        if max(report['allocated_peak'],report['reserved_peak'])>6*1024**3:raise RuntimeError('CUDA cap')
    except BaseException as e:
        report=dict(status='FAILED',stage=stage,error=repr(e),seconds=time.monotonic()-started,scientific_updates=0)
        try:report.update(allocated_peak=torch.cuda.max_memory_allocated(),reserved_peak=torch.cuda.max_memory_reserved())
        except Exception:pass
        raise
    finally:
        with (out/'result.json').open('x') as f:json.dump(report,f,indent=2)


if __name__=='__main__':main()
