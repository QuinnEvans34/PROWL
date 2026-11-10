"""Static scientific figures from the checked count report; no image/model reads."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    raw=a.report.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('Checked report changed')
    r=json.loads(raw)
    if r['schema']!='prowl.stunet.corrected-tuning-audit.v1':raise ValueError('Wrong report')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for stem in ['tradeoffs','error-oracles','case-changes']:
        for ext in ['png','pdf']:
            if (a.output_dir/f'{stem}.{ext}').exists():raise FileExistsError('Preserve existing figures')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
    series=r['series'];steps=[s['step']/1000 for s in series]
    selected=next(s for s in series if s['step']==r['selected_step']);terminal=series[-1]
    fig,axs=plt.subplots(1,3,figsize=(14,4.5),layout='constrained')
    for key,name in [('positive_macro_dice','Dice'),('positive_macro_precision_defined','Precision'),('positive_macro_recall','Recall')]:
        axs[0].plot(steps,[s['summary'][key] for s in series],marker='o',label=name)
    axs[0].set(xlabel='Global training updates (thousands)',ylabel='Positive-case macro metric',ylim=(0,1),title='Later steps trade recall for precision')
    axs[0].legend();axs[0].grid(alpha=.2)
    for s in series:
        x=s['summary']['false_positive_mL'];y=s['summary']['positive_macro_dice']
        axs[1].scatter(x,y,marker='s' if s is terminal else '*',s=65 if s is terminal else 80)
        axs[1].annotate(f"{s['step']//1000}k",(x,y),xytext=(4,5),textcoords='offset points')
    axs[1].set(xlabel='Total FP volume over 70 scans (mL)',ylabel='Positive-case macro Dice',title='Less total false tissue ≠ higher Dice')
    axs[1].grid(alpha=.2)
    bands=['small','medium','large'];x=np.arange(3)
    for off,s,label in [(-.18,selected,'18k selected'),(.18,terminal,'24k terminal')]:
        axs[2].bar(x+off,[s['size_bands'][b]['positive_macro_dice'] for b in bands],width=.36,label=label)
    axs[2].set(xticks=x,xticklabels=['<1 mL\nn=5','1–10 mL\nn=24','>10 mL\nn=7'],ylim=(0,1),ylabel='Positive-case macro Dice',title='Small-total-lesion cases remain weakest')
    axs[2].legend();fig.suptitle('Corrected STU-Net: all six native validations; raw outputs, no 5 mm filter',fontsize=13)
    for ext in ['png','pdf']:fig.savefig(a.output_dir/f'tradeoffs.{ext}')
    plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,5.5),layout='constrained')
    for ax,s,title in zip(axs,[selected,terminal],['18k selected','24k terminal']):
        cells=s['oracle_only']['error_budget_grid'];image=np.array([c['macro_dice'] for c in cells]).reshape(5,4)
        ax.imshow(image,vmin=0,vmax=1,cmap='viridis',origin='lower',aspect='auto')
        for i in range(5):
            for j in range(4):ax.text(j,i,f'{image[i,j]:.3f}',ha='center',va='center',color='white' if image[i,j]<.6 else 'black')
        ax.set(xticks=range(4),xticklabels=['0%','10%','25%','50%'],yticks=range(5),yticklabels=['0%','25%','50%','75%','100%'],xlabel='Fraction of FN perfectly recovered',ylabel='Fraction of FP perfectly removed (no TP loss)',title=title)
    fig.suptitle('REFERENCE-ONLY ORACLES — hypothetical error budgets, NOT measured tuning gains',fontsize=12)
    for ext in ['png','pdf']:fig.savefig(a.output_dir/f'error-oracles.{ext}')
    plt.close(fig)
    changes=sorted(r['selected_to_terminal']['changes'],key=lambda q:q['dice_delta'])
    fig,ax=plt.subplots(figsize=(14,4.6),layout='constrained')
    ax.bar(range(36),[c['dice_delta'] for c in changes],color=['#ae4550' if c['dice_delta']<0 else '#337d69' for c in changes])
    ax.axhline(0,color='black',linewidth=.7)
    ax.set(xticks=range(36),xticklabels=[str(int(c['case_id'].split('_')[1])) for c in changes],ylabel='Dice change (24k minus 18k)',xlabel='Pseudonymous development case',title='17 improve, 18 decline, 1 unchanged; mean Dice change −0.018545')
    ax.tick_params(axis='x',labelrotation=90)
    for ext in ['png','pdf']:fig.savefig(a.output_dir/f'case-changes.{ext}')
    plt.close(fig)


if __name__=='__main__':main()
