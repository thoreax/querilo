echo "Build Lambda :: Initializing virtual environment..."
rm -r env
python3.9 -m venv env
source env/bin/activate

echo "Build Lambda :: Installing dependencies..."
python3.9 -m pip install --upgrade pip
python3.9 -m pip install --no-cache-dir --upgrade -r requirements.txt

echo "Build Lambda :: Building lambda package..."
cd env/lib/python3.9/site-packages
zip -r9 ../../../../function.zip .
cd ../../../../
zip -g ./function.zip -r api
zip -g ./function.zip -r core
zip -g ./function.zip -r tests
zip -g ./function.zip -r utils
zip -g ./function.zip .env

echo "Build Lambda :: Done."