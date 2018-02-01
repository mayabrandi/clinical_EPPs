# clinical_EPPs 

Scripts to be run from LIMS

## EPPs

These are all scripts thar are run from different steps within lims. 

### Prerequisites


[genologics](https://github.com/SciLifeLab/genologics/tree/master/genologics)

### EPPs


These are all scripts thar are run from different steps within lims.

Script | Step | Comment
--- | --- | ---
rerun.py |CG002 - Sequence Aggregation  | Rerun HiseqX, Rerun Hisq2500, Rerun (RML) 
aliquot_covaris_microbial.py|CG002 - Normalization of microbial samples|
aliquot_for_lib_pool_2_5_nM.py||
aliquot_for_lib_pool_no_set_conc.py|G002 - Aliquot Samples for Library Pooling|
aliquot_for_lib_pool.py|G002 - Aliquot Samples for Library Pooling|
aliquot_sequencing_microbial.py|CG002 - Normalization of microbial samples for sequencing|
art_hist.py||
bcl2fastq.py|CG002 - Bcl Conversion & Demultiplexing (Illumina SBS)|
calculate_amount.py|CG002 - Qubit QC (DNA)|
|CG002 - Qubit QC (Library Validation)|
calc_vol.py|CG002 - Aliquot Samples for Covaris|
concentration2qc.py||
copy_field_art2samp.py||
copy_field_samp2art.py|CG002 - Aliquot Samples for Library Pooling|
copy_orig_well_art2samp.py|CG002 - Reception Control|
copy_UDFs_between_WFs.py|CG002 - Plate Setup MAF|
copyUDFs_from_aggregateQC_or_other.py|CG002 - Aliquot Samples for Library Pooling|
copyUDFs_from_aggregateQC.py|G002 - Aliquot Samples for Library Pooling
|CG002 - Library Normalization (HiSeq X)|
copy_well_art2samp.py||
demultiplexdata2qc.py|CG002 - Bcl Conversion & Demultiplexing (Illumina SBS)|
get_average_size.py|CG002 - Tapestation Microbial QC|
get_EB_vol.py| CG002 - Aliquot Libraries for Hybridization (SS XT)|
get_missing_reads.py|CG002 - Sequence Aggregation|
glsapiutil.py||
help_get_stuff.py||
invoice.py||
LibNorm_calc_vol.py|CG002 - Library Normalization (HiSeq X)|
MAF_calc_vol.py|CG002 - Plate Setup MAF|
make_bravo_csv.py|CG002 - Normalization of microbial samples|
|CG002 - Setup Workset/Plate|
|CG002 - Normalization of microbial samples for sequencing|
make_bravo_csv_test.py||
make_bravo_normalization_file.py||
make_MAF_plate_layout.py||
make_MAF_sample_table.py|CG002 - Plate Setup MAF|
make_placement_map.py|CG002 - Aliquot Samples for Covaris|
|CG002 - Plate Setup MAF|
|CG002 - Library Normalization (HiSeq X)|
microbial_copyUDFs_from_aggregateQC.py||
molar_concentration.py|CG002 - Aggregate QC (Library Validation)|
|CG002 - Qubit QC RML|
move_samples.py|CG002 - Aggregate QC (Library Validation)|
|CG002 - Sort HiSeq Samples|
|CG002 - Sort HiSeq X Samples (HiSeq X)|
qc2udf_art2samp.py| CG002 - Aggregate QC (DNA)|
|CG002 - Sequence Aggregation|
|CG002 - Sequence Aggregation|
|CG002 - Aggregate QC (Library Validation)|
qPCR_dilution_old.py||
qPCR_dilution.py|CG002 - qPCR QC (Library Validation)|
reads_aggregation.py|CG002 - Sequence Aggregation|
reads_aggregation_rml.py|CG002 - Sequence Aggregation|
reagent-label.py||
reception_control.py|CG002 - Reception Control|
rerun.py|CG002 - Sequence Aggregation|
set_qc.py|CG002 - Qubit QC (DNA)|
|CG002 - Qubit QC (Library Validation)|

