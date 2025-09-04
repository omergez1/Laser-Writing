# Laser-Writing

Femtosecond laser writing toolkit for building optical waveguides using Thorlabs components and a Coherent femtosecond laser.

---

## 🚀 Quick Start

### 1. Install Python dependencies
We recommend Python 3.9+ (Windows recommended for Thorlabs Kinesis).

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
(alternatively you can install the libraries in requirements.txt manually)

### 2. Drivers / DLLs / Programes
Install Thorlabs Kinesis software (download from Thorlabs).
https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=10285

Install Coherent Chameleon GUI, called GUI Software 64 Bit on their website
https://www.coherent.com

importent:

Install the RS232 drivers, here is the link to the current cable's driver in the lab 
https://www.sunrichtech.com.hk/products/U-225.html

Copy the DLLs into the projects folder.



### 3. check that each component works
run Thorlabs Kinesis software and make sure the both the BSC203 and the KCube DC Servo (PRM1Z8 rotation stage) are recognized and operating.
run Chameleon GUI and make sure there is a connection with the laser.

before running the python script exist those programes

### 4. run main.py
for now this simply write a straight waveguide, choose your own parameters.


### 5. 🔧 Hardware Used
Thorlabs BSC203 3-axis benchtop stepper stage controller (X/Y/Z)

Thorlabs KCube DC Servo (PRM1Z8 rotation stage)

Spatial Light Modulator (SLM) for beam shaping

Coherent Chameleon femtosecond laser

### 6. 📚 Documentation
There is also a folder called docs which includes all there relevant information on the components we used 

### ⚠️ Safety
This project involves high-power femtosecond lasers.
Always follow your lab’s official laser safety SOP before running any code.
Never operate the system without proper training, interlocks, and protective eyewear.
