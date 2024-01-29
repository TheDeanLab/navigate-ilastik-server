# navigate-ilastik-server
Ilastik as a server for communication with the navigate software.

### Installation with Conda
~~~
conda activate your-ilastik-environment
python -m pip install --upgrade pip
mkdir ~/Git/
cd ~/Git/
git clone https://github.com/TheDeanLab/navigate-ilastik-server
cd navigate-ilastik-server
pip install -e .
~~~

To run:
~~~
flask --app navigate_server run
~~~
