#!/usr/bin/env bash
echo "Installing The Oslo Bergen Tagger into ./obt. You might be asked for your password to install cg3"

# Clone obt repo
if [ ! -d obt ]; then
    git clone https://github.com/noklesta/The-Oslo-Bergen-Tagger obt
fi

# Download multitagger
if [ ! -f obt/bin/mtag ]; then
    BASE_URL='http://www.tekstlab.uio.no/mtag'
    if [[ "$OSTYPE" == "darwin"* ]]; then
        wget "${BASE_URL}/osx64/mtag-osx64" -O obt/bin/mtag
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        wget "${BASE_URL}/linux64/mtag-linux-1-11" -O obt/bin/mtag
    else
        echo "You need to install manually cg3. See http://beta.visl.sdu.dk/cg3/chunked/installation.html for instructions"
    fi
fi

# Make it executable
chmod +x obt/bin/mtag

# Install VISL CG-3 (Constraint Grammar tagger)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew ls --versions homebrew/science/vislcg3 > /dev/null; then
        brew install homebrew/science/vislcg3
    fi
elif [[ "$OSTYPE" == "linux-gnu" ]]; then
    if ! dpkg -s cg3 > /dev/null 2>&1; then
        sudo apt install cg3
    fi
else
    echo "You need to install manually cg3. See http://beta.visl.sdu.dk/cg3/chunked/installation.html for instructions"
fi

# Clone obt-stat repo
if [ ! -d obt/OBT-Stat ]; then
    git clone git://github.com/andrely/OBT-Stat.git obt/OBT-Stat
fi

echo "OK"