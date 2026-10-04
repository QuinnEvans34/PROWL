"""Versioned matched cosine prefix followed by a bounded constant-rate tail."""
import math
import torch
from src.data.source_inventory_records import require

REAL_SCHEDULE=dict(schema_version='twomm-cosine-tail-1',prefix_steps=300,tail_learning_rate=.00001)


def validate(schedule,config):
    require(set(schedule)==set(REAL_SCHEDULE) and schedule['schema_version']==REAL_SCHEDULE['schema_version'],
        'Unknown matched-tail schedule')
    require(type(schedule['prefix_steps']) is int and 0<schedule['prefix_steps']<config['max_steps'],
        'Invalid cosine prefix')
    rate=schedule['tail_learning_rate']
    require(type(rate) in (float,int) and math.isfinite(rate) and 0<rate<=config['learning_rate'],
        'Invalid tail rate')


def next_rate(config,step):
    validate(config['schedule'],config)
    require(type(step) is int and 0<=step<=config['max_steps'],'Invalid tail schedule position')
    prefix=config['schedule']['prefix_steps']
    return (config['learning_rate']*(1+math.cos(math.pi*step/prefix))/2 if step<prefix
        else config['schedule']['tail_learning_rate'])


class CosineThenConstantLR(torch.optim.lr_scheduler.CosineAnnealingLR):
    """Retain PyTorch's exact recursive cosine arithmetic until the explicit tail."""
    def __init__(self,optimizer,*,prefix_steps,tail_learning_rate):
        self.tail_learning_rate=tail_learning_rate
        super().__init__(optimizer,T_max=prefix_steps,eta_min=0)
    def get_lr(self):
        if self.last_epoch>=self.T_max:
            return [self.tail_learning_rate for _ in self.base_lrs]
        return super().get_lr()
    def _get_closed_form_lr(self):
        if self.last_epoch>=self.T_max:
            return [self.tail_learning_rate for _ in self.base_lrs]
        return super()._get_closed_form_lr()
