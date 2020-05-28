# clinical_EPPs 
## About

The External Program Plug-in (EPP) is a script that is configuerd to be run from within a lims step. To meet the need of cutomization.... bla bla help

In the Clinical Genomics lims we are using both scripts that are developed and maintained by Genologics, and scripts that are developed by developers at Clinical Genomics. Script developed and maintained by Clinical Genomics are collected in the Clinical_EPPs directory on github. There you can also find a table showing witch scripts are in production and on witch LIMS steps each particular script is used.


## Support

Please see IT manual on how to contact Genologics Clarity LIMS support.

## Scripts in production

The production lims system is set up on (thalamus).

To log in, do:
`ssh gls@clinical-lims.scilifelab.se`

Programs written and maintained by genologics are located in

`/opt/gls/clarity/`

Don't touch this directory if you dont know exactly what you are doing.

Programs written and maintained by Clinical Genomics are installed by the glsai user under the conda environment epp_master:    
```
/home/glsai/miniconda2/envs/epp_master.

sudo -iu glsai

source activate epp_master
```

### Dependencies

depending on SciLifeLab/genologics
Cloned into `/home/glsai/opt` and installed under epp_master environment.


### Config files

The following config files are requiered.

#### ~/.genologicsrc
   
This config file contains user info to give access to the lims database and is requiered for the SciLifeLab/genologics package.
Its content must look like this:

```
[genologics]
BASEURI=
USERNAME=
PASSWORD=
```

#### ~/.clinical_eppsrc 

This config file contains userinfo to give access to cgstats which contins information about demultiplexing data. The config is used by one of the scripts in the Clinical-Genomics/clinical_EPPs package; bcl2fastq.py

Its content must look like this:

```
[demultiplex data]

SQLALCHEMY_DATABASE_URI=mysql+pymysql://remoteuser:<password>@127.0.0.1:<port>/cgstats
[CgFace]
URL=https://clinical-api.scilifelab.se/api/v1

```

## Branching model

clinical_EPPs is using github flow branching model as described in our development manual.


## Setting up a new EPP - brief overview


Do the testing of your new EPP on the stage server:



```
ssh gls@clinical-lims-stage.scilifelab.se
sudo -iu glsai
source activate epp_master

```


Its set up in the same way as the production server. 

EPPs can be run from the command as well as from the step itself.
When adding a new EPP to a step, go to the CONFIGURATON tab in the web interface and the select the AUTOMATION tab.

Klick the NEW AUTOMATON button.

- Choose a Automation Name
- Channel Name should always be limsserver.
- Enter the command line string. If you need help selecting a token for an argument, klick the TOKENS tab.
- Under AUTOMATION USE, select master step(s) in which the new EPP should be available.
- Save
![](img/automation_settings.png)

Once the EPP is in place on the paster step you need to configure its usage. This can be done both on master step and on step level. 

Klick the LAB WORK tab and select a step in which you have enabeled the EPP. 
![](img/configuration_labwork.png)

Choose STEP or MASTER STEP, and scroll down to the AUTOMATION section. The new EPP should be seen there. 
![](img/step_setings.png)

Select Trigger Socation - at what point in the step the script should be run, and Trigger Style - how the script should be triggered.

Add the new EPP to the Clinical-Genomics/clinical_EPPs repo first when you are sure it works on the stage server. 
Read more about EPPs in the Clarity LIMS API Cookbook

