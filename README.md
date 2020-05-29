# clinical_EPPs 
## About

The External Program Plug-in (EPP) is a script that is configuerd to be run from within a lims step.

Clinical Genomics LIMS is using both scripts that are developed and maintained by Genologics, and scripts that are developed by developers at Clinical Genomics. Scripts developed and maintained by Clinical Genomics are collected in this repocitory.


## Branching model

clinical_EPPs is using github flow branching model as described in our development manual.


## Production and Stage

Development of new EPPs is preferably done locally but the final testing is done on the stage server.

The production lims system is set up on hippocampus and the stage lims system is set up on amygdala.

ssh into the servers:

`ssh gls@clinical-lims-stage.scilifelab.se`

`ssh gls@clinical-lims.scilifelab.se`

You will need a password wich is kept in the safety locker at clinical genomics.

## Insalling
The procedure for installing is the same on both servers.

clinical_EPPs is cloned into `/home/glsai/opt/` and installed by the glsai user under the conda environment epp_master.

```
sudo -iu glsai
source activate epp_master

cd /home/glsai/opt/clinical_EPPs
git pull <branch name>
python setup.py install

```
the branch that has been installed is now avalibe from within the [lims web interface](https://clinical-lims-stage.scilifelab.se/clarity/).



## Setting up a new EPP

The branch with the new script has been installed and you want to test the script through the web interface. (Or deploy it to production. The procedure is the same.)

Let us call the new script we want to test: `bcl2fastq.py`. Running it from the command line looks like this:

```
(epp_master)glsai@clinical-lims-stage:~/opt/clinical_EPPs/EPPs$ python bcl2fastq.py --help

usage: bcl2fastq.py [-h] [-p PID] [-l LOG]

optional arguments:
  -h, --help  show this help message and exit
  -p PID      Lims id for current Process
  -l LOG      File name for standard log file, for runtime information and
              problems.
```

When the script is configured in the lims step, arguments bust be replaced by `tokens`. They function as placeholders that are replaced with actual values at runtime. You can read more about tokens [here](https://genologics.zendesk.com/hc/en-us/articles/213988783-Derived-Sample-Naming-Convention-Tokens).

To make the new script avalible in the [web interface](https://clinical-lims-stage.scilifelab.se/clarity), go to the `CONFIGURATON` tab and then select `AUTOMATION`. Klick the `NEW AUTOMATON` button.

- Choose a Automation Name
- Channel Name should always be `limsserver`.
- Enter the command line string. If you need help selecting a token for an argument, klick the `TOKENS` tab wich will show the list of avalible tokens. In this case the string is
`bash -c "/home/glsai/miniconda2/envs/epp_master/bin/bcl2fastq.py -p {processLuid} -l {compoundOutputFileLuid0}"`
- Under `AUTOMATION USE`, select master step(s) in which the new EPP should be available.
- Save


![](img/Automation_details.png)


Once the EPP is in place on the master step you need to configure its usage. This can be done both on master step and on step level. 

Klick the `LAB WORK` tab and select a step in which you have enabeled the EPP. 


![](img/configuration_labwork.png)



Choose `STEP` or `MASTER STEP`, and scroll down to the `AUTOMATION` section. The new EPP should be seen there. 


![](img/step_settings.png)


Select Trigger Location - at what point in the step the script should be run, and Trigger Style - how the script should be triggered.

The script is now avalible from within the step. Queue some samples to the step to try it!

![](img/record_details_view.png)

Read more about EPPs in the [Clarity LIMS API Cookbook](https://genologics.zendesk.com/hc/en-us/restricted?return_to=https%3A%2F%2Fgenologics.zendesk.com%2Fhc%2Fen-us%2Fcategories%2F201688743-Clarity-LIMS-API-Cookbook)


## Config files

**~/.genologicsrc**
   
This config file contains user info to give access to the lims database and is requiered for the SciLifeLab/genologics package. All EPPs depend on this config.

Its content must look like this:

```
[genologics]
BASEURI=
USERNAME=
PASSWORD=
```

**~/.clinical_eppsrc**

This config file contains userinfo to give access to cgstats which contains information about demultiplexing data. The config is used by one of the scripts in the Clinical-Genomics/clinical_EPPs package; bcl2fastq.py

Its content must look like this:

```
[demultiplex data]

SQLALCHEMY_DATABASE_URI=mysql+pymysql://remoteuser:<password>@127.0.0.1:<port>/cgstats
[CgFace]
URL=https://clinical-api.scilifelab.se/api/v1

```
