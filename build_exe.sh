# only for ubutu
# note 1: this buiild_exe.sh that needs to setup module please as follows
# pip install pyinstaller
# note 2: chmod +x build_exe.sh
# ubuntu
# below command will be created an exe that without consloe while user run it
pyinstaller -F --noconsole --onefile ./main.py
#pyinstaller -F --onefile main.py --windowed
# below command will be created an exe that with consloe while user run it
#pyinstaller -F ./main.py
cp ./dist/main ./
mv main vott_retain_json.exe
rm -rf dist
rm -rf __pycache__
rm -rf build
rm *.spec

