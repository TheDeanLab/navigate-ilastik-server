# aslm-ilastik-plugin
Ilastik as a server for communication with the ASLM software.

### Installation with Conda
~~~
conda activate your-ilastik-environment
python -m pip install --upgrade pip
mkdir ~/Git/
cd ~/Git/
git clone https://github.com/TheDeanLab/aslm-ilastik-plugin
cd aslm-ilastik-plugin
pip install -e .
~~~

To run:
~~~
flask --app aslm_server run
~~~
