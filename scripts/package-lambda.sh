
# Assert that ls includes qa_engine, otherwise terminate
if [ ! -d "qa_engine" ]; then
    echo "Build Lambda :: qa_engine directory not found. Please run this script from the root of the repository."
    exit 1
fi

# Check that python command exists
if ! command -v python &> /dev/null
then
    echo "Build Lambda :: python command not found. Please install python 3.9."
    exit 1
fi

echo "Build Lambda :: Initializing virtual environment..."
if [ -d "env" ]; then
    rm -r env
fi
python -m venv env
source env/bin/activate

echo "Build Lambda :: Initialising build folder..."
if [ -d ".lambda" ]; then
    rm -r .lambda
fi
mkdir .lambda

echo "Build Lambda :: Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install --no-cache-dir --upgrade -r requirements.txt

echo "Build Lambda :: Building lambda package..."
# Move all site-packages to .lambda
# get python directory name
pythondirname=$(ls env/lib)
echo "Build Lambda :: using python directory name: $pythondirname"
cp -r env/lib/$pythondirname/site-packages/* .lambda
# Move all modules to .lambda
cp -r qa_engine .lambda/qa_engine

echo "Build Lambda :: Zipping lambda package..."
cd .lambda
zip -r9 ../function.zip .
cd ../

echo "Build Lambda :: Cleaning up..."
rm -r .lambda
rm -r env


echo "Build Lambda :: Done."