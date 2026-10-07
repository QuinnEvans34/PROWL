---
pipeline_tag: image-segmentation
license: mit
---

This is a segmentation model (MedFormer architecture) trained for pancreas tumor segmentation, as presented in the paper [**Scaling Artificial Intelligence for Multi-Tumor Early Detection with More Reports, Fewer Masks**](https://huggingface.co/papers/2510.14803).

It serves as a public baseline, specifically referred to as the "segmentation" baseline, and is trained on the [PanTS](https://github.com/MrGiovanni/PanTS) public dataset.

This model is also a starting point for our R-Super framework: you can fine-tune it with radiology reports. Please see our [Report Supervision (R-Super) GitHub](https://github.com/MrGiovanni/R-Super).

**Training and inference code: https://github.com/MrGiovanni/R-Super**

<details>
  <summary>Label order</summary>
  
```yaml
- adrenal_gland_left
- adrenal_gland_right
- aorta
- bladder
- colon
- common_bile_duct
- duodenum
- femur_left
- femur_right
- gall_bladder
- kidney_left
- kidney_right
- liver
- lung_left
- lung_right
- pancreas
- pancreas_body
- pancreas_head
- pancreas_tail
- pancreatic_lesion
- postcava
- prostate
- spleen
- stomach
- superior_mesenteric_artery
- veins
```
</details>

---
# Papers


<b>Learning Segmentation from Radiology Reports</b> <br/>
[Pedro R. A. S. Bassi](https://scholar.google.com/citations?user=NftgL6gAAAAJ&hl=en), [Wenxuan Li](https://scholar.google.com/citations?hl=en&user=tpNZM2YAAAAJ), [Jieneng Chen](https://scholar.google.com/citations?user=yLYj88sAAAAJ&hl=zh-CN), Zheren Zhu, Tianyu Lin, [Sergio Decherchi](https://scholar.google.com/citations?user=T09qQ1IAAAAJ&hl=it), [Andrea Cavalli](https://scholar.google.com/citations?user=4xTOvaMAAAAJ&hl=en), [Kang Wang](https://radiology.ucsf.edu/people/kang-wang), [Yang Yang](https://scholar.google.com/citations?hl=en&user=6XsJUBIAAAAJ), [Alan Yuille](https://www.cs.jhu.edu/~ayuille/), [Zongwei Zhou](https://www.zongweiz.com/)* <br/>
*Johns Hopkins University* <br/>
MICCAI 2025 <br/>
<b>Best Paper Award Runner-up (top 2 in 1,027 papers)</b>  <br/>
<a href='https://link.springer.com/chapter/10.1007/978-3-032-04971-1_29'><img src='https://img.shields.io/badge/Paper-PDF-purple'></a><a href='https://link.springer.com/chapter/10.1007/978-3-032-04971-1_29'><img src='https://img.shields.io/badge/Springer-Link-orange'></a>

<p align="center">
  <img src="https://github.com/MrGiovanni/R-Super/raw/main/documents/miccai_2025_best_paper_award.png"
       alt="Prize"
       width="400">
</p>

<b>Scaling Artificial Intelligence for Multi-Tumor Early Detection with More Reports, Fewer Masks</b> <br/>
[Pedro R. A. S. Bassi](https://scholar.google.com/citations?user=NftgL6gAAAAJ&hl=en), [Wenxuan Li](https://scholar.google.com/citations?hl=en&user=tpNZM2YAAAAJ), [Jieneng Chen](https://scholar.google.com/citations?user=yLYj88sAAAAJ&hl=zh-CN), Zheren Zhu, Tianyu Lin, [Sergio Decherchi](https://scholar.google.com/citations?user=T09qQ1IAAAAJ&hl=it), [Andrea Cavalli](https://scholar.google.com/citations?user=4xTOvaMAAAAJ&hl=en), [Kang Wang](https://radiology.ucsf.edu/people/kang-wang), [Yang Yang](https://scholar.google.com/citations?hl=en&user=6XsJUBIAAAAJ), [Alan Yuille](https://www.cs.jhu.edu/~ayuille/), [Zongwei Zhou](https://www.zongweiz.com/)* <br/>
*Johns Hopkins University* <br/>
<a href='https://huggingface.co/papers/2510.14803'><img src='https://img.shields.io/badge/Paper-HuggingFace-blue'></a>


<b>PanTS: The Pancreatic Tumor Segmentation Dataset</b> <br/>
[Wenxuan Li](https://scholar.google.com/citations?hl=en&user=tpNZM2YAAAAJ), [Xinze Zhou](), [Qi Chen](), Tianyu Lin, Pedro R.A.S. Bassi, ..., [Alan Yuille](https://www.cs.jhu.edu/~ayuille/), [Zongwei Zhou](https://www.zongweiz.com/)<sup>★</sup> <br/>
*Johns Hopkins University* <br/>
<a href='https://www.zongweiz.com/dataset'><img src='https://img.shields.io/badge/Project-Page-Green'></a> <a href='https://www.cs.jhu.edu/~zongwei/publication/li2025pants.pdf'><img src='https://img.shields.io/badge/Paper-PDF-purple'></a>




# Inference

**0- Download and installation.**


<details>
<summary style="margin-left: 25px;">[Optional] Install Anaconda on Linux</summary>
<div style="margin-left: 25px;">
    
```bash
wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh
bash Anaconda3-2024.06-1-Linux-x86_64.sh -b -p ./anaconda3
./anaconda3/bin/conda init
source ~/.bashrc
```
</div>
</details>

```
git clone https://github.com/MrGiovanni/R-Super
cd R-Super/rsuper_train
conda create -n rsuper python=3.10
conda activate rsuper
pip install -r requirements.txt
pip install -U "huggingface_hub[cli]"
hf download AbdomenAtlas/MedFormerPanTS --local-dir ./MedFormerPanTS
```

**1- Pre-processing.** Prepare your dataset in the format below. You can use symlinks instead of copying your data.
<details>
<summary style="margin-left: 25px;">Dataset format.</summary>
<div style="margin-left: 25px;">

```
/path/to/dataset/
├── BDMAP_0000001
|    └── ct.nii.gz
├── BDMAP_0000002
|    └── ct.nii.gz
...
```
</div>
</details>

**2- Inference.** The code below will inference, generating binary segmentation masks. To save probabilities, add the argument --save_probabilities or --save_probabilities_lesions (which saves only probabilities for lesions, not for organs). The optional argument --organ_mask_on_lesion will use organ segmentations (produced by the R-Super model itself, not ground-truth) to remove tumor predictions outside its organ. 

```bash
python predict_abdomenatlas.py --load MedFormerPanTS/pants_pancreas_release/fold_0_latest.pth --img_path /path/to/test/dataset/ --class_list MedFormerPanTS/labels_pants.yaml --save_path /path/to/inference/output/ --organ_mask_on_lesion
```
<details>
<summary style="margin-left: 25px;"> Argument Details </summary>
<div style="margin-left: 25px;">
  
- load: path to the model checkpoint (fold_0_latest.pth)
- img_path: path to dataset
- class_list: a yaml file with the class names of your model
- save_path: path to output, where masks will be saved
- ids: this is an optional argument. By default, the code will predict on all cases in --img_path. If you pass ids, the code will only test with the CT scans indicated in ids. You can use this to separate a test set: --ids /path/to/test/set/ids.csv. The csv file must have a 'BDMAP ID' column with the ids of the test cases.

</details>

For more details, see https://github.com/MrGiovanni/R-Super/tree/main/rsuper_train#test



# Citations
If you use this data, please cite the 2 papers below:

```
@article{bassi2025learning,
  title={Learning Segmentation from Radiology Reports},
  author={Bassi, Pedro RAS and Li, Wenxuan and Chen, Jieneng and Zhu, Zheren and Lin, Tianyu and Decherchi, Sergio and Cavalli, Andrea and Wang, Kang and Yang, Yang and Yuille, Alan L and others},
  journal={arXiv preprint arXiv:2507.05582},
  year={2025}
}

@article{li2025pants,
  title={PanTS: The Pancreatic Tumor Segmentation Dataset},
  author={Li, Wenxuan and Zhou, Xinze and Chen, Qi and Lin, Tianyu and Bassi, Pedro RAS and Plotka, Szymon and Cwikla, Jaroslaw B and Chen, Xiaoxi and Ye, Chen and Zhu, Zheren and others},
  journal={arXiv preprint arXiv:2507.01291},
  year={2025},
  url={https://github.com/MrGiovanni/PanTS}
}

```

## Acknowledgement

This work was supported by the Lustgarten Foundation for Pancreatic Cancer Research, the Patrick J. McGovern Foundation Award, and the National Institutes of Health (NIH) under Award Number R01EB037669. We would like to thank the Johns Hopkins Research IT team in [IT@JH](https://researchit.jhu.edu/) for their support and infrastructure resources where some of these analyses were conducted; especially [DISCOVERY HPC](https://researchit.jhu.edu/). Paper content is covered by patents pending.