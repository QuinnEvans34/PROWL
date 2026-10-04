import pytest
import torch
from src.training import segmenter_loss_audit_v1 as audit, segmenter_session_v1 as numerical

@pytest.mark.parametrize('target', [
    [0,0,0,0,0,0,0,0], [1,1,1,1,1,1,1,1], [2,2,2,2,2,2,2,2],
    [0,1,1,1,1,1,1,2], [2,1,0,0,0,0,0,0], [0,0,0,2,0,0,0,0]])
@pytest.mark.parametrize('dtype', [torch.float32, torch.float64])
def test_scalar_and_analytic_gradient_parity(target, dtype):
    g = torch.Generator().manual_seed(9)
    z = torch.randn((1,3,2,2,2), generator=g, dtype=dtype, requires_grad=True)
    y = torch.tensor(target).reshape(1,2,2,2)
    ce, di, p, gc, gd, row = audit.terms(z,y)
    tol = 1e-6 if dtype == torch.float32 else 1e-12
    assert torch.allclose(ce+di, numerical.objective(z,y,numerical.LOSS_V3), atol=tol, rtol=0)
    assert abs(sum(row['ce_by_true_class'])-ce.item()) < tol
    for loss, grad in ((ce,gc), (di,gd)):
        expected = torch.autograd.grad(loss,z,retain_graph=True)[0]
        assert torch.allclose(grad,expected,atol=tol,rtol=0)
    assert torch.allclose((gc+gd).sum(1), torch.zeros_like(y,dtype=dtype), atol=tol,rtol=0)


def test_batch_absence_reduction():
    z=torch.randn(2,3,2,2,2,dtype=torch.float64,requires_grad=True)
    y=torch.zeros(2,2,2,2,dtype=torch.long); y[1,0,0,0]=2; y[1,1,1,1]=1
    ce,di,p,gc,gd,row=audit.terms(z,y)
    assert [r['batch'] for r in row['dice_present_terms']]==[1,1]
    assert gd[0].abs().sum()==0
    assert torch.allclose(di+ce,numerical.objective(z,y,numerical.LOSS_V3),atol=1e-12,rtol=0)
    assert torch.allclose(gd,torch.autograd.grad(di,z)[0],atol=1e-12,rtol=0)

@pytest.mark.parametrize('name', numerical.NAMES)
def test_invented_cases_head_decomposition_no_mutation(name):
    model=numerical.scratch(numerical.config()); model.eval(); x,y=numerical.fixture(name)
    # Accepted GroupNorm/no-dropout architecture has identical train/eval forwards.
    with torch.no_grad():
        a=model(x[None]); model.train(); b=model(x[None]); model.eval()
    assert torch.equal(a,b)
    clone=audit.analysis_clone(model,'cpu'); row=audit.analyze(clone,x[None],y[None])
    assert row['nonmutation_verified'] and row['model_forwards']==1 and row['head_vjp_queries']==2
    assert sum(row['class_counts'])==24**3
    assert row['class_counts']==[int((y==k).sum()) for k in range(3)]
    c=torch.tensor(row['head_gradients']['ce']['values'])
    d=torch.tensor(row['head_gradients']['dice']['values'])
    total=torch.tensor(row['head_gradients']['total']['values'])
    assert torch.allclose(c+d,total,atol=1e-6)
    # Independent total objective backward oracle for the same clone.
    z=clone(x[None]); expected=torch.autograd.grad(numerical.objective(z,y[None],numerical.LOSS_V3),[dict(clone.named_parameters())[n] for n in audit.HEAD])
    oracle=audit.head_stats(expected)
    assert torch.allclose(torch.tensor(oracle['values']),total,atol=1e-6,rtol=1e-5)

@pytest.mark.parametrize('fault', ['nan','code','dtype','shape','empty'])
def test_bad_numerics_refused(fault):
    z=torch.ones(1,3,2,2,2); y=torch.zeros(1,2,2,2,dtype=torch.long)
    if fault=='nan': z[0,0,0,0,0]=float('nan')
    if fault=='code': y[0,0,0,0]=3
    if fault=='dtype': y=y.float()
    if fault=='shape': y=y[:,:,:,:1]
    if fault=='empty': z=z[:0]; y=y[:0]
    with pytest.raises(ValueError): audit.terms(z,y)


def test_audit_protected_role_and_batch_mutation():
    from scripts.diagnostics.segmenter_loss_audit import sealed_batch
    from src.data.segmenter_training_inputs_v1 import InventedInputs
    provider=InventedInputs(24)
    with pytest.raises(ValueError):sealed_batch(provider,provider.control,'invented-validation')
    with pytest.raises(ValueError):sealed_batch(provider,provider.control,'held-or-new-member')
    with pytest.raises(ValueError):sealed_batch(object(),provider.control,provider.control['train'][0])
    changed=dict(provider.control,train=['substitution']*6)
    with pytest.raises(ValueError):sealed_batch(provider,changed,provider.control['train'][0])
    b,x,y=sealed_batch(provider,provider.control,provider.control['train'][0])
    b.target[0,0,0]=2
    from src.data.manifest_records import canonical,digest
    with pytest.raises(ValueError):b.checked(digest(canonical(provider.control)),'optimizer',b.study_id)


def test_audit_requires_head_only_clone():
    m=numerical.scratch(numerical.config());x,y=numerical.fixture('sparse')
    with pytest.raises(ValueError):audit.analyze(m,x[None],y[None])
    m=audit.analysis_clone(m,'cpu');m.train()
    with pytest.raises(ValueError):audit.analyze(m,x[None],y[None])
    m.eval();dict(m.named_parameters())[audit.HEAD[0]].grad=torch.ones_like(dict(m.named_parameters())[audit.HEAD[0]])
    with pytest.raises(ValueError):audit.analyze(m,x[None],y[None])


def test_request_pin_hashes_persisted_encoding(tmp_path):
    from scripts.diagnostics.segmenter_loss_audit import request_pin
    from scripts.diagnostics.segmenter_source_verification import put
    from src.data.manifest_records import canonical,digest
    p=tmp_path/'request.json'; value={'example':'request'};put(p,value)
    assert request_pin(p)==digest(p.read_bytes())
    assert request_pin(p)!=digest(canonical(value)) # canonical appends a newline; source.put does not
