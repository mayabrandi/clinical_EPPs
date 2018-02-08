# clinical_EPPs 
Should be updated whenever a new script is added ore removed from the directory and whenever a script is used in a new lims step.

### Prerequisites


[SciLifeLab/genologics](https://github.com/SciLifeLab/genologics/tree/master/genologics)

## EPPs
Scripts to be run from LIMS.



Script | Step | Comment
--- | --- | ---
aliquot_covaris_microbial.py|CG002 - Normalization of microbial samples|
aliquot_for_lib_pool.py|G002 - Aliquot Samples for Library Pooling|
aliquot_sequencing_microbial.py|CG002 - Normalization of microbial samples for sequencing|
amount2qc.py|CG002 - Quantit QC (DNA)|
art_hist.py|| Helper script, used by other EPPS
bcl2fastq.py|CG002 - Bcl Conversion & Demultiplexing (Illumina SBS)|
calculate_amount.py|CG002 - Qubit QC (DNA)|
||CG002 - Qubit QC (Library Validation)|
calc_vol.py|CG002 - Aliquot Samples for Covaris|
copy_field_samp2art.py|CG002 - Aliquot Samples for Library Pooling|
copy_orig_well_art2samp.py|CG002 - Reception Control|
copy_UDFs_between_WFs.py|CG002 - Plate Setup MAF|
copyUDFs_from_aggregateQC_or_other.py|CG002 - Aliquot Samples for Library Pooling|
copyUDFs_from_aggregateQC.py|G002 - Aliquot Samples for Library Pooling
||CG002 - Library Normalization (HiSeq X)|
demultiplexdata2qc.py|CG002 - Bcl Conversion & Demultiplexing (Illumina SBS)|
file2udf_quantit_qc.py|CG002 - Quantit QC (DNA)|
get_average_size.py|CG002 - Tapestation Microbial QC|
get_EB_vol.py| CG002 - Aliquot Libraries for Hybridization (SS XT)|
get_missing_reads.py|CG002 - Sequence Aggregation|
help_get_stuff.py||silly development helper
LibNorm_calc_vol.py|CG002 - Library Normalization (HiSeq X)|
MAF_calc_vol.py|CG002 - Plate Setup MAF|
make_bravo_csv.py|CG002 - Normalization of microbial samples|
||CG002 - Normalization of microbial samples for sequencing|
make_MAF_sample_table.py|CG002 - Plate Setup MAF|
make_placement_map.py|CG002 - Aliquot Samples for Covaris|
||CG002 - Plate Setup MAF|
||CG002 - Library Normalization (HiSeq X)|
molar_concentration.py|CG002 - Aggregate QC (Library Validation)|
||CG002 - Qubit QC RML|
move_samples.py|CG002 - Aggregate QC (Library Validation)|
||CG002 - Sort HiSeq Samples|
||CG002 - Sort HiSeq X Samples (HiSeq X)|
qc2udf_art2samp.py| CG002 - Aggregate QC (DNA)|
||CG002 - Sequence Aggregation|
||CG002 - Sequence Aggregation|
||CG002 - Aggregate QC (Library Validation)|
qPCR_dilution.py|CG002 - qPCR QC (Library Validation)|
reads_aggregation.py|CG002 - Sequence Aggregation|
reads_aggregation_rml.py|CG002 - Sequence Aggregation|
reception_control.py|CG002 - Reception Control|
rerun.py|CG002 - Sequence Aggregation|
set_qc.py|CG002 - Qubit QC (DNA)|
||CG002 - Qubit QC (Library Validation)|


#### Scripts no longer in use


```python
concentration2qc.py
aliquot_for_lib_pool_2_5_nM.py  
copy_field_art2samp.py
copy_well_art2samp.py
glsapiutil.py
invoice.py
make_bravo_csv_test.py
make_bravo_normalization_file.py
make_MAF_plate_layout.py
microbial_copyUDFs_from_aggregateQC.py
qPCR_dilution_old.py
reagent-label.py
aliquot_for_lib_pool_no_set_conc.py
set_udf_from_excel.py
```
