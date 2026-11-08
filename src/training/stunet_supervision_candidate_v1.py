"""Unlaunched single-factor candidate; no trainer imports or runtime defaults."""


def deep_supervision_loss(outputs,target,*,policy):
    import torch
    from torch.nn import functional as F
    weights={'baseline':(16/31,8/31,4/31,2/31,1/31),
             'omit_coarsest':(16/30,8/30,4/30,2/30,0.)}
    if policy not in weights or not isinstance(outputs,(tuple,list)) or len(outputs)!=5:
        raise ValueError('Explicit supported policy and five outputs required')
    if target.dtype!=torch.long or target.ndim!=4 or not ((target>=0)&(target<=2)).all():
        raise ValueError('Long three-class target required')
    if tuple(outputs[0].shape)!=(target.shape[0],3,*target.shape[1:]):
        raise ValueError('Full-resolution target mismatch')
    losses=[];previous=target.shape[1:]
    for out in outputs:
        if out.ndim!=5 or out.shape[:2]!=(target.shape[0],3) or any(a>b for a,b in zip(out.shape[2:],previous)):
            raise ValueError('Invalid scale order')
        if not torch.isfinite(out).all():raise ValueError('Nonfinite logits')
        previous=out.shape[2:]
        small=F.interpolate(target[:,None].float(),size=out.shape[2:],mode='nearest')[:,0].long()
        onehot=F.one_hot(small,3).movedim(-1,1).float()[:,1:]
        prob=out.float().softmax(1)[:,1:];axes=(2,3,4)
        dice=(2*(prob*onehot).sum(axes)+1e-5)/(prob.sum(axes)+onehot.sum(axes)+1e-5)
        losses.append(F.cross_entropy(out.float(),small,reduction='mean')+1-dice.mean())
    # Keep the zero-weight branch connected so gradient/state checks see zero,
    # not missing gradients. The current scientific trainer is not modified.
    return sum(w*l for w,l in zip(weights[policy],losses))
